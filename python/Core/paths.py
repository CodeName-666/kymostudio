"""Writable user data paths; project resources are always read-only defaults."""
from __future__ import annotations
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    override = os.environ.get('PLOTTER_CONFIG_HOME')
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', str(Path.home() / 'AppData/Roaming')))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library/Application Support'
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    return base / 'PlotterApp'


def user_config_path() -> Path:
    return user_data_dir() / 'config.json'
