"""Main-thread Qt Charts batch bridge; coordinates are never downsampled here."""
import math

import shiboken6
from PySide6.QtCore import QObject, QPointF, Slot
from PySide6.QtCharts import QXYSeries
from PySide6.QtQml import QJSValue


class SeriesBridge(QObject):
    """Appends batches through one ``replace`` per call.

    ``QXYSeries.append(list)`` adds point by point and Qt Charts recomputes the
    whole series geometry for every point, which is quadratic in the batch size.
    A Python mirror of each series' points allows a single ``replace`` instead.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mirrors: dict[int, list[QPointF]] = {}

    def _mirror(self, series: QXYSeries) -> list[QPointF]:
        key = shiboken6.getCppPointer(series)[0]
        mirror = self._mirrors.get(key)
        if mirror is None:
            series.destroyed.connect(lambda *_: self._mirrors.pop(key, None))
        if mirror is None or len(mirror) != series.count():
            # First use, or the series was changed elsewhere (e.g. cleared).
            mirror = self._mirrors[key] = list(series.points())
        return mirror

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
        mirror = self._mirror(series)
        if not batch and len(mirror) <= limit:
            return len(mirror)
        mirror.extend(batch)
        if len(mirror) > limit:
            del mirror[:len(mirror) - limit]
        series.replace(mirror)
        return len(mirror)
