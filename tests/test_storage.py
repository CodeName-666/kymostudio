# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Raw retention and display back-pressure are independent and bounded."""
import csv
import math
import pytest
from Core.samples import Sample, SampleStore, export_csv
from Core.buffering import FrameBuffer, peak_envelope


def sample(y, t=0):
    return Sample(t=t, x=None, y=y, z=None, timestamp=None, rx_time=t)


def test_per_signal_and_global_bounds():
    store = SampleStore(max_per_signal=3, max_total=4, max_signals=2)
    for i in range(5): store.append('a', sample(i, i))
    assert [p.y for p in store.samples('a')] == [2, 3, 4]
    assert store.evicted == 2
    store.append('b', sample(6, 6)); store.append('b', sample(7, 7))
    assert store.total_count == 4
    assert [p.y for p in store.samples('a')] == [3, 4]
    assert store.evicted == 3
    assert not store.append('c', sample(8, 8))
    assert store.rejected == 1


def test_statistics_are_retained_window_statistics():
    store = SampleStore(max_per_signal=4)
    for i in [100, 1, 2, 3, 4]: store.append('a', sample(i, i))
    stats = store.statistics('a')
    assert stats['count'] == 4
    assert stats['received'] == 5
    assert stats['min'] == 1 and stats['max'] == 4
    assert stats['mean'] == 2.5
    assert stats['rms'] == pytest.approx(math.sqrt(7.5))
    assert stats['stddev'] == pytest.approx(math.sqrt(1.25))


def test_large_finite_values_do_not_overflow_statistics():
    store = SampleStore()
    for y in [1e308, -1e308]: store.append('a', sample(y))
    stats = store.statistics('a')
    assert stats['mean'] == 0
    assert stats['rms'] == 1e308
    assert stats['stddev'] == 1e308


def test_remove_and_clear_remove_raw_samples():
    store = SampleStore()
    store.append('a', sample(1)); store.append('b', sample(2))
    store.remove('a')
    assert store.total_count == 1 and store.statistics('a')['count'] == 0
    store.clear()
    assert store.total_count == 0


def test_csv_has_raw_optional_coordinates_and_injection_safe_names(tmp_path):
    store = SampleStore()
    store.append('=cmd', Sample(1., None, -3., 4., 42., 123.))
    target = tmp_path / 'data.csv'
    assert export_csv(target, store.snapshot(), {'=cmd': '=HYPERLINK("x")'}) == 1
    with target.open(encoding='utf-8-sig', newline='') as f: rows = list(csv.DictReader(f))
    assert rows[0]['signal_id'].startswith("'")
    assert rows[0]['name'].startswith("'")
    assert rows[0]['x'] == ''
    assert float(rows[0]['y']) == -3
    assert float(rows[0]['timestamp_s']) == 42


def test_buffer_only_flushes_when_explicitly_drained():
    buffer = FrameBuffer(max_points=4, max_series=2)
    for i in range(10): buffer.append('a', (i, i))
    assert buffer.pending_count == 4
    assert buffer.dropped == 6
    assert buffer.drain() == {'a': [(6,6),(7,7),(8,8),(9,9)]}
    assert buffer.drain() == {}


def test_buffer_limits_series_and_can_remove_a_stream():
    buffer = FrameBuffer(max_points=3, max_series=1)
    assert buffer.append('a', (1,2))
    assert not buffer.append('b', (1,2))
    buffer.remove('a')
    assert buffer.append('b', (2,3))


def test_peak_envelope_keeps_spikes_endpoints_and_input_order():
    points = [(i, 99 if i == 513 else (-77 if i == 400 else 0)) for i in range(1000)]
    result = peak_envelope(points, 80)
    assert len(result) <= 80
    assert result[0] == points[0] and result[-1] == points[-1]
    assert (513,99) in result and (400,-77) in result
    assert [p[0] for p in result] == sorted(p[0] for p in result)
    assert len(points) == 1000
