"""Exercise actual QML wheel handlers with Qt; run with the app's Python."""
import math
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QPoint, QPointF, QUrl, Qt, qInstallMessageHandler
from PySide6.QtGui import QWheelEvent
from PySide6.QtQml import QQmlExpression
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


def main():
    project = Path(__file__).resolve().parents[1]
    app = QApplication.instance() or QApplication([])
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    checks = 0
    try:
        for renderer in ("TimeSeriesRenderer", "XYChartRenderer"):
            view = QQuickView()
            for path in ("qml", "qml/imports", "qml/content"):
                view.engine().addImportPath(str(project / path))
            view.setResizeMode(QQuickView.SizeRootObjectToView)
            view.resize(800, 600)
            view.setSource(QUrl.fromLocalFile(str(project / f"qml/content/ChartTypes/{renderer}.qml")))
            assert view.status() == QQuickView.Ready, view.errors()
            view.show()
            QTest.qWait(100)

            def evaluate(code):
                expression = QQmlExpression(view.rootContext(), view.rootObject(), code)
                value = expression.evaluate()[0]
                assert not expression.hasError(), expression.error().toString()
                return value.toVariant() if hasattr(value, "toVariant") else value

            evaluate("createLine('test', 'Test', '#ff0000', 'Test', 0, 'y')")
            QTest.qWait(50)
            for modifiers, change_x, change_y in (
                (Qt.NoModifier, True, True),
                (Qt.ShiftModifier, True, False),
                (Qt.ControlModifier, False, True),
            ):
                for delta, factor in ((120, 0.9), (-120, 1.1)):
                    evaluate("setViewRange(0, 100, -10, 10)")
                    before = evaluate("viewSettings()")
                    pos = QPointF(400, 300)
                    event = QWheelEvent(pos, pos, QPoint(), QPoint(0, delta),
                                        Qt.NoButton, modifiers, Qt.NoScrollPhase, False)
                    QApplication.sendEvent(view, event)
                    QTest.qWait(20)
                    after = evaluate("viewSettings()")
                    for axis, changed in (("x", change_x), ("y", change_y)):
                        low, high = axis + "Min", axis + "Max"
                        expected = (before[high] - before[low]) * (factor if changed else 1)
                        actual = after[high] - after[low]
                        assert math.isclose(actual, expected, rel_tol=1e-9), (
                            renderer, modifiers, delta, axis, actual, expected, messages
                        )
                        if not changed:
                            assert after[low] == before[low] and after[high] == before[high]
                    checks += 1
            view.close()
            view.deleteLater()
            app.processEvents()
        errors = [m for m in messages if "Error" in m or "is not a function" in m]
        assert not errors, errors
        print(f"{checks} Qt wheel-zoom checks passed (time series and XY, both/X/Y, in/out)")
    finally:
        qInstallMessageHandler(previous)


if __name__ == "__main__":
    main()
