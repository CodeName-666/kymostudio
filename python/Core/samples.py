"""Bounded raw measurement retention and statistics, independent of rendering."""
from __future__ import annotations

import csv
import math
import os
import tempfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class Sample:
    """Raw values plus elapsed reception time; optional values are not invented."""
    t: float
    x: float | None
    y: float
    z: float | None
    timestamp: float | None
    rx_time: float


class SampleStore:
    """O(1) append/eviction with both per-signal and global sample budgets.

    This is a bounded analysis window, not a lossless disk recorder. Statistics
    always refer to the retained window; ``received`` is the session counter.
    """

    def __init__(self, max_per_signal: int = 20000, max_total: int = 250000,
                 max_signals: int = 256) -> None:
        if min(max_per_signal, max_total, max_signals) < 1:
            raise ValueError("Retention limits must be positive")
        self.max_per_signal = max_per_signal
        self.max_total = max_total
        self.max_signals = max_signals
        self._signals: dict[str, OrderedDict[int, Sample]] = {}
        self._global: OrderedDict[int, tuple[str, Sample]] = OrderedDict()
        self._received: dict[str, int] = {}
        self._sequence = 0
        self.evicted = 0
        self.rejected = 0

    @property
    def total_count(self) -> int:
        return len(self._global)

    def append(self, key: str, sample: Sample) -> bool:
        if key not in self._received and len(self._received) >= self.max_signals:
            self.rejected += 1
            return False
        self._received[key] = self._received.get(key, 0) + 1
        signal = self._signals.setdefault(key, OrderedDict())
        self._sequence += 1
        sequence = self._sequence
        signal[sequence] = sample
        self._global[sequence] = (key, sample)
        if len(signal) > self.max_per_signal:
            oldest, _ = signal.popitem(last=False)
            self._global.pop(oldest)
            self.evicted += 1
        while len(self._global) > self.max_total:
            oldest, (owner, _) = self._global.popitem(last=False)
            del self._signals[owner][oldest]
            self.evicted += 1
        return True

    def samples(self, key: str) -> list[Sample]:
        return list(self._signals.get(key, {}).values())

    def snapshot(self, key: str = '') -> list[tuple[str, Sample]]:
        return [(key, p) for p in self.samples(key)] if key else list(self._global.values())

    def statistics(self, key: str) -> dict:
        values = self.samples(key)
        count = len(values)
        result = {'count': count, 'received': self._received.get(key, 0),
                  'min': None, 'max': None, 'mean': None, 'rms': None,
                  'stddev': None, 'latest': None, 'duration': 0.0}
        if not values:
            return result
        ys = [p.y for p in values]
        scale = max(map(abs, ys)) or 1.0
        normalized = [y / scale for y in ys]
        mean = math.fsum(normalized) / count
        result.update(
            min=min(ys), max=max(ys), latest=ys[-1], mean=mean * scale,
            rms=math.sqrt(math.fsum(y*y for y in normalized) / count) * scale,
            stddev=math.sqrt(math.fsum((y-mean)**2 for y in normalized) / count) * scale,
            duration=max(0.0, values[-1].t - values[0].t),
        )
        return result

    def remove(self, key: str) -> None:
        for sequence in self._signals.pop(key, {}):
            self._global.pop(sequence, None)
        self._received.pop(key, None)

    def clear(self) -> None:
        self._signals.clear()
        self._global.clear()
        self._received.clear()
        self.evicted = self.rejected = 0


def _safe_metadata(value: str) -> str:
    """Prevent spreadsheet formula evaluation of external names/identifiers."""
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else value


def export_csv(target: Path, rows: Iterable[tuple[str, Sample]],
               names: Mapping[str, str] | None = None) -> int:
    """Atomically export raw retained samples, never decimated display points."""
    names = names or {}
    target = Path(target).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    count = 0
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8-sig', newline='',
                                         dir=target.parent, prefix='.'+target.name+'.',
                                         suffix='.tmp', delete=False) as stream:
            temporary = stream.name
            writer = csv.writer(stream)
            writer.writerow(('signal_id', 'name', 'elapsed_s', 'x', 'y', 'z', 'timestamp_s', 'received_unix_s'))
            for key, p in rows:
                writer.writerow((_safe_metadata(key), _safe_metadata(names.get(key, key)),
                                 p.t, p.x, p.y, p.z, p.timestamp, p.rx_time))
                count += 1
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)
    return count
