"""XY Chart - 2D Line and Scatter chart implementations."""

from typing import Dict, Any
from .base_chart import BaseChart, ChartType, DataLine


class XYLineChart(BaseChart):
    """Cartesian 2D line chart using transmitted X and Y coordinates.

    Time-series charts are handled separately by ``TimeSeriesChart``. An XY
    chart must never substitute elapsed time for an explicitly transmitted X.

    Attributes:
        axis_x_min: Minimum X-axis value
        axis_x_max: Maximum X-axis value
        axis_y_min: Minimum Y-axis value
        axis_y_max: Maximum Y-axis value
    """

    def __init__(self, chart_id: str, name: str):
        """Initialize XY Line Chart.

        Args:
            chart_id: Unique identifier for this chart
            name: Display name
        """
        super().__init__(chart_id, name, ChartType.XY_LINE)

        # Axis ranges
        self.axis_x_min = 0.0
        self.axis_x_max = 10.0
        self.axis_y_min = 0.0
        self.axis_y_max = 10.0

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
            display_name=config.get("display_name", f"Line {len(self.data_lines)}"),
            color=config.get("color", "#0066cc"),
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
        """XY charts require 2 dimensions (X, Y).

        Returns:
            2
        """
        return 2

    def validate_data_point(self, point: Any) -> bool:
        """Validate that a data point contains explicit X and Y coordinates.

        Args:
            point: PlotDataPoint to validate

        Returns:
            True only when the protocol supplied X and the point has Y/value
        """
        return getattr(point, "x", None) is not None and hasattr(point, "value")

    def get_qml_component(self) -> str:
        """Return QML component path for XY Line Chart.

        Returns:
            QML component path
        """
        return "qrc:/qt/qml/content/ChartTypes/XYChartRenderer.qml"

    def set_axis_range(self, x_min: float, x_max: float, y_min: float, y_max: float) -> None:
        """Set axis ranges for this chart.

        Args:
            x_min: Minimum X value
            x_max: Maximum X value
            y_min: Minimum Y value
            y_max: Maximum Y value
        """
        self.axis_x_min = x_min
        self.axis_x_max = x_max
        self.axis_y_min = y_min
        self.axis_y_max = y_max

    def get_axis_range(self) -> Dict[str, float]:
        """Get current axis ranges.

        Returns:
            Dictionary with x_min, x_max, y_min, y_max
        """
        return {
            "x_min": self.axis_x_min,
            "x_max": self.axis_x_max,
            "y_min": self.axis_y_min,
            "y_max": self.axis_y_max
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, including axis ranges.

        Returns:
            Dictionary representation
        """
        data = super().to_dict()
        data["axis_ranges"] = self.get_axis_range()
        return data


class XYScatterChart(XYLineChart):
    """2D Scatter Chart (points without connecting lines).

    Inherits from XYLineChart as they share the same data structure,
    only the visual representation differs (points vs lines).
    """

    def __init__(self, chart_id: str, name: str):
        """Initialize XY Scatter Chart.

        Args:
            chart_id: Unique identifier
            name: Display name
        """
        super().__init__(chart_id, name)
        self.chart_type = ChartType.XY_SCATTER

    def get_qml_component(self) -> str:
        """Return QML component path for XY Scatter Chart.

        Returns:
            QML component path
        """
        return "qrc:/qt/qml/content/ChartTypes/XYChartRenderer.qml"
