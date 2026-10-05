"""Transport lifecycle orchestration with no QML or configuration-file access.

Callbacks are injected by the QObject facade. All service methods and receiver
status callbacks run on the owning GUI thread; workers only enqueue payloads.
"""
from __future__ import annotations

import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Protocol


class ReceiverProtocol(Protocol):
    """Minimal lifecycle used here; concrete transports provide Qt signals."""
    def config(self, config: dict) -> None: ...
    def settings_valid(self) -> bool: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_connected(self) -> bool: ...


@dataclass
class ConnectionInfo:
    connection_id: str
    interface_type: str
    display_name: str
    status: str = 'disconnected'
    settings: dict[str, Any] = field(default_factory=dict)
    receiver: ReceiverProtocol | None = None
    created_at: float = field(default_factory=time.time)


class ConnectionService:
    """Own connection instances and preserve them on timeout/failure."""

    def __init__(self, registry: Any, on_data: Callable, on_change: Callable,
                 on_status: Callable, notify: Callable, on_samples: Callable | None = None) -> None:
        self.registry = registry
        self.on_data, self.on_change = on_data, on_change
        self.on_samples = on_samples
        self.on_status, self.notify = on_status, notify
        self.connections: dict[str, ConnectionInfo] = {}
        self._requested: set[str] = set()

    def _wire(self, info: ConnectionInfo) -> None:
        receiver = info.receiver
        receiver.new_data.connect(partial(self._data, info.connection_id, receiver))
        if hasattr(receiver, 'samples_ready'):
            receiver.samples_ready.connect(partial(self._samples, info.connection_id, receiver))
        if hasattr(receiver, 'connection_changed'):
            receiver.connection_changed.connect(partial(self._receiver_state, info.connection_id, receiver))
        if hasattr(receiver, 'connection_failed'):
            receiver.connection_failed.connect(partial(self._receiver_failed, info.connection_id, receiver))

    def _data(self, key: str, receiver: ReceiverProtocol, payload: bytes) -> None:
        if key in self.connections and self.connections[key].receiver is receiver:
            self.on_data(key, payload)

    def _samples(self, key: str, receiver: ReceiverProtocol, items: list) -> None:
        if self.on_samples and key in self.connections and self.connections[key].receiver is receiver:
            self.on_samples(key, items)

    def _status(self, key: str, status: str, error: str = '') -> None:
        info = self.connections.get(key)
        if info is None:
            return
        info.status = status
        self.on_status(key, status, {'error': error} if error else {})
        self.on_change()

    def _receiver_state(self, key: str, receiver: ReceiverProtocol, connected: bool) -> None:
        if key not in self.connections or self.connections[key].receiver is not receiver:
            return
        self._status(key, 'connected' if connected else
                     ('connecting' if key in self._requested else 'disconnected'))

    def _receiver_failed(self, key: str, receiver: ReceiverProtocol, message: str) -> None:
        if key in self.connections and self.connections[key].receiver is receiver:
            self._requested.discard(key)
            self._status(key, 'error', message)
            self.notify('error', message)

    def _make_receiver(self, interface_type: str, settings: dict) -> ReceiverProtocol:
        receiver = self.registry.create_receiver({'type': interface_type, 'default': deepcopy(settings)})
        if receiver is None:
            raise ValueError(f'No receiver is available for {interface_type}')
        if not receiver.settings_valid():
            if hasattr(receiver, 'deleteLater'):
                receiver.deleteLater()
            raise ValueError('The connection settings are invalid')
        return receiver

    def create(self, interface_type: str, name: str, settings: dict) -> str:
        if len(self.connections) >= 128:
            self.notify('error', 'The 128-connection limit has been reached')
            return ''
        try:
            receiver = self._make_receiver(interface_type, settings)
        except Exception as exc:
            self.notify('error', str(exc))
            return ''
        key = f'{interface_type}_{uuid.uuid4().hex}'
        info = ConnectionInfo(key, interface_type, name.strip() or interface_type,
                              settings=deepcopy(settings), receiver=receiver)
        self.connections[key] = info
        self._wire(info)
        self.on_change()
        return key

    def restore(self, entry: dict) -> bool:
        key = entry['id']
        if key in self.connections:
            return False
        try:
            # Saved disconnected entries may contain incomplete settings and
            # must remain editable; validation happens when the user starts.
            settings = deepcopy(entry.get('settings', {}))
            receiver = self.registry.create_receiver({'type': entry['type'], 'default': settings})
            if receiver is None:
                raise ValueError('Receiver unavailable')
            info = ConnectionInfo(key, entry['type'], entry['name'], settings=settings,
                                  receiver=receiver, created_at=float(entry.get('created_at', time.time())))
            self.connections[key] = info
            self._wire(info)
            return True
        except Exception as exc:
            self.notify('warning', f'Could not restore {key}: {exc}')
            return False

    def start(self, key: str) -> bool:
        info = self.connections.get(key)
        if info is None or info.receiver is None:
            self.notify('error', 'Connection not found')
            return False
        if key in self._requested and info.status in ('connected', 'connecting'):
            return True
        self._requested.add(key)
        self._status(key, 'connecting')
        try:
            info.receiver.start()
            self._status(key, 'connected' if info.receiver.is_connected() else 'connecting')
            return True
        except Exception as exc:
            self._requested.discard(key)
            self._status(key, 'error', str(exc))
            self.notify('error', f'{info.display_name}: {exc}')
            return False

    def stop(self, key: str) -> bool:
        info = self.connections.get(key)
        if info is None:
            return False
        self._requested.discard(key)
        try:
            if info.receiver is not None:
                info.receiver.stop()
            self._status(key, 'disconnected')
            return True
        except Exception as exc:
            self._status(key, 'error', str(exc))
            self.notify('error', f'Could not stop {info.display_name}: {exc}')
            return False

    def update_settings(self, key: str, settings: dict) -> bool:
        info = self.connections.get(key)
        if info is None:
            return False
        try:
            candidate = self._make_receiver(info.interface_type, settings)
        except Exception as exc:
            self.notify('warning', f'Invalid connection settings: {exc}')
            return False
        restart = key in self._requested or info.status in ('connected', 'connecting')
        if not self.stop(key):
            if hasattr(candidate, 'deleteLater'):
                candidate.deleteLater()
            return False
        old = info.receiver
        info.receiver = candidate
        info.settings = deepcopy(settings)
        self._wire(info)
        if old is not None and hasattr(old, 'deleteLater'):
            old.deleteLater()
        if restart:
            self.start(key)  # A failed reconnect is visible; settings remain saved.
        self.on_change()
        return True

    def rename(self, key: str, name: str) -> bool:
        if key not in self.connections or not name.strip():
            return False
        self.connections[key].display_name = name.strip()[:200]
        self.on_change()
        return True

    def shutdown(self) -> bool:
        # Do not short-circuit: every source receives its stop request.
        return all([self.stop(key) for key in list(self.connections)])
