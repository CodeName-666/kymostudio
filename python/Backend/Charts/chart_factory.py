# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Chart Factory - Factory pattern for creating chart instances."""

from typing import Optional
from .base_chart import BaseChart, ChartType
from .xy_chart import XYLineChart, XYScatterChart
from .time_series_chart import TimeSeriesChart
from .xyz_chart import XYZScatterChart


class ChartFactory:
    """Factory for creating chart instances based on chart type.

    This factory implements the Factory pattern to create appropriate
    chart objects based on the requested ChartType.

    Example:
        factory = ChartFactory()
        chart = factory.create_chart("chart_1", "My Chart", ChartType.XY_LINE)
    """

    @staticmethod
    def create_chart(chart_id: str, name: str, chart_type: ChartType) -> Optional[BaseChart]:
        """Create a chart instance of the specified type.

        Args:
            chart_id: Unique identifier for the new chart
            name: Display name for the chart
            chart_type: Type of chart to create (from ChartType enum)

        Returns:
            BaseChart instance of the appropriate type, or None if type is unknown

        Raises:
            ValueError: If chart_id or name is empty
        """
        if not chart_id:
            raise ValueError("chart_id cannot be empty")
        if not name:
            raise ValueError("name cannot be empty")

        # Map chart types to their implementations
        chart_map = {
            ChartType.XY_LINE: XYLineChart,
            ChartType.XY_SCATTER: XYScatterChart,
            ChartType.TIME_SERIES: TimeSeriesChart,
            ChartType.XYZ_SCATTER: XYZScatterChart,
            # Future chart types with dedicated renderers:
            # ChartType.XYZ_SURFACE: XYZSurfaceChart,
            # ChartType.BAR: BarChart,
            # ChartType.HEATMAP: HeatmapChart,
        }

        chart_class = chart_map.get(chart_type)
        if chart_class is None:
            print(f"Warning: Unknown chart type: {chart_type}")
            return None

        return chart_class(chart_id, name)

    @staticmethod
    def get_supported_types() -> list[ChartType]:
        """Get list of currently supported chart types.

        Returns:
            List of supported ChartType enums
        """
        return [
            ChartType.XY_LINE,
            ChartType.XY_SCATTER,
            ChartType.TIME_SERIES,
            ChartType.XYZ_SCATTER,
        ]

    @staticmethod
    def is_type_supported(chart_type: ChartType) -> bool:
        """Check if a chart type is currently supported.

        Args:
            chart_type: ChartType to check

        Returns:
            True if supported, False otherwise
        """
        return chart_type in ChartFactory.get_supported_types()

    @staticmethod
    def get_default_chart_type() -> ChartType:
        """Get the default chart type for new charts.

        Returns:
            ChartType.XY_LINE (standard 2D line chart)
        """
        return ChartType.XY_LINE
