# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
"""Keep tests out of the real user profile; Qt stays an optional test dependency."""
import os
import tempfile
from pathlib import Path
import pytest

@pytest.fixture(scope="session", autouse=True)
def isolated_user_configuration():
    with tempfile.TemporaryDirectory(prefix="kymo-tests-") as directory:
        original = os.environ.get("KYMO_CONFIG_HOME")
        os.environ["KYMO_CONFIG_HOME"] = directory
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        yield Path(directory)
        if original is None:
            os.environ.pop("KYMO_CONFIG_HOME", None)
        else:
            os.environ["KYMO_CONFIG_HOME"] = original
