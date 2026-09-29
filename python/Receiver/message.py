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
        if type(self.id) is not int or not 0 <= self.id <= 255:
            raise ValueError("ID must be an integer between 0 and 255 (not bool)")
        for name in ("value", "x", "timestamp", "z_value"):
            value = getattr(self, name)
            if value is None and name != "value":
                continue
            if type(value) not in (int, float):
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
