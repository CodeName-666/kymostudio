from PySide6.QtCore import QObject, QThread, Signal, Slot
from typing import Optional


class ReceiverThread(QThread):

    new_data = Signal(bytes)
    stop_event = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super(ReceiverThread, self).__init__(parent)
        self.__stop: bool = False
        self.stop_event.connect(self.on_stop)

    def stop(self) -> None:
        """Request interruption for workers that also inspect Qt's flag."""
        self.requestInterruption()
    
    def stopped(self) -> bool:
        return self.__stop or self.isInterruptionRequested()

    @Slot()
    def on_stop(self) -> None:
        self.__stop = True
        self.stop()
