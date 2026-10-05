# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Erzeugt die README-Screenshots von KymoStudio mit synthetischen Demo-Daten.

Aufruf: .venv/Scripts/python.exe tools/capture_screenshots.py [--offscreen]

Die App läuft mit einem temporären Profil; Benutzereinstellungen bleiben
unberührt. Ergebnis: docs/screenshots/*.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/screenshots"
sys.path.insert(0, str(ROOT / "python"))

parser = argparse.ArgumentParser()
parser.add_argument("--offscreen", action="store_true", help="ohne sichtbares Fenster rendern")
parser.add_argument("--seconds", type=float, default=30, help="Laufzeit der Demo vor dem ersten Bild")
parser.add_argument("--width", type=int, default=1760)
parser.add_argument("--height", type=int, default=1000)
options = parser.parse_args()
profile = tempfile.TemporaryDirectory(prefix="kymo-shots-")
os.environ["KYMO_CONFIG_HOME"] = profile.name
if options.offscreen:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"))

from PySide6.QtCore import QCoreApplication, QSettings, QTimer  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtQml import QQmlExpression  # noqa: E402
from PySide6.QtQuickControls2 import QQuickStyle  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from Backend.backend import Backend  # noqa: E402
from Backend.Windows.window_manager_bridge import WindowManagerBridge  # noqa: E402
from Core.configuration import ConfigurationRepository  # noqa: E402
from Core.paths import PROJECT_ROOT, user_config_path  # noqa: E402
from Studio.studio import KymoStudio  # noqa: E402

QCoreApplication.setOrganizationName("KymoStudio")
QCoreApplication.setApplicationName("KymoStudio")
QSettings.setDefaultFormat(QSettings.IniFormat)
QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, profile.name)
QQuickStyle.setStyle("Fusion")
app = QApplication.instance() or QApplication([sys.argv[0]])
app.setWindowIcon(QIcon(str(PROJECT_ROOT / "resources/icons/kymotrace.ico")))
with (PROJECT_ROOT / "config/config.json").open(encoding="utf-8-sig") as stream:
    defaults = json.load(stream)
config = ConfigurationRepository(user_config_path(), defaults).load()
studio = KymoStudio([sys.argv[0]], config)
backend = Backend(user_config_path())
backend.config(config)
studio.set_backend(backend)
studio.set_window_manager(WindowManagerBridge())
studio.load_app()
root = studio.rootObjects()[0]
root.setWidth(options.width)
root.setHeight(options.height)


def js(code: str):
    expression = QQmlExpression(studio.engine.rootContext(), root, code)
    value, failed = expression.evaluate()
    if expression.hasError() and expression.error().description():
        print("JS-Fehler:", expression.error().toString(), file=sys.stderr)
    return value


def build_showcase() -> None:
    js("startDemo()")
    js("""(function () {
        var wc = workspaceController
        var chartId = wc.createChart("xy_line", qsTr("XY · Lissajous und Kreis"))
        var conn = Backend.create_connection("Test", "Demo XY", {type: "XYMulti", sample_ms: 20})
        var names = ["Kreis", "Lissajous"]
        for (var i = 0; i < 2; i++) {
            var uid = conn + "_" + i
            wc.addSignal(uid, names[i], ["#C79BFF", "#E78AB8"][i], "Test", i, {})
            wc.setSignalCharts(uid, [{chartId: chartId, chartType: "xy_line", valueField: null}])
        }
        Backend.start_connection(conn)
        refreshConnections()
        wc.layoutMode = "tile"
        scheduleLayout()
    })()""")


def capture(name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image = root.grabWindow()
    path = OUT / name
    image.save(str(path))
    print("gespeichert:", path.relative_to(ROOT), image.width(), "x", image.height())


def finish() -> None:
    backend.shutdown()
    app.quit()


QTimer.singleShot(300, build_showcase)
first = int(options.seconds * 1000)


def tiled() -> None:
    js("""(function () {
        var wc = workspaceController
        wc.layoutMode = 'tile'; applyLayout(); wc.fitAll()
        for (var i = 0; i < wc.chartModel.count; i++) {
            var chart = wc.chartModel.get(i)
            var window = wc.windowForChart(chart.chartId)
            if (chart.chartType === "time_series" && window && window.chartRenderer)
                window.chartRenderer.setTimeWindow(10)
        }
    })()""")


def focused_xy() -> None:
    js("""(function () {
        var wc = workspaceController
        for (var i = 0; i < wc.chartModel.count; i++)
            if (wc.chartModel.get(i).chartType === "xy_line") wc.activeChartId = wc.chartModel.get(i).chartId
        wc.layoutMode = 'focus'; applyLayout(); wc.fitAll()
    })()""")


STEPS = [
    (first - 1500, tiled),
    (1500, lambda: capture("kymostudio-workbench.png")),
    (300, focused_xy),
    (1700, lambda: capture("kymostudio-xy.png")),
    (300, finish),
]


def run_steps(index: int = 0) -> None:
    """Führt die Schritte nacheinander aus; jeder plant erst danach den nächsten."""
    if index >= len(STEPS):
        return
    delay, step = STEPS[index]

    def execute() -> None:
        try:
            step()
        except Exception as exc:  # Fehler sichtbar machen, statt still abzubrechen
            print("Schritt fehlgeschlagen:", repr(exc), file=sys.stderr, flush=True)
        run_steps(index + 1)

    QTimer.singleShot(delay, execute)


run_steps()
root.show()
app.exec()
