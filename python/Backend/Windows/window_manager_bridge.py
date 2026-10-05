"""QML Bridge for FloatingWindowManager.

Provides QObject interface between QML and Python window management.
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from typing import Optional
from .window_manager import FloatingWindowManager
from .window_state import WindowState


class WindowManagerBridge(QObject):
    """Qt/QML bridge for the floating window manager.

    Exposes window management functionality to QML via signals and slots.
    """

    # Signals
    windowCreated = Signal(str, arguments=['chartId'])
    windowRemoved = Signal(str, arguments=['chartId'])
    windowStateChanged = Signal(str, arguments=['chartId'])
    layoutSaved = Signal(str, arguments=['filename'])
    layoutLoaded = Signal(str, arguments=['filename'])

    def __init__(self, parent=None):
        """Initialize the bridge.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._manager = FloatingWindowManager()

    @Slot(str, result=bool)
    def createWindow(self, chart_id: str) -> bool:
        """Create a new floating window.

        Args:
            chart_id: Unique identifier for the chart

        Returns:
            True if created successfully
        """
        try:
            self._manager.create_window(chart_id)
            self.windowCreated.emit(chart_id)
            return True
        except ValueError as e:
            print(f"WindowManagerBridge: Failed to create window {chart_id}: {e}")
            return False

    @Slot(str, result=bool)
    def removeWindow(self, chart_id: str) -> bool:
        """Remove a floating window.

        Args:
            chart_id: Identifier of chart to remove

        Returns:
            True if removed successfully
        """
        result = self._manager.remove_window(chart_id)
        if result:
            self.windowRemoved.emit(chart_id)
        return result

    @Slot(str, int, int, int, int)
    def updateWindowPosition(self, chart_id: str, x: int, y: int, width: int, height: int):
        """Update window position and size.

        Args:
            chart_id: Identifier of chart
            x: X coordinate
            y: Y coordinate
            width: Window width
            height: Window height
        """
        state = self._manager.get_window_state(chart_id)
        if state:
            state.x = x
            state.y = y
            state.width = width
            state.height = height
            self._manager.update_window_state(chart_id, state)
            self.windowStateChanged.emit(chart_id)

    @Slot(str)
    def bringToFront(self, chart_id: str):
        """Bring window to front.

        Args:
            chart_id: Identifier of chart
        """
        self._manager.bring_to_front(chart_id)
        self.windowStateChanged.emit(chart_id)

    @Slot(str)
    def sendToBack(self, chart_id: str):
        """Send window to back.

        Args:
            chart_id: Identifier of chart
        """
        self._manager.send_to_back(chart_id)
        self.windowStateChanged.emit(chart_id)

    @Slot(str, str, int, int, result=bool)
    def dockWindow(self, chart_id: str, edge: str, screen_width: int, screen_height: int) -> bool:
        """Dock window to edge.

        Args:
            chart_id: Identifier of chart
            edge: Edge to dock to ("left", "right", "top", "bottom")
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels

        Returns:
            True if docked successfully
        """
        result = self._manager.dock_window(chart_id, edge, screen_width, screen_height)
        if result:
            self.windowStateChanged.emit(chart_id)
        return result

    @Slot(str, result=bool)
    def undockWindow(self, chart_id: str) -> bool:
        """Undock window from edge.

        Args:
            chart_id: Identifier of chart

        Returns:
            True if undocked successfully
        """
        result = self._manager.undock_window(chart_id)
        if result:
            self.windowStateChanged.emit(chart_id)
        return result

    @Slot(str)
    def saveLayout(self, filename: str):
        """Save window layout to file.

        Args:
            filename: Path to save layout file
        """
        self._manager.save_layout(filename)
        self.layoutSaved.emit(filename)

    @Slot(str, result=bool)
    def loadLayout(self, filename: str) -> bool:
        """Load window layout from file.

        Args:
            filename: Path to layout file

        Returns:
            True if loaded successfully
        """
        result = self._manager.load_layout(filename)
        if result:
            self.layoutLoaded.emit(filename)
        return result

    @Slot(str, result=int)
    def getWindowZIndex(self, chart_id: str) -> int:
        """Get window z-index.

        Args:
            chart_id: Identifier of chart

        Returns:
            Z-index value, or -1 if not found
        """
        state = self._manager.get_window_state(chart_id)
        return state.z_index if state else -1

    @Slot(result=int)
    def getWindowCount(self) -> int:
        """Get number of managed windows.

        Returns:
            Number of windows
        """
        return self._manager.get_window_count()

    @Slot(str, result=bool)
    def hasWindow(self, chart_id: str) -> bool:
        """Check if window exists.

        Args:
            chart_id: Chart identifier

        Returns:
            True if window exists
        """
        return self._manager.has_window(chart_id)

    @Slot()
    def clearAll(self):
        """Remove all windows."""
        self._manager.clear()

    @Property(FloatingWindowManager, constant=True)
    def manager(self) -> FloatingWindowManager:
        """Get the underlying window manager.

        Returns:
            FloatingWindowManager instance
        """
        return self._manager
