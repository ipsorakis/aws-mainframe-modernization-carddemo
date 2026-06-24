"""Shared fixtures for CardDemo test suite."""
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"


@pytest.fixture(scope="session")
def app_root():
    return APP


@pytest.fixture(scope="session")
def cobol_sources(app_root):
    """Return all .cbl files under app/cbl and sub-app dirs."""
    return sorted(app_root.rglob("*.cbl")) + sorted(app_root.rglob("*.CBL"))


@pytest.fixture(scope="session")
def copybooks(app_root):
    """Return all .cpy files under app/cpy and sub-app dirs."""
    return sorted(app_root.rglob("*.cpy")) + sorted(app_root.rglob("*.CPY"))


@pytest.fixture(scope="session")
def dcl_files(app_root):
    """Return all .dcl files (DB2 DECLARE TABLE definitions)."""
    return sorted(app_root.rglob("*.dcl"))


@pytest.fixture(scope="session")
def copybook_names(copybooks, dcl_files):
    """Return set of copybook/DCL stems (upper-cased, without extension)."""
    names = {p.stem.upper() for p in copybooks}
    names.update(p.stem.upper() for p in dcl_files)
    return names


@pytest.fixture(scope="session")
def jcl_files(app_root):
    """Return all .jcl / .JCL files."""
    return sorted(app_root.rglob("*.jcl")) + sorted(app_root.rglob("*.JCL"))


@pytest.fixture(scope="session")
def bms_files(app_root):
    """Return all .bms files."""
    return sorted(app_root.rglob("*.bms"))


@pytest.fixture(scope="session")
def ascii_data_dir(app_root):
    return app_root / "data" / "ASCII"


@pytest.fixture(scope="session")
def scripts_dir():
    return ROOT / "scripts"
