"""Own application/engine lifetime and explicit QML context dependencies."""
import os
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication, QOffscreenSurface, QOpenGLContext
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication

from Core.paths import PROJECT_ROOT
from Backend.series_bridge import SeriesBridge


def _opengl_usable() -> bool:
    """Whether a real OpenGL context can be made current (not over RDP/VM without GL)."""
    if QGuiApplication.platformName() in ("offscreen", "minimal"):
        return False
    context = QOpenGLContext()
    if not context.create():
        return False
    surface = QOffscreenSurface()
    surface.setFormat(context.format())
    surface.create()
    usable = surface.isValid() and context.makeCurrent(surface)
    if usable:
        context.doneCurrent()
    return usable


def prefer_opengl_scene_graph() -> bool:
    """Render Qt Quick through OpenGL when available.

    Qt Charts only accelerates line/scatter series (``useOpenGL``) on an OpenGL
    scene graph; otherwise every frame repaints all points with QPainter on the
    GUI thread. An explicit QSG_RHI_BACKEND / QT_QUICK_BACKEND choice wins.
    """
    if os.environ.get("QSG_RHI_BACKEND") or os.environ.get("QT_QUICK_BACKEND"):
        return False
    if not _opengl_usable():
        return False
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGL)
    return True


class Plotter(QObject):
    def __init__(self, args: list[str], config: dict) -> None:
        app = QApplication.instance() or QApplication(args)
        super().__init__()
        self.app = app
        prefer_opengl_scene_graph()
        self.engine = QQmlApplicationEngine()
        # Import resources only from the delivered application, not arbitrary
        # paths contained in an imported user configuration.
        for path in ('qml', 'qml/imports', 'qml/content'):
            self.engine.addImportPath(str(PROJECT_ROOT / path))
        self._backend = None
        self._window_manager = None
        self._series_bridge = SeriesBridge(self)
        self.engine.rootContext().setContextProperty('SeriesBridge', self._series_bridge)

    def set_backend(self, backend) -> None:
        self._backend = backend
        self.engine.rootContext().setContextProperty('Backend', backend)

    def set_window_manager(self, window_manager) -> None:
        self._window_manager = window_manager
        self.engine.rootContext().setContextProperty('WindowManager', window_manager)

    def load_app(self) -> None:
        self.engine.load(str(PROJECT_ROOT / 'qml/main.qml'))

    def run(self) -> int:
        return self.app.exec()

    def rootObjects(self) -> list:
        return self.engine.rootObjects()

    def setImportPaths(self, path_list: list) -> None:
        """Compatibility API; resolve imports against the application root."""
        for path in path_list:
            self.engine.addImportPath(str((Path(__file__).parent / path).resolve()))
