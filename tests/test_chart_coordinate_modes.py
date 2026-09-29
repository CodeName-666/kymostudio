"""Regression tests for the time-series / Cartesian-XY boundary."""

from __future__ import annotations

import pytest
pytest.importorskip("PySide6", reason="Install requirements-dev.txt to run Qt integration tests")
pytest.importorskip("can", reason="python-can transport dependency missing")
pytest.importorskip("serial", reason="pyserial transport dependency missing")
pytest.importorskip("paho.mqtt.client", reason="paho-mqtt transport dependency missing")

import sys
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from Backend.Charts.xy_chart import XYLineChart  # noqa: E402
from Backend.backend import Backend  # noqa: E402
from Receiver.message import PlotDataPoint  # noqa: E402


class ChartCoordinateModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QCoreApplication.instance() or QCoreApplication([])
        Backend._Backend__backend_instance = None
        cls.backend = Backend()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.backend.shutdown()
        Backend._Backend__backend_instance = None

    def _capture_buffered_point(self, payload: bytes) -> tuple:
        captured: list[tuple] = []
        self.backend._queue_event = lambda *args: None
        self.backend._buffer_point = lambda *args: captured.append(args)

        self.backend._on_receiver_data("Serial", payload)

        self.assertEqual(len(captured), 1)
        return captured[0]

    def test_cartesian_xy_preserves_protocol_x_and_y(self) -> None:
        unique_id, x, y, _time_value, has_explicit_x = self._capture_buffered_point(
            b'{"id": 7, "x": 12.5, "y": -3.0}'
        )

        self.assertEqual(unique_id, "Serial_7")
        self.assertEqual(x, 12.5)
        self.assertEqual(y, -3.0)
        self.assertTrue(has_explicit_x)

    def test_time_series_fallback_is_marked_as_not_cartesian_x(self) -> None:
        _unique_id, x, y, time_value, has_explicit_x = self._capture_buffered_point(
            b'{"id": 2, "value": 42.0, "timestamp": 1000.0}'
        )

        self.assertEqual(x, 0.0)
        self.assertEqual(time_value, 0.0)
        self.assertEqual(y, 42.0)
        self.assertFalse(has_explicit_x)

    def test_xy_chart_requires_an_explicit_protocol_x(self) -> None:
        chart = XYLineChart("xy", "Cartesian XY")

        self.assertTrue(chart.validate_data_point(PlotDataPoint(id=1, x=1.5, value=2.5)))
        self.assertFalse(
            chart.validate_data_point(PlotDataPoint(id=1, value=2.5, timestamp=10.0))
        )


if __name__ == "__main__":
    unittest.main()
