"""Shared fixtures for CardDemo test suite."""
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"


@pytest.fixture
def root_dir():
    return ROOT


@pytest.fixture
def app_dir():
    return APP


@pytest.fixture
def cbl_dir():
    return APP / "cbl"


@pytest.fixture
def cpy_dir():
    return APP / "cpy"


@pytest.fixture
def jcl_dir():
    return APP / "jcl"


@pytest.fixture
def bms_dir():
    return APP / "bms"


@pytest.fixture
def data_ascii_dir():
    return APP / "data" / "ASCII"


@pytest.fixture
def scripts_dir():
    return ROOT / "scripts"
