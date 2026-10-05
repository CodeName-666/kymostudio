# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Window Management Module - Floating window state management."""

from .window_state import WindowState
from .window_manager import FloatingWindowManager

__all__ = [
    "WindowState",
    "FloatingWindowManager",
]
