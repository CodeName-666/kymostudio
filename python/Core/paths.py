# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Writable user data paths; project resources are always read-only defaults."""
from __future__ import annotations
import os
import sys
from pathlib import Path

# In a PyInstaller bundle all resources (qml, config, resources) live in sys._MEIPASS.
PROJECT_ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))


LEGACY_DIR_NAME = 'PlotterApp'  # name before the Kymotrace rename


def user_data_dir() -> Path:
    override = os.environ.get('KYMO_CONFIG_HOME') or os.environ.get('PLOTTER_CONFIG_HOME')
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', str(Path.home() / 'AppData/Roaming')))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library/Application Support'
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    current, legacy = base / 'KymoStudio', base / LEGACY_DIR_NAME
    if not current.exists() and legacy.is_dir():
        try:
            legacy.rename(current)  # one-time migration of existing user data
        except OSError:
            return legacy
    return current


def user_config_path() -> Path:
    return user_data_dir() / 'config.json'
