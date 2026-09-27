"""Common receiver base class used by backend connection implementations."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal, Slot

from .receiver_thread import ReceiverThread


class MetaQObjectABC(type(QObject), ABCMeta):
    """Metaclass combining PySide's QObject meta type with ABCMeta."""

    pass

class Receiver(QObject, metaclass=MetaQObjectABC):
    """Defines the lifecycle contract that every backend receiver must follow.

    A receiver encapsulates the transport specific logic that connects to an
    external data source (serial, telnet, mqtt, ...). Each receiver exposes a
    uniform API so the backend can manage instances without caring about the
    underlying protocol.
    """

    # Bytes emitted from the underlying worker thread. Consumers connect to
    # this signal to receive decoded payload from any receiver implementation.
    new_data = Signal(bytes)

    def __init__(
        self,
        receiver_thread: Optional[ReceiverThread] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._receiver_thread: Optional[ReceiverThread] = None
        self._connected: bool = False
        self._config: Dict[str, Any] = {}
        if receiver_thread is not None:
            self.attach_thread(receiver_thread)

    # ------------------------------------------------------------------
    # Thread handling / signal plumbing
    # ------------------------------------------------------------------
    def attach_thread(self, receiver_thread: ReceiverThread) -> None:
        """Attach a worker thread and forward its data to ``new_data``.

        A receiver implementation can either supply an already configured
        thread instance on construction or attach a thread later on. The base
        class ensures that the ``new_data`` signal is relayed to listeners.
        """

        if receiver_thread is None:
            raise ValueError("receiver_thread must not be None")

        if self._receiver_thread is not None:
            try:
                self._receiver_thread.new_data.disconnect(self._on_thread_data)
            except (TypeError, RuntimeError):
                # When disconnecting during teardown the signal might already
                # be disconnected or thread deleted. Silently ignore those.
                pass

        self._receiver_thread = receiver_thread
        self._receiver_thread.new_data.connect(self._on_thread_data)

    @property
    def receiver_thread(self) -> Optional[ReceiverThread]:
        return self._receiver_thread

    def detach_thread(self) -> None:
        """Detach the currently assigned worker thread, if any."""

        if self._receiver_thread is None:
            return

        try:
            self._receiver_thread.new_data.disconnect(self._on_thread_data)
        except (TypeError, RuntimeError):
            pass

        self._receiver_thread = None

    @Slot(bytes)
    def _on_thread_data(self, payload: bytes) -> None:
        """Default slot that forwards worker data to backend consumers."""

        self.new_data.emit(payload)

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start data acquisition.

        The base implementation validates settings, opens the connection if
        needed and finally starts the worker thread.
        """

        if not self.settings_valid():
            raise ValueError("Cannot start receiver with invalid settings")

        if not self.is_connected() and not self.open_connection():
            raise ConnectionError("Receiver failed to open the connection")

        if self._receiver_thread and not self._receiver_thread.isRunning():
            self._receiver_thread.start()

    def stop(self) -> None:
        """Stop the worker thread and close the connection."""

        if self._receiver_thread and self._receiver_thread.isRunning():
            # Ask the thread to finish its loop, then wait for it to end.
            self._receiver_thread.stop_event.emit()
            self._receiver_thread.wait()

        if self.is_connected():
            self.close_connection()

    def send_response(self, response: bytes) -> None:
        """Forward a response payload to the worker thread if available."""

        if self._receiver_thread is None:
            raise RuntimeError("Receiver thread not attached")

        if hasattr(self._receiver_thread, "send_response"):
            self._receiver_thread.send_response(response)
        else:
            raise NotImplementedError("Receiver thread cannot send responses")

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def config(self, config: Dict[str, Any]) -> None:
        """Store backend supplied configuration and notify subclasses."""

        self._config = config or {}
        self._on_config_updated()

    @property
    def config_data(self) -> Dict[str, Any]:
        return self._config

    def _on_config_updated(self) -> None:
        """Optional hook for subclasses when configuration changes."""

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def is_connected(self) -> bool:
        return self._connected

    def _set_connected(self, status: bool) -> None:
        self._connected = status

    # ------------------------------------------------------------------
    # Interface contracts
    # ------------------------------------------------------------------
    @abstractmethod
    def open_connection(self) -> bool:
        """Establish the transport specific connection."""

    @abstractmethod
    def close_connection(self) -> None:
        """Tear down the connection and release resources."""

    @abstractmethod
    def settings_valid(self) -> bool:
        """Validate the settings gathered from the UI/backend."""


__all__ = ["Receiver"]
