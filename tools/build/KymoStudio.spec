# -*- mode: python ; coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""
PyInstaller spec for KymoStudio (onedir).

Run from the project root:
    pyinstaller tools/build/KymoStudio.spec --noconfirm
or via:
    bash tools/build/build.sh
"""
import os
from PyInstaller.utils.hooks import collect_submodules

# SPECPATH is set by PyInstaller and points to tools/build/.
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir, os.pardir))

# python-can loads its interfaces by name at runtime; static analysis misses them.
hiddenimports = collect_submodules("can.interfaces")

# Core/paths.py resolves all resources relative to sys._MEIPASS in the bundle.
datas = [
    (os.path.join(PROJECT_ROOT, "qml"), "qml"),
    (os.path.join(PROJECT_ROOT, "config", "config.json"), "config"),
    (os.path.join(PROJECT_ROOT, "resources", "icons"), os.path.join("resources", "icons")),
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, "run.py")],
    pathex=[os.path.join(PROJECT_ROOT, "python")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # onedir: binaries are bundled by COLLECT
    name="KymoStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               # UPX off: avoids antivirus false positives
    console=False,           # GUI app without a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, "resources", "icons", "kymotrace.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="KymoStudio",       # output folder: build/dist/KymoStudio/
)
