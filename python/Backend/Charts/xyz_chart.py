"""XYZ Chart - 3D Scatter and Surface chart implementations."""

from typing import Dict, Any
from .base_chart import BaseChart, ChartType, DataLine


class XYZScatterChart(BaseChart):
    """3D Scatter Chart implementation.

    This chart type displays 3D data points with X, Y, and Z coordinates.
    Suitable for visualizing spatial data, 3D trajectories, and multi-dimensional
    measurements.

    Attributes:
        axis_x_min: Minimum X-axis value
        axis_x_max: Maximum X-axis value
        axis_y_min: Minimum Y-axis value
        axis_y_max: Maximum Y-axis value
        axis_z_min: Minimum Z-axis value
        axis_z_max: Maximum Z-axis value
    """

    def __init__(self, chart_id: str, name: str):
        """Initialize XYZ Scatter Chart.

        Args:
            chart_id: Unique identifier for this chart
            name: Display name
        """
        super().__init__(chart_id, name, ChartType.XYZ_SCATTER)

        # Axis ranges (default cube from -10 to +10)
        self.axis_x_min = -10.0
        self.axis_x_max = 10.0
        self.axis_y_min = -10.0
        self.axis_y_max = 10.0
        self.axis_z_min = -10.0
        self.axis_z_max = 10.0

    def add_data_line(self, unique_id: str, config: Dict[str, Any]) -> bool:
        """Add a scatter plot to this chart.

        Args:
            unique_id: Unique identifier for the scatter plot
            config: Configuration with display_name, color, interface_type, data_id

        Returns:
            True if added successfully
        """
        if unique_id in self.data_lines:
            return False  # Already exists

        line = DataLine(
            unique_id=unique_id,
            display_name=config.get("display_name", f"Scatter {len(self.data_lines)}"),
            color=config.get("color", "#ffff00"),  # Default: yellow
            visible=config.get("visible", True),
            interface_type=config.get("interface_type", "Unknown"),
            data_id=config.get("data_id", 0)
        )

        self.data_lines[unique_id] = line
        return True

    def remove_data_line(self, unique_id: str) -> bool:
        """Remove a scatter plot from this chart.

        Args:
            unique_id: Unique identifier of the scatter plot

        Returns:
            True if removed successfully
        """
        if unique_id in self.data_lines:
            del self.data_lines[unique_id]
            return True
        return False

    def get_required_dimensions(self) -> int:
        """XYZ charts require 3 dimensions (X, Y, Z).

        Returns:
            3
        """
        return 3

    def validate_data_point(self, point: Any) -> bool:
        """Validate if data point has X, Y, and Z coordinates.

        Args:
            point: PlotDataPoint to validate

        Returns:
            True if point has value (y), timestamp (x), and z_value
        """
        # Point must have value (Y), timestamp (X), and z_value (Z)
        if not hasattr(point, 'value'):
            return False
        if not hasattr(point, 'z_value') or point.z_value is None:
            return False
        # timestamp (X) is optional, will be auto-generated if missing
        return True

    def get_qml_component(self) -> str:
        """Return QML component path for XYZ Scatter Chart.

        Returns:
            QML component path
        """
        return "qrc:/qt/qml/content/ChartTypes/XYZChartRenderer.qml"

    def set_axis_range(self, x_min: float, x_max: float, y_min: float, y_max: float,
                       z_min: float, z_max: float) -> None:
        """Set axis ranges for this 3D chart.

        Args:
            x_min: Minimum X value
            x_max: Maximum X value
            y_min: Minimum Y value
            y_max: Maximum Y value
            z_min: Minimum Z value
            z_max: Maximum Z value
        """
        self.axis_x_min = x_min
        self.axis_x_max = x_max
        self.axis_y_min = y_min
        self.axis_y_max = y_max
        self.axis_z_min = z_min
        self.axis_z_max = z_max

    def get_axis_range(self) -> Dict[str, float]:
        """Get current axis ranges.

        Returns:
            Dictionary with x_min, x_max, y_min, y_max, z_min, z_max
        """
        return {
            "x_min": self.axis_x_min,
            "x_max": self.axis_x_max,
            "y_min": self.axis_y_min,
            "y_max": self.axis_y_max,
            "z_min": self.axis_z_min,
            "z_max": self.axis_z_max
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, including axis ranges.

        Returns:
            Dictionary representation
        """
        data = super().to_dict()
        data["axis_ranges"] = self.get_axis_range()
        return data


class XYZSurfaceChart(XYZScatterChart):
    """3D Surface Chart (mesh connecting points).

    Inherits from XYZScatterChart as they share the same 3D data structure,
    only the visual representation differs (surface mesh vs scatter points).

    Note: Surface rendering requires structured grid data and is not yet
    fully implemented in the frontend.
    """

    def __init__(self, chart_id: str, name: str):
        """Initialize XYZ Surface Chart.

        Args:
            chart_id: Unique identifier
            name: Display name
        """
        super().__init__(chart_id, name)
        self.chart_type = ChartType.XYZ_SURFACE

    def get_qml_component(self) -> str:
        """Return QML component path for XYZ Surface Chart.

        Returns:
            QML component path (currently same as scatter)
        """
        # TODO: Create dedicated XYZSurfaceRenderer.qml for mesh rendering
        return "qrc:/qt/qml/content/ChartTypes/XYZChartRenderer.qml"
