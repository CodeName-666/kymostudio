# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Deterministic retention stress check; NOT a GUI/FPS or transport benchmark."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from Core.samples import Sample, SampleStore
from Core.buffering import FrameBuffer


def main() -> None:
    store, frames = SampleStore(), FrameBuffer(max_points=4096, max_series=256)
    count = 300000
    keys = [f'stress_{i}' for i in range(32)]
    start = time.perf_counter()
    for i in range(count):
        key = keys[i % len(keys)]
        t = i / 1000.0
        store.append(key, Sample(t=t, x=None, y=float(i % 100), z=None, timestamp=t, rx_time=t))
        frames.append(key, (t, float(i % 100), t, False))
    elapsed = time.perf_counter() - start
    assert store.total_count == 250000
    assert store.evicted == 50000
    assert all(len(store.samples(key)) <= 20000 for key in keys)
    assert all(len(points) <= 4096 for points in frames.queues.values())
    print(json.dumps({'scope': 'raw-store + display-queue only; no Qt or transport',
        'input_samples': count, 'signals': len(keys), 'raw_retained': store.total_count,
        'raw_evicted': store.evicted, 'display_retained': sum(map(len, frames.queues.values())),
        'elapsed_seconds': round(elapsed, 3), 'python': sys.version.split()[0]}, indent=2))

if __name__ == '__main__':
    main()
