from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest


_original_database_path = os.environ.get("MMG_DATABASE_PATH")
_temporary_database_directory = tempfile.TemporaryDirectory(prefix="mini-maltego-pytest-")
os.environ["MMG_DATABASE_PATH"] = str(
    Path(_temporary_database_directory.name) / "app-import.sqlite3"
)


def pytest_unconfigure(config: pytest.Config) -> None:
    try:
        application_module = sys.modules.get("app.api.main")
        if application_module is not None:
            application_module.app.state.engine.dispose()
    finally:
        if _original_database_path is None:
            os.environ.pop("MMG_DATABASE_PATH", None)
        else:
            os.environ["MMG_DATABASE_PATH"] = _original_database_path
        _temporary_database_directory.cleanup()
