# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Base Chart - Abstract base class for all chart types."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class ChartType(Enum):
    """Enumeration of available chart types."""
    XY_LINE = "xy_line"           # 2D Line Chart (standard)
    XY_SCATTER = "xy_scatter"     # 2D Scatter Plot
    TIME_SERIES = "time_series"   # Time Series Chart (Y values over time)
    XYZ_SURFACE = "xyz_surface"   # 3D Surface Plot
    XYZ_SCATTER = "xyz_scatter"   # 3D Scatter Plot
    BAR = "bar"                   # Bar Chart
    HEATMAP = "heatmap"           # 2D Heatmap
    CUSTOM = "custom"             # Custom Plugin


@dataclass
class DataLine:
    """Represents a single data line within a chart."""
    unique_id: str
    display_name: str
    color: str
    visible: bool = True
    interface_type: str = "Unknown"
    data_id: int = 0


class BaseChart(ABC):
    """Abstract base class for all chart types.

    All concrete chart implementations must inherit from this class
    and implement the abstract methods.

    Attributes:
        chart_id: Unique identifier for this chart instance
        name: Display name of the chart
        chart_type: Type of chart (from ChartType enum)
        data_lines: Dictionary of data lines {unique_id: DataLine}
        visible: Whether the chart window is visible
    """

    def __init__(self, chart_id: str, name: str, chart_type: ChartType):
        """Initialize base chart.

        Args:
            chart_id: Unique identifier for this chart
            name: Display name
            chart_type: Type from ChartType enum
        """
        self.chart_id = chart_id
        self.name = name
        self.chart_type = chart_type
        self.data_lines: Dict[str, DataLine] = {}
        self.visible = True

    @abstractmethod
    def add_data_line(self, unique_id: str, config: Dict[str, Any]) -> bool:
        """Add a data line to this chart.

        Args:
            unique_id: Unique identifier for the line (format: "interface_dataId")
            config: Configuration dictionary containing:
                - display_name: str
                - color: str
                - interface_type: str
                - data_id: int

        Returns:
            True if line was added successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_data_line(self, unique_id: str) -> bool:
        """Remove a data line from this chart.

        Args:
            unique_id: Unique identifier of the line to remove

        Returns:
            True if line was removed successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_required_dimensions(self) -> int:
        """Return number of dimensions required for this chart type.

        Returns:
            2 for XY charts, 3 for XYZ charts
        """
        pass

    @abstractmethod
    def validate_data_point(self, point: Any) -> bool:
        """Validate if a data point is compatible with this chart type.

        Args:
            point: Data point to validate (PlotDataPoint)

        Returns:
            True if compatible, False otherwise
        """
        pass

    @abstractmethod
    def get_qml_component(self) -> str:
        """Return QML component path for this chart type.

        Returns:
            QML component path (e.g., "qrc:/qt/qml/content/ChartTypes/XYChart.qml")
        """
        pass

    def get_line(self, unique_id: str) -> Optional[DataLine]:
        """Get a data line by its unique ID.

        Args:
            unique_id: Unique identifier of the line

        Returns:
            DataLine if found, None otherwise
        """
        return self.data_lines.get(unique_id)

    def get_all_lines(self) -> list[DataLine]:
        """Get all data lines in this chart.

        Returns:
            List of DataLine objects
        """
        return list(self.data_lines.values())

    def set_visible(self, visible: bool) -> None:
        """Set chart visibility.

        Args:
            visible: True to show, False to hide
        """
        self.visible = visible

    def is_visible(self) -> bool:
        """Check if chart is visible.

        Returns:
            True if visible, False otherwise
        """
        return self.visible

    def to_dict(self) -> Dict[str, Any]:
        """Convert chart to dictionary for serialization.

        Returns:
            Dictionary representation of the chart
        """
        return {
            "chart_id": self.chart_id,
            "name": self.name,
            "chart_type": self.chart_type.value,
            "visible": self.visible,
            "data_lines": [
                {
                    "unique_id": line.unique_id,
                    "display_name": line.display_name,
                    "color": line.color,
                    "visible": line.visible,
                    "interface_type": line.interface_type,
                    "data_id": line.data_id
                }
                for line in self.data_lines.values()
            ]
        }

    def __repr__(self) -> str:
        """String representation of the chart."""
        return f"<{self.__class__.__name__}(id={self.chart_id}, name={self.name}, lines={len(self.data_lines)})>"
