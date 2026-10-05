# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Regression tests use the real data model, without a Qt substitute."""
import math
import pytest
from Receiver.message import PlotDataPoint

@pytest.mark.parametrize("field", ["value", "x", "timestamp", "z_value"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True, False])
def test_rejects_non_finite_and_boolean_coordinates(field, value):
    kwargs = {"id": 1, "value": 2.0, field: value}
    with pytest.raises(ValueError):
        PlotDataPoint(**kwargs)

@pytest.mark.parametrize("value", [True, False, -1, 256, 1.0, "1"])
def test_requires_byte_integer_id(value):
    with pytest.raises(ValueError):
        PlotDataPoint(id=value, value=1.0)

def test_negative_timestamp_rejected():
    with pytest.raises(ValueError):
        PlotDataPoint(id=0, value=1, timestamp=-1)

def test_zero_and_optional_coordinates_are_valid():
    point = PlotDataPoint(id=0, value=0, x=0, z_value=0, timestamp=0)
    assert point.get_dimensions() == 3
    assert point.is_3d()
