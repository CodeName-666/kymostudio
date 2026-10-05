"""Chart Data Router - Routes data points to appropriate floating windows."""

from typing import Dict, Optional, List, Tuple
from PySide6.QtCore import QObject, Signal, Slot
from Receiver.message import PlotDataPoint
from Logger import logger


class ChartDataRouter(QObject):
    """Routes incoming data points to appropriate charts based on chart ID.

    This router manages the flow of data from the receiver to floating chart windows.
    It supports both 2D (XY) and 3D (XYZ) data points and routes them to the
    correct chart renderer via Qt signals.

    Signals:
        data_point_2d: Emitted for 2D points (chartId, uniqueId, x, y)
        data_point_3d: Emitted for 3D points (chartId, uniqueId, x, y, z)
        data_batch_2d: Emitted for 2D point batches (chartId, uniqueId, points)
        data_batch_3d: Emitted for 3D point batches (chartId, uniqueId, points)
    """

    # Signals for routing data to charts
    data_point_2d = Signal(str, str, float, float)  # (chartId, uniqueId, x, y)
    data_point_3d = Signal(str, str, float, float, float)  # (chartId, uniqueId, x, y, z)
    data_batch_2d = Signal(str, str, list)  # (chartId, uniqueId, [[x,y], ...])
    data_batch_3d = Signal(str, str, list)  # (chartId, uniqueId, [[x,y,z], ...])

    def __init__(self):
        """Initialize the chart data router."""
        super().__init__()

        # Mapping: data_id -> chart_id (which chart should receive this data)
        self._data_to_chart_map: Dict[int, str] = {}

        # Mapping: data_id -> unique_id (line/scatter plot identifier)
        self._data_to_line_map: Dict[int, str] = {}

        # Auto-increment X values for data points without timestamp
        self._auto_x_values: Dict[str, float] = {}

        logger.log_info("ChartDataRouter initialized")

    def register_data_line(self, data_id: int, chart_id: str, unique_id: str) -> None:
        """Register a data line to route data to a specific chart.

        Args:
            data_id: The data ID from PlotDataPoint (0-255)
            chart_id: The target chart ID (floating window ID)
            unique_id: The unique line/scatter plot ID within the chart
        """
        self._data_to_chart_map[data_id] = chart_id
        self._data_to_line_map[data_id] = unique_id
        self._auto_x_values[unique_id] = 0.0

        logger.log_info(f"ChartDataRouter: Registered data_id={data_id} -> chart={chart_id}, line={unique_id}")

    def unregister_data_line(self, data_id: int) -> None:
        """Unregister a data line.

        Args:
            data_id: The data ID to unregister
        """
        if data_id in self._data_to_chart_map:
            unique_id = self._data_to_line_map.get(data_id)
            del self._data_to_chart_map[data_id]
            del self._data_to_line_map[data_id]

            if unique_id and unique_id in self._auto_x_values:
                del self._auto_x_values[unique_id]

            logger.log_info(f"ChartDataRouter: Unregistered data_id={data_id}")

    def get_chart_for_data(self, data_id: int) -> Optional[str]:
        """Get the chart ID that should receive data for this data ID.

        Args:
            data_id: The data ID

        Returns:
            Chart ID or None if not registered
        """
        return self._data_to_chart_map.get(data_id)

    @Slot(object)
    def route_data_point(self, point: PlotDataPoint) -> bool:
        """Route a single data point to the appropriate chart.

        Args:
            point: The PlotDataPoint to route

        Returns:
            True if routed successfully, False if data_id not registered
        """
        chart_id = self._data_to_chart_map.get(point.id)
        if chart_id is None:
            # Not registered - silently ignore (not an error, just not visualized)
            return False

        unique_id = self._data_to_line_map.get(point.id)
        if unique_id is None:
            logger.log_warning(f"ChartDataRouter: No unique_id for data_id={point.id}")
            return False

        # Determine X value (explicit X, timestamp, or auto-increment)
        if getattr(point, "x", None) is not None:
            x_val = float(point.x)  # type: ignore[arg-type]
        elif point.timestamp is not None:
            x_val = point.timestamp
        else:
            x_val = self._auto_x_values.get(unique_id, 0.0)
            self._auto_x_values[unique_id] = x_val + 1.0

        y_val = point.value

        # Route based on dimensionality
        if point.is_3d():
            z_val = point.z_value
            self.data_point_3d.emit(chart_id, unique_id, x_val, y_val, z_val)
            logger.log_debug(f"ChartDataRouter: Routed 3D point to chart={chart_id}, line={unique_id}")
        else:
            self.data_point_2d.emit(chart_id, unique_id, x_val, y_val)
            logger.log_debug(f"ChartDataRouter: Routed 2D point to chart={chart_id}, line={unique_id}")

        return True

    @Slot(int, list)
    def route_data_batch(self, data_id: int, points: List[PlotDataPoint]) -> bool:
        """Route a batch of data points to the appropriate chart.

        Args:
            data_id: The data ID
            points: List of PlotDataPoint objects

        Returns:
            True if routed successfully, False if data_id not registered
        """
        if not points:
            return True

        chart_id = self._data_to_chart_map.get(data_id)
        if chart_id is None:
            return False

        unique_id = self._data_to_line_map.get(data_id)
        if unique_id is None:
            logger.log_warning(f"ChartDataRouter: No unique_id for data_id={data_id}")
            return False

        # Check dimensionality from first point
        is_3d = points[0].is_3d()

        # Convert points to list format
        if is_3d:
            point_list = []
            for p in points:
                if getattr(p, "x", None) is not None:
                    x_val = float(p.x)  # type: ignore[arg-type]
                else:
                    x_val = p.timestamp if p.timestamp is not None else self._auto_x_values.get(unique_id, 0.0)
                if getattr(p, "x", None) is None and p.timestamp is None:
                    self._auto_x_values[unique_id] = x_val + 1.0
                point_list.append([x_val, p.value, p.z_value])

            self.data_batch_3d.emit(chart_id, unique_id, point_list)
            logger.log_debug(f"ChartDataRouter: Routed 3D batch ({len(points)} points) to chart={chart_id}")
        else:
            point_list = []
            for p in points:
                if getattr(p, "x", None) is not None:
                    x_val = float(p.x)  # type: ignore[arg-type]
                else:
                    x_val = p.timestamp if p.timestamp is not None else self._auto_x_values.get(unique_id, 0.0)
                if getattr(p, "x", None) is None and p.timestamp is None:
                    self._auto_x_values[unique_id] = x_val + 1.0
                point_list.append([x_val, p.value])

            self.data_batch_2d.emit(chart_id, unique_id, point_list)
            logger.log_debug(f"ChartDataRouter: Routed 2D batch ({len(points)} points) to chart={chart_id}")

        return True

    def clear_all(self) -> None:
        """Clear all registrations."""
        self._data_to_chart_map.clear()
        self._data_to_line_map.clear()
        self._auto_x_values.clear()
        logger.log_info("ChartDataRouter: Cleared all registrations")

    def get_stats(self) -> Dict[str, int]:
        """Get router statistics.

        Returns:
            Dictionary with registration counts
        """
        return {
            "registered_data_ids": len(self._data_to_chart_map),
            "registered_lines": len(self._data_to_line_map)
        }
