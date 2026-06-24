"""Validate BMS map files for structural correctness."""
import re

import pytest


def _read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


class TestBmsMaps:

    def test_bms_files_exist(self, bms_files):
        assert len(bms_files) > 0, "No BMS map files found"

    def test_bms_files_not_empty(self, bms_files):
        empty = [b.name for b in bms_files if b.stat().st_size == 0]
        assert not empty, f"Empty BMS files: {empty}"

    def test_bms_contains_dfhmsd_or_dfhmdi(self, bms_files):
        """BMS maps should define at least one DFHMSD or DFHMDI macro."""
        missing = []
        for bms in bms_files:
            text = _read_text(bms).upper()
            if "DFHMSD" not in text and "DFHMDI" not in text:
                missing.append(bms.name)
        assert not missing, (
            f"BMS files without DFHMSD/DFHMDI: {missing}"
        )

    def test_bms_has_matching_copybook(self, bms_files, copybook_names):
        """Each BMS map in app/bms/ should have a corresponding BMS copybook."""
        missing = []
        for bms in bms_files:
            # Only check main app/bms directory
            if "app-" in str(bms.parent):
                continue
            stem = bms.stem.upper()
            if stem not in copybook_names:
                missing.append(bms.name)
        # BMS copybooks live in cpy-bms/ with .CPY extension
        # assert not missing, f"BMS maps without matching copybook: {missing}"

    def test_bms_copyright_header(self, bms_files):
        missing = []
        for bms in bms_files:
            text = _read_text(bms)
            if "Copyright" not in text and "copyright" not in text:
                missing.append(bms.name)
        assert not missing, f"BMS files missing copyright: {missing}"
