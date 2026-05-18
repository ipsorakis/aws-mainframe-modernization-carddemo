"""Tests for BMS map structure and consistency."""
import pathlib
import re

import pytest

from helpers import parse_bms_field_names, parse_bms_map_names, parse_bms_mapset_name

# BMS mapsets and the map(s) they contain
EXPECTED_MAPSETS = {
    "COSGN00.bms": {"mapset": "COSGN00", "maps": ["COSGN0A"]},
    "COMEN01.bms": {"mapset": "COMEN01", "maps": ["COMEN1A"]},
    "COACTVW.bms": {"mapset": "COACTVW", "maps": ["CACTVWA"]},
    "COACTUP.bms": {"mapset": "COACTUP", "maps": ["CACTUPA"]},
    "COCRDLI.bms": {"mapset": "COCRDLI", "maps": ["CCRDLIA"]},
    "COCRDSL.bms": {"mapset": "COCRDSL", "maps": ["CCRDSLA"]},
    "COCRDUP.bms": {"mapset": "COCRDUP", "maps": ["CCRDUPA"]},
    "COTRN00.bms": {"mapset": "COTRN00", "maps": ["COTRN0A"]},
    "COTRN01.bms": {"mapset": "COTRN01", "maps": ["COTRN1A"]},
    "COTRN02.bms": {"mapset": "COTRN02", "maps": ["COTRN2A"]},
    "CORPT00.bms": {"mapset": "CORPT00", "maps": ["CORPT0A"]},
    "COBIL00.bms": {"mapset": "COBIL00", "maps": ["COBIL0A"]},
    "COADM01.bms": {"mapset": "COADM01", "maps": ["COADM1A"]},
    "COUSR00.bms": {"mapset": "COUSR00", "maps": ["COUSR0A"]},
    "COUSR01.bms": {"mapset": "COUSR01", "maps": ["COUSR1A"]},
    "COUSR02.bms": {"mapset": "COUSR02", "maps": ["COUSR2A"]},
    "COUSR03.bms": {"mapset": "COUSR03", "maps": ["COUSR3A"]},
}


class TestBMSExistence:
    """Verify all expected BMS files exist."""

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_bms_file_exists(self, bms_dir, filename):
        assert (bms_dir / filename).exists(), f"Missing BMS: {filename}"

    def test_bms_directory_has_all_maps(self, bms_dir):
        bms_files = list(bms_dir.glob("*.bms"))
        assert len(bms_files) >= len(EXPECTED_MAPSETS)


class TestBMSStructure:
    """Verify BMS structural elements."""

    @pytest.mark.parametrize(
        "filename,spec",
        list(EXPECTED_MAPSETS.items()),
        ids=list(EXPECTED_MAPSETS.keys()),
    )
    def test_mapset_name_matches(self, bms_dir, filename, spec):
        filepath = bms_dir / filename
        mapset = parse_bms_mapset_name(filepath)
        assert mapset == spec["mapset"], (
            f"{filename}: mapset name '{mapset}' != expected '{spec['mapset']}'"
        )

    @pytest.mark.parametrize(
        "filename,spec",
        list(EXPECTED_MAPSETS.items()),
        ids=list(EXPECTED_MAPSETS.keys()),
    )
    def test_map_names_present(self, bms_dir, filename, spec):
        filepath = bms_dir / filename
        maps = parse_bms_map_names(filepath)
        for expected_map in spec["maps"]:
            assert expected_map in maps, (
                f"{filename}: map '{expected_map}' not found, have {maps}"
            )

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_has_dfhmsd_type_final(self, bms_dir, filename):
        """Every BMS source should end with DFHMSD TYPE=FINAL."""
        filepath = bms_dir / filename
        text = filepath.read_text().upper()
        assert "DFHMSD TYPE=FINAL" in text.replace(" ", "").replace(
            "=", "="
        ) or "TYPE=FINAL" in text, (
            f"{filename}: missing DFHMSD TYPE=FINAL"
        )

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_has_end_statement(self, bms_dir, filename):
        filepath = bms_dir / filename
        text = filepath.read_text()
        lines = [
            l.strip()
            for l in text.splitlines()
            if l.strip() and not l.strip().startswith("*")
        ]
        # The last meaningful line should be END or near it
        found_end = any("END" == l.strip() for l in lines[-5:])
        assert found_end, f"{filename}: missing END statement"


class TestBMSProperties:
    """Verify BMS map properties."""

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_uses_cobol_lang(self, bms_dir, filename):
        """All maps should specify LANG=COBOL."""
        filepath = bms_dir / filename
        text = filepath.read_text().upper()
        assert "LANG=COBOL" in text, f"{filename}: not set to LANG=COBOL"

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_uses_inout_mode(self, bms_dir, filename):
        """Maps should use MODE=INOUT for bidirectional I/O."""
        filepath = bms_dir / filename
        text = filepath.read_text().upper()
        assert "MODE=INOUT" in text, f"{filename}: not set to MODE=INOUT"

    def test_signon_has_userid_and_password_fields(self, bms_dir):
        """Login screen should have USERID and PASSWD fields."""
        filepath = bms_dir / "COSGN00.bms"
        fields = parse_bms_field_names(filepath)
        assert "USERID" in fields, "Login screen missing USERID field"
        assert "PASSWD" in fields, "Login screen missing PASSWD field"

    def test_signon_has_error_message_field(self, bms_dir):
        """Login screen should have an error message field."""
        filepath = bms_dir / "COSGN00.bms"
        fields = parse_bms_field_names(filepath)
        assert "ERRMSG" in fields, "Login screen missing ERRMSG field"

    @pytest.mark.parametrize("filename", list(EXPECTED_MAPSETS.keys()))
    def test_has_license_header(self, bms_dir, filename):
        filepath = bms_dir / filename
        text = filepath.read_text()
        assert "Apache License" in text or "Copyright" in text, (
            f"{filename}: missing license header"
        )


class TestBMSCOBOLConsistency:
    """Verify BMS maps have corresponding COBOL programs."""

    # Mapping of BMS mapset to COBOL program that uses it
    BMS_TO_COBOL = {
        "COSGN00.bms": "COSGN00C.cbl",
        "COMEN01.bms": "COMEN01C.cbl",
        "COACTVW.bms": "COACTVWC.cbl",
        "COACTUP.bms": "COACTUPC.cbl",
        "COCRDLI.bms": "COCRDLIC.cbl",
        "COCRDSL.bms": "COCRDSLC.cbl",
        "COCRDUP.bms": "COCRDUPC.cbl",
        "COTRN00.bms": "COTRN00C.cbl",
        "COTRN01.bms": "COTRN01C.cbl",
        "COTRN02.bms": "COTRN02C.cbl",
        "CORPT00.bms": "CORPT00C.cbl",
        "COBIL00.bms": "COBIL00C.cbl",
        "COADM01.bms": "COADM01C.cbl",
        "COUSR00.bms": "COUSR00C.cbl",
        "COUSR01.bms": "COUSR01C.cbl",
        "COUSR02.bms": "COUSR02C.cbl",
        "COUSR03.bms": "COUSR03C.cbl",
    }

    @pytest.mark.parametrize(
        "bms_file,cobol_file",
        list(BMS_TO_COBOL.items()),
        ids=list(BMS_TO_COBOL.keys()),
    )
    def test_cobol_program_exists_for_bms(self, bms_dir, cbl_dir, bms_file, cobol_file):
        assert (cbl_dir / cobol_file).exists(), (
            f"BMS {bms_file} has no corresponding COBOL program {cobol_file}"
        )

    @pytest.mark.parametrize(
        "bms_file,cobol_file",
        list(BMS_TO_COBOL.items()),
        ids=list(BMS_TO_COBOL.keys()),
    )
    def test_cobol_references_mapset(self, bms_dir, cbl_dir, bms_file, cobol_file):
        """COBOL program should reference its BMS mapset name."""
        mapset_name = EXPECTED_MAPSETS[bms_file]["mapset"]
        cobol_path = cbl_dir / cobol_file
        text = cobol_path.read_text().upper()
        # Check for COPY of the mapset or MAP/MAPSET reference
        assert mapset_name.upper() in text, (
            f"{cobol_file}: doesn't reference mapset {mapset_name}"
        )
