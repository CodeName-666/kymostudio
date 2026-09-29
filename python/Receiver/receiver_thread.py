"""Cooperative worker contract with interruptible reconnect backoff."""
from threading import Event
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot


class ReceiverThread(QThread):
    new_data = Signal(bytes)
    stop_event = Signal()
    connection_state = Signal(bool)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._stop_requested = Event()
        self.stop_event.connect(self.on_stop)

    def stop(self) -> None:
        self._stop_requested.set()
        self.requestInterruption()

    def stopped(self) -> bool:
        return self._stop_requested.is_set() or self.isInterruptionRequested()

    def interruptible_wait(self, seconds: float) -> bool:
        """Return True immediately when shutdown interrupts a retry delay."""
        return self._stop_requested.wait(max(0.0, seconds))

    @Slot()
    def on_stop(self) -> None:
        self._stop_requested.set()
        self.requestInterruption()
        self.stop()
