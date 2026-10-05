# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Run with: python run.py [--demo] [--config path/to/config.json]."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
try:
    from main import main
except ModuleNotFoundError as exc:
    print(f'Fehlendes Paket: {exc.name}\nAbhängigkeiten installieren: python -m pip install -r requirements.txt', file=sys.stderr)
    raise SystemExit(1) from None

if __name__ == '__main__':
    raise SystemExit(main())
