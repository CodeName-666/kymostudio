"""Window State - Data structure for window position and state."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json


@dataclass
class WindowState:
    """Represents the state of a floating chart window.

    This class stores all information about a window's position, size,
    and visual state. It can be serialized to/from JSON for persistence.

    Attributes:
        x: X coordinate of window (pixels)
        y: Y coordinate of window (pixels)
        width: Window width (pixels)
        height: Window height (pixels)
        minimized: Whether window is minimized
        maximized: Whether window is maximized
        docked: Docking position ("left", "right", "top", "bottom", or None)
        monitor_id: Which monitor the window is on (0 = primary)
        z_index: Z-order (higher = on top)
        visible: Whether window is currently visible
    """

    x: int = 100
    y: int = 100
    width: int = 800
    height: int = 600
    minimized: bool = False
    maximized: bool = False
    docked: Optional[str] = None
    monitor_id: int = 0
    z_index: int = 0
    visible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of window state
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "minimized": self.minimized,
            "maximized": self.maximized,
            "docked": self.docked,
            "monitor_id": self.monitor_id,
            "z_index": self.z_index,
            "visible": self.visible
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowState':
        """Create WindowState from dictionary.

        Args:
            data: Dictionary with window state data

        Returns:
            WindowState instance
        """
        return cls(
            x=data.get("x", 100),
            y=data.get("y", 100),
            width=data.get("width", 800),
            height=data.get("height", 600),
            minimized=data.get("minimized", False),
            maximized=data.get("maximized", False),
            docked=data.get("docked"),
            monitor_id=data.get("monitor_id", 0),
            z_index=data.get("z_index", 0),
            visible=data.get("visible", True)
        )

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'WindowState':
        """Create WindowState from JSON string.

        Args:
            json_str: JSON string

        Returns:
            WindowState instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def is_docked(self) -> bool:
        """Check if window is docked to an edge.

        Returns:
            True if docked, False otherwise
        """
        return self.docked is not None

    def get_dock_position(self) -> Optional[str]:
        """Get docking position.

        Returns:
            "left", "right", "top", "bottom", or None
        """
        return self.docked

    def set_dock_position(self, position: Optional[str]) -> None:
        """Set docking position.

        Args:
            position: "left", "right", "top", "bottom", or None to undock
        """
        valid_positions = ["left", "right", "top", "bottom", None]
        if position not in valid_positions:
            raise ValueError(f"Invalid dock position: {position}")
        self.docked = position

    def __repr__(self) -> str:
        """String representation."""
        return (f"WindowState(pos=({self.x},{self.y}), "
                f"size=({self.width}x{self.height}), "
                f"z={self.z_index}, "
                f"docked={self.docked})")
