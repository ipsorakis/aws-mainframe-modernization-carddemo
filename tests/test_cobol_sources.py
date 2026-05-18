"""Tests for COBOL source program structure and integrity."""
import pathlib
import re

import pytest

from helpers import (
    parse_cobol_copy_statements,
    parse_cobol_paragraphs,
    parse_cobol_program_id,
)

# Online CICS programs and their expected PROGRAM-IDs
ONLINE_PROGRAMS = {
    "COSGN00C.cbl": "COSGN00C",
    "COMEN01C.cbl": "COMEN01C",
    "COACTVWC.cbl": "COACTVWC",
    "COACTUPC.cbl": "COACTUPC",
    "COCRDLIC.cbl": "COCRDLIC",
    "COCRDSLC.cbl": "COCRDSLC",
    "COCRDUPC.cbl": "COCRDUPC",
    "COTRN00C.cbl": "COTRN00C",
    "COTRN01C.cbl": "COTRN01C",
    "COTRN02C.cbl": "COTRN02C",
    "CORPT00C.cbl": "CORPT00C",
    "COBIL00C.cbl": "COBIL00C",
    "COADM01C.cbl": "COADM01C",
    "COUSR00C.cbl": "COUSR00C",
    "COUSR01C.cbl": "COUSR01C",
    "COUSR02C.cbl": "COUSR02C",
    "COUSR03C.cbl": "COUSR03C",
}

# Batch programs
BATCH_PROGRAMS = {
    "CBACT01C.cbl": "CBACT01C",
    "CBACT02C.cbl": "CBACT02C",
    "CBACT03C.cbl": "CBACT03C",
    "CBACT04C.cbl": "CBACT04C",
    "CBCUS01C.cbl": "CBCUS01C",
    "CBTRN01C.cbl": "CBTRN01C",
    "CBTRN02C.cbl": "CBTRN02C",
    "CBTRN03C.cbl": "CBTRN03C",
    "CBSTM03A.CBL": "CBSTM03A",
    "CBSTM03B.CBL": "CBSTM03B",
}

ALL_PROGRAMS = {**ONLINE_PROGRAMS, **BATCH_PROGRAMS}


class TestProgramExistence:
    """Verify all expected COBOL programs exist."""

    @pytest.mark.parametrize("filename", list(ALL_PROGRAMS.keys()))
    def test_program_exists(self, cbl_dir, filename):
        assert (cbl_dir / filename).exists(), f"Missing program: {filename}"

    def test_total_program_count(self, cbl_dir):
        cbl_files = list(cbl_dir.glob("*.cbl")) + list(cbl_dir.glob("*.CBL"))
        assert len(cbl_files) >= len(ALL_PROGRAMS), (
            f"Expected at least {len(ALL_PROGRAMS)} programs, "
            f"found {len(cbl_files)}"
        )


class TestProgramIdentification:
    """Verify PROGRAM-ID matches filename convention."""

    @pytest.mark.parametrize(
        "filename,expected_id",
        list(ALL_PROGRAMS.items()),
        ids=list(ALL_PROGRAMS.keys()),
    )
    def test_program_id_matches(self, cbl_dir, filename, expected_id):
        filepath = cbl_dir / filename
        program_id = parse_cobol_program_id(filepath)
        assert program_id.upper() == expected_id.upper(), (
            f"{filename}: PROGRAM-ID '{program_id}' != expected '{expected_id}'"
        )


class TestProgramDivisions:
    """Verify required COBOL divisions are present."""

    REQUIRED_DIVISIONS = [
        "IDENTIFICATION DIVISION",
        "DATA DIVISION",
        "PROCEDURE DIVISION",
    ]

    @pytest.mark.parametrize("filename", list(ALL_PROGRAMS.keys()))
    def test_has_required_divisions(self, cbl_dir, filename):
        filepath = cbl_dir / filename
        text = filepath.read_text().upper()
        for div in self.REQUIRED_DIVISIONS:
            assert div in text, f"{filename}: missing {div}"

    @pytest.mark.parametrize("filename", list(ONLINE_PROGRAMS.keys()))
    def test_online_has_linkage_section(self, cbl_dir, filename):
        """Online CICS programs should have a LINKAGE SECTION for COMMAREA."""
        filepath = cbl_dir / filename
        text = filepath.read_text().upper()
        assert "LINKAGE SECTION" in text, (
            f"{filename}: online program missing LINKAGE SECTION"
        )


class TestCopyStatements:
    """Verify COPY references resolve to existing copybooks."""

    # Copybooks provided by CICS (not in our repo)
    CICS_COPYBOOKS = {"DFHAID", "DFHBMSCA", "DFHATTR"}

    @pytest.mark.parametrize("filename", list(ALL_PROGRAMS.keys()))
    def test_copy_references_valid(self, cbl_dir, cpy_dir, filename):
        filepath = cbl_dir / filename
        copies = parse_cobol_copy_statements(filepath)
        for copybook in copies:
            if copybook.upper() in self.CICS_COPYBOOKS:
                continue
            # Check if copybook exists with .cpy or .CPY extension
            found = (
                (cpy_dir / f"{copybook}.cpy").exists()
                or (cpy_dir / f"{copybook}.CPY").exists()
            )
            # Also check cpy-bms directory for BMS-generated copybooks
            cpy_bms = cbl_dir.parent / "cpy-bms"
            if not found and cpy_bms.exists():
                found = (
                    (cpy_bms / f"{copybook}.cpy").exists()
                    or (cpy_bms / f"{copybook}.CPY").exists()
                )
            # BMS maps generate copybooks with map names
            bms_dir = cbl_dir.parent / "bms"
            if not found and bms_dir.exists():
                bms_names = {
                    f.stem.upper() for f in bms_dir.iterdir()
                }
                if copybook.upper() in bms_names:
                    found = True
            assert found, (
                f"{filename}: COPY {copybook} not found in cpy/ or cpy-bms/"
            )

    def test_online_programs_copy_commarea(self, cbl_dir):
        """Online programs should COPY the COMMAREA definition."""
        for filename in ONLINE_PROGRAMS:
            filepath = cbl_dir / filename
            copies = parse_cobol_copy_statements(filepath)
            assert "COCOM01Y" in copies, (
                f"{filename}: online program doesn't COPY COCOM01Y (COMMAREA)"
            )


class TestProgramStructure:
    """Verify structural elements of COBOL programs."""

    @pytest.mark.parametrize("filename", list(ALL_PROGRAMS.keys()))
    def test_has_at_least_one_paragraph(self, cbl_dir, filename):
        filepath = cbl_dir / filename
        paragraphs = parse_cobol_paragraphs(filepath)
        assert len(paragraphs) >= 1, (
            f"{filename}: no paragraphs found in PROCEDURE DIVISION"
        )

    @pytest.mark.parametrize("filename", list(ONLINE_PROGRAMS.keys()))
    def test_online_has_cics_commands(self, cbl_dir, filename):
        """Online programs should contain EXEC CICS commands."""
        filepath = cbl_dir / filename
        text = filepath.read_text().upper()
        assert "EXEC CICS" in text, (
            f"{filename}: online program has no EXEC CICS commands"
        )

    @pytest.mark.parametrize("filename", list(BATCH_PROGRAMS.keys()))
    def test_batch_has_file_operations(self, cbl_dir, filename):
        """Batch programs should have file I/O (OPEN/READ/WRITE/CLOSE)."""
        filepath = cbl_dir / filename
        text = filepath.read_text().upper()
        file_ops = any(
            op in text for op in ["OPEN INPUT", "OPEN OUTPUT", "OPEN I-O",
                                   "READ ", "WRITE ", "CLOSE "]
        )
        assert file_ops, (
            f"{filename}: batch program has no file I/O operations"
        )

    def test_signon_program_validates_credentials(self, cbl_dir):
        """COSGN00C should contain user/password validation logic."""
        filepath = cbl_dir / "COSGN00C.cbl"
        text = filepath.read_text()
        assert "SEC-USR-PWD" in text, "Sign-on program missing password check"
        assert "WS-USER-ID" in text, "Sign-on program missing user ID handling"

    def test_batch_posting_validates_transactions(self, cbl_dir):
        """CBTRN02C should contain transaction validation logic."""
        filepath = cbl_dir / "CBTRN02C.cbl"
        text = filepath.read_text().upper()
        assert "VALIDATE" in text, "Posting program missing validation"
        assert "REJECT" in text, "Posting program missing reject handling"


class TestCodingStandards:
    """Verify coding standards across COBOL sources."""

    # Programs written by AWS team have AUTHOR clause
    PROGRAMS_WITH_AUTHOR = [
        f for f in list(ALL_PROGRAMS.keys())
        if f in ONLINE_PROGRAMS or f.startswith("CB") and f not in (
            "CBSTM03A.CBL", "CBSTM03B.CBL",
            "COACTVWC.cbl", "COACTUPC.cbl",
            "COCRDLIC.cbl", "COCRDSLC.cbl", "COCRDUPC.cbl",
        )
    ]

    @pytest.mark.parametrize("filename", list(ALL_PROGRAMS.keys()))
    def test_has_license_header(self, cbl_dir, filename):
        filepath = cbl_dir / filename
        text = filepath.read_text()
        assert "Apache License" in text or "Copyright" in text, (
            f"{filename}: missing license header"
        )
