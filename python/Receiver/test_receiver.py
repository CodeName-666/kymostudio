"""Synthetic test receiver that generates test data for the chart."""

from __future__ import annotations

import json
import math
import time
from typing import Any, Dict, Optional

from PySide6.QtCore import QTimer

from Logger import logger

from .receiver import Receiver


class TestReceiver(Receiver):
    """Produces periodic test samples to exercise the chart pipeline.

    Supports multiple test modes:
    - Sinus: Single or multiple sine waves
    - Ramp: Linear ramp
    - Random: Random values
    - Multi: Multiple data IDs with different patterns
    """

    __test__ = False

    def __init__(self, defaults: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(receiver_thread=None)
        self._settings: Dict[str, Any] = defaults.copy() if defaults else {}
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._t = 0.0
        self._start_time = 0.0
        if self._settings:
            super().config(self._settings)

    def _on_config_updated(self) -> None:
        # Restart timer with new interval when config changes.
        interval = int(self._settings.get("sample_ms", 50))
        if interval < 5:
            interval = 5
        self._timer.setInterval(interval)

    def config(self, config: Dict[str, Any]) -> None:
        self._settings.update(config or {})
        super().config(self._settings)

    def open_connection(self) -> bool:
        self._t = 0.0
        self._start_time = time.monotonic()
        self._set_connected(True)
        self._timer.start()
        test_type = self._settings.get("type", "Sinus")
        logger.log_info(f"TestReceiver started: {test_type} mode")
        return True

    def close_connection(self) -> None:
        self._timer.stop()
        self._set_connected(False)
        logger.log_info("TestReceiver stopped")

    def settings_valid(self) -> bool:
        return True

    def _tick(self) -> None:
        """Generate test data based on configured test type."""
        test_type = self._settings.get("type", "Sinus")
        use_timestamp = self._settings.get("use_timestamp", True)
        dt = self._timer.interval() / 1000.0
        self._t += dt

        # Calculate timestamp if enabled
        timestamp = time.monotonic() - self._start_time if use_timestamp else None

        if test_type == "XYMulti":
            self._emit_xy_multi()
        elif test_type in ("XY", "XYCircle"):
            self._emit_xy_circle()
        elif test_type == "Multi":
            # Send multiple IDs with different patterns
            self._emit_multi_data(timestamp)
        elif test_type == "Ramp":
            self._emit_ramp(timestamp)
        elif test_type == "Random":
            self._emit_random(timestamp)
        else:  # "Sinus" or default
            self._emit_sinus(timestamp)

    def _emit_xy_circle(self) -> None:
        """Emit X/Y points forming a circle (useful for testing XY plots)."""
        data_id = int(self._settings.get("id", 0))
        radius = float(self._settings.get("radius", 10.0))
        freq = float(self._settings.get("frequency", 0.2))  # Hz

        x = radius * math.cos(2 * math.pi * freq * self._t)
        y = radius * math.sin(2 * math.pi * freq * self._t)

        payload = json.dumps({"id": data_id, "x": x, "y": y}).encode("utf-8")
        self.new_data.emit(payload)

    def _emit_xy_multi(self) -> None:
        """Emit 3 independent X/Y signals (ids 0/1/2) for XY charts."""
        radius = float(self._settings.get("radius", 10.0))

        # ID 0: Circle
        f0 = float(self._settings.get("frequency0", 0.20))
        x0 = radius * math.cos(2 * math.pi * f0 * self._t)
        y0 = radius * math.sin(2 * math.pi * f0 * self._t)
        self.new_data.emit(json.dumps({"id": 0, "x": x0, "y": y0}).encode("utf-8"))

        # ID 1: Lissajous-like curve
        f1x = float(self._settings.get("frequency1x", 0.15))
        f1y = float(self._settings.get("frequency1y", 0.25))
        a1 = float(self._settings.get("amplitude1", radius * 0.8))
        x1 = a1 * math.sin(2 * math.pi * f1x * self._t)
        y1 = a1 * math.sin(2 * math.pi * f1y * self._t + math.pi / 2)
        self.new_data.emit(json.dumps({"id": 1, "x": x1, "y": y1}).encode("utf-8"))

        # ID 2: Spiral (clamped radius)
        f2 = float(self._settings.get("frequency2", 0.35))
        grow = float(self._settings.get("growth2", 1.0))
        r2 = min(radius, (self._t * grow) % (radius + 0.0001))
        x2 = r2 * math.cos(2 * math.pi * f2 * self._t)
        y2 = r2 * math.sin(2 * math.pi * f2 * self._t)
        self.new_data.emit(json.dumps({"id": 2, "x": x2, "y": y2}).encode("utf-8"))

    def _emit_sinus(self, timestamp: Optional[float]) -> None:
        """Emit sine wave data."""
        data_id = int(self._settings.get("id", 0))
        amp = float(self._settings.get("amplitude", 10.0))
        freq = float(self._settings.get("frequency", 1.0))
        y = amp * math.sin(2 * math.pi * freq * self._t)

        data = {"id": data_id, "value": y}
        if timestamp is not None:
            data["timestamp"] = timestamp

        payload = json.dumps(data).encode("utf-8")
        self.new_data.emit(payload)

    def _emit_ramp(self, timestamp: Optional[float]) -> None:
        """Emit linear ramp data."""
        data_id = int(self._settings.get("id", 0))
        slope = float(self._settings.get("slope", 1.0))
        y = slope * self._t

        data = {"id": data_id, "value": y}
        if timestamp is not None:
            data["timestamp"] = timestamp

        payload = json.dumps(data).encode("utf-8")
        self.new_data.emit(payload)

    def _emit_random(self, timestamp: Optional[float]) -> None:
        """Emit random data."""
        import random
        data_id = int(self._settings.get("id", 0))
        min_val = float(self._settings.get("min", 0.0))
        max_val = float(self._settings.get("max", 100.0))
        y = random.uniform(min_val, max_val)

        data = {"id": data_id, "value": y}
        if timestamp is not None:
            data["timestamp"] = timestamp

        payload = json.dumps(data).encode("utf-8")
        self.new_data.emit(payload)

    def _emit_multi_data(self, timestamp: Optional[float]) -> None:
        """Emit multiple data IDs with different patterns."""
        # ID 0: Sine wave
        y0 = 10 * math.sin(2 * math.pi * 1.0 * self._t)
        data0 = {"id": 0, "value": y0}
        if timestamp is not None:
            data0["timestamp"] = timestamp
        self.new_data.emit(json.dumps(data0).encode("utf-8"))

        # ID 1: Cosine wave (90° phase shift)
        y1 = 10 * math.cos(2 * math.pi * 1.0 * self._t)
        data1 = {"id": 1, "value": y1}
        if timestamp is not None:
            data1["timestamp"] = timestamp
        self.new_data.emit(json.dumps(data1).encode("utf-8"))

        # ID 2: Higher frequency sine
        y2 = 5 * math.sin(2 * math.pi * 2.0 * self._t)
        data2 = {"id": 2, "value": y2}
        if timestamp is not None:
            data2["timestamp"] = timestamp
        self.new_data.emit(json.dumps(data2).encode("utf-8"))


__all__ = ["TestReceiver"]
