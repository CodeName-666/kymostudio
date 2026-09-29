"""Own application/engine lifetime and explicit QML context dependencies."""
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from Core.paths import PROJECT_ROOT
from Backend.series_bridge import SeriesBridge


class Plotter(QObject):
    def __init__(self, args: list[str], config: dict) -> None:
        app = QApplication.instance() or QApplication(args)
        super().__init__()
        self.app = app
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
