"""Common receiver base class used by backend connection implementations."""

from __future__ import annotations

import time
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, QTimer, Qt, Signal, Slot

from Core.ingress import IngressQueue
from Core.parsing import parse_payload

from .binary_protocol import ProtocolError
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

    # Raw payloads produced on the GUI thread (receivers without a worker).
    new_data = Signal(bytes)
    # Worker output, once per drain tick: a list of (PlotDataPoint, rx_wall,
    # rx_monotonic) tuples or ProtocolError instances, parsed in the worker.
    samples_ready = Signal(object)
    connection_changed = Signal(bool)
    connection_failed = Signal(str)

    def __init__(
        self,
        receiver_thread: Optional[ReceiverThread] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._receiver_thread: Optional[ReceiverThread] = None
        self._connected: bool = False
        self._config: Dict[str, Any] = {}
        # ~0.6 s of headroom at 50 000 samples/s if the GUI thread stalls.
        self._ingress = IngressQueue(capacity=32768, max_bytes=16 * 1024 * 1024)
        self._drain_timer = QTimer(self)
        self._drain_timer.setInterval(16)
        self._drain_timer.timeout.connect(self._drain_ingress)
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
            if self._receiver_thread.isRunning():
                raise RuntimeError("Cannot replace a running acquisition worker")
            self.detach_thread()

        self._receiver_thread = receiver_thread
        receiver_thread._sink = self._enqueue_payloads
        # Parsing and the locked enqueue execute in the producing thread;
        # model changes and status signals stay on the GUI thread.
        self._receiver_thread.new_data.connect(self._enqueue_payload, Qt.DirectConnection)
        self._receiver_thread.connection_state.connect(self._set_connected, Qt.QueuedConnection)
        self._receiver_thread.finished.connect(self._worker_finished, Qt.QueuedConnection)

    @property
    def receiver_thread(self) -> Optional[ReceiverThread]:
        return self._receiver_thread

    def detach_thread(self) -> None:
        """Detach the currently assigned worker thread, if any."""

        if self._receiver_thread is None:
            return

        if self._receiver_thread.isRunning():
            raise RuntimeError("Cannot detach a running acquisition worker")
        self._receiver_thread._sink = None
        try:
            self._receiver_thread.connection_state.disconnect(self._set_connected)
            self._receiver_thread.finished.disconnect(self._worker_finished)
            self._receiver_thread.new_data.disconnect(self._enqueue_payload)
        except (TypeError, RuntimeError):
            pass

        self._receiver_thread.deleteLater()
        self._receiver_thread = None

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

        self._drain_timer.start()
        if self._receiver_thread and not self._receiver_thread.isRunning():
            self._receiver_thread.start()

    def stop(self) -> None:
        """Cooperatively stop; never destroy a still-running QThread.

        A stubborn driver produces a visible error instead of an unlimited
        wait. The backend retains the receiver so a later stop can retry.
        """
        self._stop_worker()
        self._drain_timer.stop()
        while len(self._ingress):
            self._drain_ingress()
        self.close_connection()
        self._ingress.clear()
        self._set_connected(False)

    def _stop_worker(self) -> None:
        worker = self._receiver_thread
        if worker and worker.isRunning():
            worker.on_stop()
            if not worker.wait(1500):
                raise TimeoutError("Acquisition worker did not stop within 1.5 s; connection retained")

    @property
    def dropped_payloads(self) -> int:
        return self._ingress.dropped

    @Slot(bytes)
    def _enqueue_payload(self, payload: bytes) -> None:
        self._enqueue_payloads((payload,))

    def _enqueue_payloads(self, payloads) -> None:
        """Runs in the producing thread: parse each message and stamp the receive time.

        Messages handed over together arrived in the same read, so they share it.
        """
        rx_wall, rx_monotonic = time.time(), time.monotonic()
        entries = []
        for payload in payloads:
            try:
                point = parse_payload(payload)
            except ProtocolError as exc:
                entries.append((exc, len(payload)))
                continue
            if point is not None:
                entries.append(((point, rx_wall, rx_monotonic), len(payload)))
        self._ingress.put_many(entries)

    @Slot()
    def _drain_ingress(self) -> None:
        items = self._ingress.drain(self._ingress.capacity)
        if items:
            self.samples_ready.emit(items)

    @Slot()
    def _worker_finished(self) -> None:
        if self.sender() is self._receiver_thread:
            self._set_connected(False)
            if not self._receiver_thread.stopped():
                self.connection_failed.emit("Acquisition worker stopped unexpectedly; restart the connection")

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

    @Slot(bool)
    def _set_connected(self, status: bool) -> None:
        sender = self.sender()
        if isinstance(sender, ReceiverThread) and sender is not self._receiver_thread:
            return
        if self._connected != status:
            self._connected = status
            self.connection_changed.emit(status)

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
