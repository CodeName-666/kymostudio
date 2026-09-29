"""Keep tests out of the real user profile; Qt stays an optional test dependency."""
import os
import tempfile
from pathlib import Path
import pytest

@pytest.fixture(scope="session", autouse=True)
def isolated_user_configuration():
    with tempfile.TemporaryDirectory(prefix="plotter-tests-") as directory:
        original = os.environ.get("PLOTTER_CONFIG_HOME")
        os.environ["PLOTTER_CONFIG_HOME"] = directory
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        yield Path(directory)
        if original is None:
            os.environ.pop("PLOTTER_CONFIG_HOME", None)
        else:
            os.environ["PLOTTER_CONFIG_HOME"] = original
