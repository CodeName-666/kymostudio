"""PlotterApp entry point, independent of the current working directory."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QEvent, QCoreApplication, QMetaObject, QSettings, QTimer, Qt, qInstallMessageHandler
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMessageBox

from Backend.backend import Backend
from Backend.Windows.window_manager_bridge import WindowManagerBridge
from Core.configuration import ConfigurationRepository
from Core.paths import PROJECT_ROOT, user_config_path, user_data_dir
from Logger.logger import Logger
from Plotter.plotter import Plotter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='PlotterApp — live measurement workbench')
    parser.add_argument('--config', type=Path, help='Explicit writable user configuration')
    parser.add_argument('--demo', action='store_true', help='Open a synthetic three-signal example')
    parser.add_argument('--smoke-test', action='store_true', help='Isolated Qt/QML launch + acquisition check')
    options = parser.parse_args(argv)
    QCoreApplication.setOrganizationName('PlotterApp')
    QCoreApplication.setApplicationName('PlotterApp')
    QCoreApplication.setApplicationVersion('2.0.0-modernized')
    QQuickStyle.setStyle('Fusion')
    app = QApplication.instance() or QApplication([sys.argv[0]])
    temporary = TemporaryDirectory(prefix='plotter-smoke-') if options.smoke_test else None
    config_path = Path(temporary.name) / 'config.json' if temporary else (options.config or user_config_path())
    if temporary:
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, temporary.name)
    with (PROJECT_ROOT / 'config/config.json').open(encoding='utf-8-sig') as stream:
        defaults = json.load(stream)
    try:
        config = ConfigurationRepository(config_path, defaults).load()
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        message = f'Konfiguration nicht geladen: {config_path}\n\n{exc}\n\nDie Datei wurde nicht verändert.'
        print(message, file=sys.stderr)
        if not options.smoke_test:
            QMessageBox.critical(None, 'PlotterApp — Konfigurationsfehler', message)
        if temporary:
            temporary.cleanup()
        return 2
    log_dir = Path(temporary.name) if temporary else user_data_dir()
    log_config = dict(config.get('logging', {}))
    log_config['name'] = str(log_dir / 'logs' / 'plotter.log')
    Logger.get_instance().config(log_config)
    plotter = Plotter([sys.argv[0]], config)
    backend = Backend(config_path)
    backend.config(config)
    plotter.set_backend(backend)
    plotter.set_window_manager(WindowManagerBridge())
    errors: list[str] = []
    previous_handler = None
    if options.smoke_test:
        def capture(kind, context, message):
            print(message, file=sys.stderr)
            if any(term in message for term in ('Error:', 'is not defined', 'Cannot assign',
                'Cannot read property', 'is not a function', 'Binding loop', 'Unable to assign', 'failed to load')):
                errors.append(message)
        previous_handler = qInstallMessageHandler(capture)
    plotter.load_app()
    if not plotter.rootObjects():
        backend.shutdown()
        plotter.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        if options.smoke_test:
            qInstallMessageHandler(previous_handler)
        if temporary:
            logging.shutdown()
            temporary.cleanup()
        return 3
    root = plotter.rootObjects()[0]
    if options.demo or options.smoke_test:
        QTimer.singleShot(100, lambda: QMetaObject.invokeMethod(root, 'startDemo', Qt.QueuedConnection))
    if options.smoke_test:
        def finish_smoke():
            data = backend.get_diagnostics()
            okay = data['received'] >= 3 and not errors
            print(json.dumps({'qt_smoke': 'passed' if okay else 'failed', 'diagnostics': data,
                              'qml_errors': errors}, indent=2))
            if not backend.shutdown():
                okay = False
            app.exit(0 if okay else 4)
        QTimer.singleShot(1600, finish_smoke)
    result = plotter.run()
    backend.shutdown()
    plotter.engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    if options.smoke_test:
        qInstallMessageHandler(previous_handler)
    if temporary:
        logging.shutdown()
        temporary.cleanup()
    return result


if __name__ == '__main__':
    raise SystemExit(main())
