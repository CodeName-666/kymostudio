"""Bounded display queues and order-preserving min/max envelope reduction."""
from __future__ import annotations

from collections import deque
from typing import Any, Sequence


class FrameBuffer:
    """A producer never triggers rendering; only the GUI frame timer drains.

    Under overload the oldest pending display samples are discarded. ``dropped``
    makes that policy observable. Raw analysis retention lives in SampleStore.
    """

    def __init__(self, max_points: int = 4096, max_series: int = 256) -> None:
        if max_points < 1 or max_series < 1:
            raise ValueError("Buffer limits must be positive")
        self.max_points = max_points
        self.max_series = max_series
        self.queues: dict[str, deque] = {}
        self.dropped = 0

    @property
    def pending_count(self) -> int:
        return sum(map(len, self.queues.values()))

    def append(self, key: str, point: Any) -> bool:
        if key not in self.queues:
            if len(self.queues) >= self.max_series:
                self.dropped += 1
                return False
            self.queues[key] = deque(maxlen=self.max_points)
        queue = self.queues[key]
        if len(queue) == self.max_points:
            self.dropped += 1
        queue.append(point)
        return True

    def drain(self) -> dict[str, list]:
        result = {key: list(queue) for key, queue in self.queues.items() if queue}
        self.queues.clear()
        return result

    def remove(self, key: str) -> None:
        self.queues.pop(key, None)

    def clear(self) -> None:
        self.queues.clear()


def peak_envelope(points: Sequence, target: int, value_index: int = 1) -> list:
    """Keep endpoints plus each bucket's minimum/maximum in acquisition order.

    This is display-only reduction for time series; it must not be used as
    analysis data or applied to Cartesian trajectories as a time sampler.
    """
    if target < 2:
        raise ValueError("At least two display points are required")
    if len(points) <= target:
        return list(points)
    if target < 4:
        return [points[0], points[-1]]
    buckets = (target - 2) // 2
    selected = [0]
    inner = len(points) - 2
    for bucket in range(buckets):
        start = 1 + (bucket * inner) // buckets
        end = 1 + ((bucket + 1) * inner) // buckets
        if start >= end:
            continue
        low = min(range(start, end), key=lambda i: points[i][value_index])
        high = max(range(start, end), key=lambda i: points[i][value_index])
        selected.extend(sorted({low, high}))
    selected.append(len(points) - 1)
    return [points[index] for index in selected]
