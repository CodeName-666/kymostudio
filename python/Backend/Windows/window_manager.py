"""Floating Window Manager - Manages all floating chart windows."""

from typing import Dict, List, Optional
import json
from pathlib import Path
from .window_state import WindowState


class FloatingWindowManager:
    """Manages state and layout of all floating chart windows.

    This class handles window positioning, z-ordering, docking,
    and persistence of window layouts.

    Attributes:
        _windows: Dictionary mapping chart_id to WindowState
        _focus_stack: List of chart_ids in z-order (bottom to top)
    """

    def __init__(self):
        """Initialize the window manager."""
        self._windows: Dict[str, WindowState] = {}
        self._focus_stack: List[str] = []

    def create_window(
        self,
        chart_id: str,
        initial_state: Optional[WindowState] = None
    ) -> WindowState:
        """Create a new floating window.

        Args:
            chart_id: Unique identifier for the chart
            initial_state: Optional initial window state (auto-generated if None)

        Returns:
            WindowState for the new window

        Raises:
            ValueError: If chart_id already exists
        """
        if chart_id in self._windows:
            raise ValueError(f"Window already exists for chart: {chart_id}")

        # Create default state if not provided
        state = initial_state or WindowState()

        # Set z-index to be on top
        state.z_index = len(self._windows)

        # Store state
        self._windows[chart_id] = state
        self._focus_stack.append(chart_id)

        return state

    def remove_window(self, chart_id: str) -> bool:
        """Remove a floating window.

        Args:
            chart_id: Identifier of chart to remove

        Returns:
            True if removed, False if not found
        """
        if chart_id not in self._windows:
            return False

        # Remove from storage
        del self._windows[chart_id]

        # Remove from focus stack
        if chart_id in self._focus_stack:
            self._focus_stack.remove(chart_id)

        # Reindex z-order
        self._reindex_z_order()

        return True

    def update_window_state(self, chart_id: str, state: WindowState) -> bool:
        """Update window state.

        Args:
            chart_id: Identifier of chart to update
            state: New window state

        Returns:
            True if updated, False if chart not found
        """
        if chart_id not in self._windows:
            return False

        self._windows[chart_id] = state
        return True

    def get_window_state(self, chart_id: str) -> Optional[WindowState]:
        """Get current window state.

        Args:
            chart_id: Identifier of chart

        Returns:
            WindowState if found, None otherwise
        """
        return self._windows.get(chart_id)

    def get_all_windows(self) -> Dict[str, WindowState]:
        """Get all window states.

        Returns:
            Dictionary of chart_id to WindowState
        """
        return self._windows.copy()

    def bring_to_front(self, chart_id: str) -> None:
        """Bring window to front (top of z-order).

        Args:
            chart_id: Identifier of chart to bring to front
        """
        if chart_id not in self._windows:
            return

        # Move to end of focus stack (= on top)
        if chart_id in self._focus_stack:
            self._focus_stack.remove(chart_id)
        self._focus_stack.append(chart_id)

        # Update z-indices
        self._reindex_z_order()

    def send_to_back(self, chart_id: str) -> None:
        """Send window to back (bottom of z-order).

        Args:
            chart_id: Identifier of chart to send to back
        """
        if chart_id not in self._windows:
            return

        # Move to start of focus stack (= at bottom)
        if chart_id in self._focus_stack:
            self._focus_stack.remove(chart_id)
        self._focus_stack.insert(0, chart_id)

        # Update z-indices
        self._reindex_z_order()

    def dock_window(self, chart_id: str, edge: str, screen_width: int = 1920, screen_height: int = 1080) -> bool:
        """Dock window to screen edge.

        Args:
            chart_id: Identifier of chart to dock
            edge: Edge to dock to ("left", "right", "top", "bottom")
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels

        Returns:
            True if docked, False if chart not found or invalid edge
        """
        if chart_id not in self._windows:
            return False

        valid_edges = ["left", "right", "top", "bottom"]
        if edge not in valid_edges:
            return False

        state = self._windows[chart_id]
        state.docked = edge

        # Calculate docked position and size
        if edge == "left":
            state.x = 0
            state.y = 0
            state.width = screen_width // 2
            state.height = screen_height
        elif edge == "right":
            state.x = screen_width // 2
            state.y = 0
            state.width = screen_width // 2
            state.height = screen_height
        elif edge == "top":
            state.x = 0
            state.y = 0
            state.width = screen_width
            state.height = screen_height // 2
        elif edge == "bottom":
            state.x = 0
            state.y = screen_height // 2
            state.width = screen_width
            state.height = screen_height // 2

        return True

    def undock_window(self, chart_id: str) -> bool:
        """Undock window from edge.

        Args:
            chart_id: Identifier of chart to undock

        Returns:
            True if undocked, False if chart not found
        """
        if chart_id not in self._windows:
            return False

        state = self._windows[chart_id]
        state.docked = None

        # Reset to reasonable free-floating size
        state.width = 800
        state.height = 600

        return True

    def save_layout(self, filename: str) -> None:
        """Save window layout to file.

        Args:
            filename: Path to save layout file
        """
        layout = {
            "version": "1.0",
            "windows": {
                chart_id: state.to_dict()
                for chart_id, state in self._windows.items()
            },
            "focus_stack": self._focus_stack.copy()
        }

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(layout, f, indent=2)

    def load_layout(self, filename: str) -> bool:
        """Load window layout from file.

        Args:
            filename: Path to layout file

        Returns:
            True if loaded successfully, False otherwise
        """
        path = Path(filename)
        if not path.exists():
            return False

        try:
            with open(path, 'r') as f:
                layout = json.load(f)

            # Clear current state
            self._windows.clear()
            self._focus_stack.clear()

            # Load windows
            for chart_id, state_dict in layout.get("windows", {}).items():
                self._windows[chart_id] = WindowState.from_dict(state_dict)

            # Load focus stack
            self._focus_stack = layout.get("focus_stack", [])

            return True

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading layout: {e}")
            return False

    def get_next_window_position(self) -> tuple[int, int]:
        """Calculate position for next new window (cascade layout).

        Returns:
            Tuple of (x, y) coordinates
        """
        # Cascade windows diagonally
        offset = len(self._windows) * 30
        return (100 + offset, 100 + offset)

    def _reindex_z_order(self) -> None:
        """Reindex z-order of all windows based on focus stack."""
        for i, chart_id in enumerate(self._focus_stack):
            if chart_id in self._windows:
                self._windows[chart_id].z_index = i

    def get_window_count(self) -> int:
        """Get number of windows.

        Returns:
            Number of managed windows
        """
        return len(self._windows)

    def has_window(self, chart_id: str) -> bool:
        """Check if window exists.

        Args:
            chart_id: Chart identifier

        Returns:
            True if window exists
        """
        return chart_id in self._windows

    def clear(self) -> None:
        """Remove all windows."""
        self._windows.clear()
        self._focus_stack.clear()
