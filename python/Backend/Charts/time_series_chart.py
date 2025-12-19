"""Time Series Chart - Simple chart for displaying Y values over time."""

from typing import Dict, Any
from .base_chart import BaseChart, ChartType, DataLine


class TimeSeriesChart(BaseChart):
    """Time Series Chart implementation.

    This chart type displays single Y-values cyclically over time.
    It automatically manages the time axis (X) and only requires Y values.
    Perfect for monitoring single data streams over time.

    Features:
    - Automatic time axis management
    - Configurable time window (default: last 60 seconds)
    - Auto-scrolling as new data arrives
    - Multiple lines supported

    Attributes:
        time_window: Time window in seconds (default: 60)
        auto_scroll: Whether to auto-scroll as new data arrives (default: True)
        axis_y_min: Minimum Y-axis value (auto-adjusts if auto_scale enabled)
        axis_y_max: Maximum Y-axis value (auto-adjusts if auto_scale enabled)
        auto_scale_y: Whether to auto-scale Y axis (default: True)
    """

    def __init__(self, chart_id: str, name: str):
        """Initialize Time Series Chart.

        Args:
            chart_id: Unique identifier for this chart
            name: Display name
        """
        super().__init__(chart_id, name, ChartType.TIME_SERIES)

        # Time window configuration (in seconds)
        self.time_window = 60.0  # Show last 60 seconds by default
        self.auto_scroll = True

        # Y-axis configuration
        self.axis_y_min = 0.0
        self.axis_y_max = 10.0
        self.auto_scale_y = True

    def add_data_line(self, unique_id: str, config: Dict[str, Any]) -> bool:
        """Add a data line to this chart.

        Args:
            unique_id: Unique identifier for the line
            config: Configuration with display_name, color, interface_type, data_id

        Returns:
            True if added successfully
        """
        if unique_id in self.data_lines:
            return False  # Already exists

        line = DataLine(
            unique_id=unique_id,
            display_name=config.get("display_name", f"Signal {len(self.data_lines)}"),
            color=config.get("color", "#00aaff"),
            visible=config.get("visible", True),
            interface_type=config.get("interface_type", "Unknown"),
            data_id=config.get("data_id", 0)
        )

        self.data_lines[unique_id] = line
        return True

    def remove_data_line(self, unique_id: str) -> bool:
        """Remove a data line from this chart.

        Args:
            unique_id: Unique identifier of the line

        Returns:
            True if removed successfully
        """
        if unique_id in self.data_lines:
            del self.data_lines[unique_id]
            return True
        return False

    def get_required_dimensions(self) -> int:
        """Time series charts require only Y dimension (time is automatic).

        Returns:
            1 (only Y value required, X/time is auto-generated)
        """
        return 1

    def validate_data_point(self, point: Any) -> bool:
        """Validate if data point has at minimum a Y value.

        Args:
            point: PlotDataPoint to validate

        Returns:
            True if point has a 'value' (Y coordinate)
        """
        # Time series only needs Y value (timestamp is auto-generated)
        return hasattr(point, 'value')

    def get_qml_component(self) -> str:
        """Return QML component path for Time Series Chart.

        Returns:
            QML component path
        """
        return "qrc:/qt/qml/content/ChartTypes/TimeSeriesChart.qml"

    def set_time_window(self, window_seconds: float) -> None:
        """Set the time window to display.

        Args:
            window_seconds: Time window in seconds (e.g., 60 for last minute)
        """
        if window_seconds > 0:
            self.time_window = window_seconds

    def get_time_window(self) -> float:
        """Get current time window setting.

        Returns:
            Time window in seconds
        """
        return self.time_window

    def set_y_range(self, y_min: float, y_max: float, auto_scale: bool = False) -> None:
        """Set Y-axis range.

        Args:
            y_min: Minimum Y value
            y_max: Maximum Y value
            auto_scale: Enable auto-scaling
        """
        self.axis_y_min = y_min
        self.axis_y_max = y_max
        self.auto_scale_y = auto_scale

    def get_y_range(self) -> Dict[str, Any]:
        """Get current Y-axis range configuration.

        Returns:
            Dictionary with y_min, y_max, auto_scale
        """
        return {
            "y_min": self.axis_y_min,
            "y_max": self.axis_y_max,
            "auto_scale": self.auto_scale_y
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, including time series specific settings.

        Returns:
            Dictionary representation
        """
        data = super().to_dict()
        data["time_window"] = self.time_window
        data["auto_scroll"] = self.auto_scroll
        data["y_range"] = self.get_y_range()
        return data
