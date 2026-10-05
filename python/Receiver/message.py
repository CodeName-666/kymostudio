# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Validated wire-level measurement records shared by every transport."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class PlotDataPoint:
    """One measurement; protocol IDs occupy one byte and timestamps use seconds.

    ``x`` is an explicit Cartesian coordinate, *not* an inferred time coordinate.
    Keeping those meanings separate prevents time-series/XY routing mistakes.
    Invalid values are rejected here, so no transport can bypass validation.
    """

    id: int
    value: float
    x: float | None = None
    timestamp: float | None = None
    z_value: float | None = None

    def __post_init__(self) -> None:
        # Fast path for the common record: finite float value, no optional fields.
        if (self.x is None and self.timestamp is None and self.z_value is None
                and type(self.id) is int and 0 <= self.id <= 255
                and type(self.value) is float and math.isfinite(self.value)):
            return
        if type(self.id) is not int or not 0 <= self.id <= 255:
            raise ValueError("ID must be an integer between 0 and 255 (not bool)")
        for name, value in (("value", self.value), ("x", self.x),
                            ("timestamp", self.timestamp), ("z_value", self.z_value)):
            if value is None and name != "value":
                continue
            kind = type(value)
            if kind is float:
                if not math.isfinite(value):
                    raise ValueError(f"{name} must be finite")
                continue
            if kind is not int:
                raise ValueError(f"{name} must be numeric (not bool)")
            try:
                finite = math.isfinite(value)
            except (OverflowError, TypeError):
                finite = False
            if not finite:
                raise ValueError(f"{name} must be finite")
        if self.timestamp is not None and self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")

    def get_dimensions(self) -> int:
        """Return the spatial dimensionality of this sample."""
        return 3 if self.z_value is not None else 2

    def is_3d(self) -> bool:
        """Whether a Z coordinate was supplied, including a zero value."""
        return self.z_value is not None
