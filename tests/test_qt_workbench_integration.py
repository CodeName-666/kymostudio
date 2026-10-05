"""Exercise real Qt APIs; these checks must not use mocked PySide modules."""
import os
import subprocess
import sys
from pathlib import Path
import pytest
pytest.importorskip("PySide6", reason="Real Qt integration requires requirements-dev.txt")
from PySide6.QtCore import QCoreApplication
from PySide6.QtCharts import QLineSeries
from Backend.series_bridge import SeriesBridge


def test_native_batch_bridge_keeps_exact_tail_and_ignores_nonfinite_points():
    app = QCoreApplication.instance() or QCoreApplication([])
    bridge, series = SeriesBridge(), QLineSeries()
    assert bridge.appendBatch(series, [[i, i * 2] for i in range(2000)], 100) == 100
    assert series.at(0).x() == 1900
    assert series.at(99).x() == 1999
    assert bridge.appendBatch(series, [[2000, 3], [2001, float("nan")], [True, 1]], 100) == 100
    assert series.at(0).x() == 1901
    assert series.at(99).x() == 2000
    assert bridge.appendBatch(series, [], 20) == 20
    assert series.at(0).x() == 1981


def test_qml_demo_launch_and_acquisition_in_separate_process():
    pytest.importorskip("can")
    pytest.importorskip("serial")
    pytest.importorskip("paho.mqtt.client")
    project = Path(__file__).resolve().parents[1]
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software"}
    result = subprocess.run([sys.executable, str(project / "run.py"), "--smoke-test"],
                            cwd=project, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"qt_smoke": "passed"' in result.stdout
