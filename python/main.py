# This Python file uses the following encoding: utf-8
import os
import sys
import json

from os.path import abspath, dirname, join

from PySide6.QtQml import QQmlDebuggingEnabler
from PySide6.QtCore import QSettings, QCoreApplication
from PySide6.QtQuickControls2 import QQuickStyle

from Plotter.plotter import Plotter
from Backend.backend import Backend
from Logger.logger import Logger
from Backend.Windows.window_manager_bridge import WindowManagerBridge


# from style_rc import *

def getJsonConfigData(json_path: str):
    file_path = os.path.dirname(__file__)
    if file_path:
        config = file_path + '/' + json_path
    else:
        config = json_path
    try:
        with open(config) as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        return None


def getInterface(json_config: dict, type: str):
    if json_config:
        interface_list = json_config["interfaces"]
        for interface in interface_list:
            if interface["type"] == type:
                return interface
        return None


def getSerialConfig(json_config: dict):
    return getInterface(json_config, "Serial")


def getTelnetConfig(json_config: dict):
    return getInterface(json_config, "Telnet")


if __name__ == "__main__":

    QCoreApplication.setOrganizationName("PlotterApp")
    QCoreApplication.setOrganizationDomain("plotter.app")
    QCoreApplication.setApplicationName("PlotterApp")

    settings = QSettings()
    controls_style = settings.value("ui/controlsStyle", "Fusion")
    if not controls_style:
        controls_style = "Fusion"
    os.environ["QT_QUICK_CONTROLS_STYLE"] = controls_style
    QQuickStyle.setStyle(controls_style)

    qt_controls_conf = abspath(join(dirname(__file__), "../qml/qtquickcontrols2.conf"))
    if os.path.exists(qt_controls_conf):
        os.environ["QT_QUICK_CONTROLS_CONF"] = qt_controls_conf
    else:
        print(f"Warning: qtquickcontrols2.conf not found at {qt_controls_conf}", file=sys.stderr)

    QQmlDebuggingEnabler()

    json_config = getJsonConfigData('../config/config.json')

    Logger.get_instance().config(json_config["logging"])

    Logger.get_instance().log_info('=========================================')
    Logger.get_instance().log_info('========== Logger Startup ===============')
    Logger.get_instance().log_info('=========================================')

    plotter = Plotter(sys.argv, json_config)
    backend = Backend()
    window_manager = WindowManagerBridge()

    backend.config(json_config)

    plotter.set_backend(backend)
    plotter.set_window_manager(window_manager)

    plotter.load_app()

    if not plotter.rootObjects():
        sys.exit(-1)

    sys.exit(plotter.run())
