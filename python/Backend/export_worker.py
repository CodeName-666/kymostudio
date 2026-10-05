# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""CSV disk work runs off the GUI thread over an immutable sample snapshot."""
from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from Core.samples import export_csv


class CsvExportWorker(QThread):
    completed = Signal(str, int)
    failed = Signal(str)

    def __init__(self, path: Path, rows: list, names: dict, parent=None) -> None:
        super().__init__(parent)
        self.path, self.rows, self.names = path, rows, names

    def run(self) -> None:
        try:
            count = export_csv(self.path, self.rows, self.names)
            self.completed.emit(str(self.path), count)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.rows = []
