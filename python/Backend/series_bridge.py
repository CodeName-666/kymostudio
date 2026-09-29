"""Main-thread Qt Charts batch bridge; coordinates are never downsampled here."""
import math

from PySide6.QtCore import QObject, QPointF, Slot
from PySide6.QtCharts import QXYSeries
from PySide6.QtQml import QJSValue


class SeriesBridge(QObject):
    @Slot(QObject, 'QVariant', int, result=int)
    def appendBatch(self, series: QObject, points, limit: int) -> int:
        if not isinstance(series, QXYSeries):
            return 0
        if isinstance(points, QJSValue):
            points = points.toVariant()
        limit = max(1, min(int(limit), 50000))
        batch = []
        for point in (points or [])[-limit:]:
            if len(point) < 2:
                continue
            x, y = point[:2]
            if type(x) not in (int, float) or type(y) not in (int, float):
                continue
            try:
                if math.isfinite(x) and math.isfinite(y):
                    batch.append(QPointF(float(x), float(y)))
            except (OverflowError, ValueError):
                continue
        if len(batch) >= limit:
            series.replace(batch)
        else:
            excess = min(series.count(), max(0, series.count() + len(batch) - limit))
            if excess:
                series.removePoints(0, excess)
            if batch:
                series.append(batch)
        return series.count()
