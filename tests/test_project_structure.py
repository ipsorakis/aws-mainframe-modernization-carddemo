"""Validate the overall project structure and completeness."""
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"


class TestProjectStructure:
    """Verify expected directories and key files exist."""

    EXPECTED_DIRS = [
        "app/cbl",
        "app/cpy",
        "app/cpy-bms",
        "app/jcl",
        "app/bms",
        "app/data/ASCII",
        "app/data/EBCDIC",
        "app/csd",
        "app/proc",
        "scripts",
    ]

    EXPECTED_FILES = [
        "README.md",
        "app/csd/CARDDEMO.CSD",
    ]

    @pytest.mark.parametrize("rel_dir", EXPECTED_DIRS)
    def test_expected_directory_exists(self, rel_dir):
        assert (ROOT / rel_dir).is_dir(), f"Directory missing: {rel_dir}"

    @pytest.mark.parametrize("rel_file", EXPECTED_FILES)
    def test_expected_file_exists(self, rel_file):
        assert (ROOT / rel_file).is_file(), f"File missing: {rel_file}"

    def test_no_stray_files_in_root(self):
        """Root should only have expected config files, not source code."""
        allowed_extensions = {
            ".md", ".txt", ".yml", ".yaml", ".json", ".toml", ".ini",
            ".cfg", ".gitignore", ".gitattributes", ".editorconfig",
            "",  # files without extensions (e.g. Makefile, LICENSE)
        }
        stray = []
        for item in ROOT.iterdir():
            if item.is_file() and item.suffix not in allowed_extensions:
                stray.append(item.name)
        assert not stray, f"Unexpected files in project root: {stray}"


class TestAssetCounts:
    """Sanity-check that the asset counts haven't dropped unexpectedly."""

    def test_minimum_cobol_programs(self):
        count = len(list(APP.rglob("*.cbl"))) + len(list(APP.rglob("*.CBL")))
        assert count >= 29, f"Expected ≥29 COBOL programs, found {count}"

    def test_minimum_copybooks(self):
        count = len(list(APP.rglob("*.cpy"))) + len(list(APP.rglob("*.CPY")))
        assert count >= 29, f"Expected ≥29 copybooks, found {count}"

    def test_minimum_jcl_files(self):
        count = len(list(APP.rglob("*.jcl"))) + len(list(APP.rglob("*.JCL")))
        assert count >= 30, f"Expected ≥30 JCL files, found {count}"

    def test_minimum_bms_maps(self):
        count = len(list(APP.rglob("*.bms")))
        assert count >= 17, f"Expected ≥17 BMS maps, found {count}"

    def test_minimum_data_files(self):
        ascii_dir = APP / "data" / "ASCII"
        count = len(list(ascii_dir.glob("*.txt")))
        assert count >= 9, f"Expected ≥9 ASCII data files, found {count}"


class TestCsdDefinitions:
    """Validate CICS System Definition file references."""

    def test_csd_defines_programs(self):
        csd = ROOT / "app" / "csd" / "CARDDEMO.CSD"
        if not csd.exists():
            pytest.skip("CSD file not found")
        text = csd.read_text(encoding="utf-8", errors="replace").upper()
        assert "DEFINE" in text or "PROGRAM" in text, (
            "CSD file does not contain program definitions"
        )

    def test_csd_defines_transactions(self):
        csd = ROOT / "app" / "csd" / "CARDDEMO.CSD"
        if not csd.exists():
            pytest.skip("CSD file not found")
        text = csd.read_text(encoding="utf-8", errors="replace").upper()
        assert "TRANSACTION" in text, (
            "CSD file does not contain transaction definitions"
        )
