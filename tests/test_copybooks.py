"""Tests for COBOL copybook structure and integrity."""
import pathlib

import pytest

from helpers import (
    compute_record_length,
    get_declared_record_length,
    parse_copybook_fields,
)

# Copybooks that declare an explicit record length in their comment header
COPYBOOKS_WITH_RECLN = {
    "CVACT01Y.cpy": 300,
    "CVACT02Y.cpy": 150,
    "CVACT03Y.cpy": 50,
    "CVCUS01Y.cpy": 500,
    "CVTRA01Y.cpy": 50,
    "CVTRA02Y.cpy": 50,
    "CVTRA03Y.cpy": 60,
    "CVTRA04Y.cpy": 60,
    "CVTRA05Y.cpy": 350,
    "CVTRA06Y.cpy": 350,
}

# Every copybook must have a 01-level record definition
EXPECTED_01_RECORDS = {
    "CVACT01Y.cpy": "ACCOUNT-RECORD",
    "CVACT02Y.cpy": "CARD-RECORD",
    "CVACT03Y.cpy": "CARD-XREF-RECORD",
    "CSUSR01Y.cpy": "SEC-USER-DATA",
    "CVCUS01Y.cpy": "CUSTOMER-RECORD",
    "CVTRA01Y.cpy": "TRAN-CAT-BAL-RECORD",
    "CVTRA02Y.cpy": "DIS-GROUP-RECORD",
    "CVTRA03Y.cpy": "TRAN-TYPE-RECORD",
    "CVTRA04Y.cpy": "TRAN-CAT-RECORD",
    "CVTRA05Y.cpy": "TRAN-RECORD",
    "CVTRA06Y.cpy": "DALYTRAN-RECORD",
    "COCOM01Y.cpy": "CARDDEMO-COMMAREA",
}


class TestCopybookRecordLengths:
    """Verify that copybook field sizes sum to the declared record length."""

    @pytest.mark.parametrize(
        "filename,expected_len",
        list(COPYBOOKS_WITH_RECLN.items()),
        ids=list(COPYBOOKS_WITH_RECLN.keys()),
    )
    def test_record_length_matches_declaration(
        self, cpy_dir, filename, expected_len
    ):
        filepath = cpy_dir / filename
        assert filepath.exists(), f"Copybook {filename} not found"
        computed = compute_record_length(filepath)
        assert computed == expected_len, (
            f"{filename}: computed record length {computed} != "
            f"declared {expected_len}"
        )

    @pytest.mark.parametrize(
        "filename,expected_len",
        list(COPYBOOKS_WITH_RECLN.items()),
        ids=list(COPYBOOKS_WITH_RECLN.keys()),
    )
    def test_declared_recln_comment_present(
        self, cpy_dir, filename, expected_len
    ):
        filepath = cpy_dir / filename
        declared = get_declared_record_length(filepath)
        assert declared == expected_len, (
            f"{filename}: RECLN comment says {declared}, expected {expected_len}"
        )


class TestCopybookStructure:
    """Verify structural properties of copybooks."""

    @pytest.mark.parametrize(
        "filename,record_name",
        list(EXPECTED_01_RECORDS.items()),
        ids=list(EXPECTED_01_RECORDS.keys()),
    )
    def test_01_level_record_name(self, cpy_dir, filename, record_name):
        filepath = cpy_dir / filename
        fields = parse_copybook_fields(filepath)
        level_01 = [f for f in fields if f["level"] == 1]
        assert len(level_01) >= 1, f"{filename}: no 01-level record found"
        names = [f["name"] for f in level_01]
        assert record_name in names, (
            f"{filename}: expected 01-level '{record_name}', found {names}"
        )

    def test_all_copybooks_exist(self, cpy_dir):
        """All expected copybooks must be present in the cpy directory."""
        expected = set(COPYBOOKS_WITH_RECLN.keys()) | set(
            EXPECTED_01_RECORDS.keys()
        )
        for filename in expected:
            assert (cpy_dir / filename).exists(), f"Missing copybook: {filename}"

    def test_no_empty_copybooks(self, cpy_dir):
        """No copybook file should be empty."""
        for f in cpy_dir.iterdir():
            if f.suffix.lower() in (".cpy",):
                content = f.read_text().strip()
                assert len(content) > 0, f"Empty copybook: {f.name}"

    def test_copybooks_have_pic_clauses(self, cpy_dir):
        """Data copybooks should contain at least one PIC clause."""
        data_copybooks = [
            "CVACT01Y.cpy",
            "CVACT02Y.cpy",
            "CVACT03Y.cpy",
            "CSUSR01Y.cpy",
            "CVCUS01Y.cpy",
            "CVTRA05Y.cpy",
            "CVTRA06Y.cpy",
        ]
        for filename in data_copybooks:
            filepath = cpy_dir / filename
            fields = parse_copybook_fields(filepath)
            pic_fields = [f for f in fields if f["level"] > 1 and f["pic"]]
            assert len(pic_fields) >= 1, (
                f"{filename}: no PIC fields found"
            )

    def test_filler_fields_present_in_data_copybooks(self, cpy_dir):
        """Data copybooks with declared lengths should have FILLER to pad."""
        for filename in COPYBOOKS_WITH_RECLN:
            filepath = cpy_dir / filename
            fields = parse_copybook_fields(filepath)
            filler_fields = [f for f in fields if f["name"] == "FILLER"]
            assert len(filler_fields) >= 1, (
                f"{filename}: missing FILLER padding field"
            )


class TestCopybookFieldTypes:
    """Validate PIC clause patterns in copybooks."""

    def test_account_id_is_numeric(self, cpy_dir):
        filepath = cpy_dir / "CVACT01Y.cpy"
        fields = parse_copybook_fields(filepath)
        acct_id = next(f for f in fields if f["name"] == "ACCT-ID")
        assert "9" in acct_id["pic"], "ACCT-ID should be numeric PIC 9"
        assert acct_id["size"] == 11

    def test_card_num_is_alphanumeric(self, cpy_dir):
        filepath = cpy_dir / "CVACT02Y.cpy"
        fields = parse_copybook_fields(filepath)
        card_num = next(f for f in fields if f["name"] == "CARD-NUM")
        assert "X" in card_num["pic"], "CARD-NUM should be alphanumeric PIC X"
        assert card_num["size"] == 16

    def test_customer_ssn_is_9_digits(self, cpy_dir):
        filepath = cpy_dir / "CVCUS01Y.cpy"
        fields = parse_copybook_fields(filepath)
        ssn = next(f for f in fields if f["name"] == "CUST-SSN")
        assert ssn["size"] == 9

    def test_user_security_record_fields(self, cpy_dir):
        filepath = cpy_dir / "CSUSR01Y.cpy"
        fields = parse_copybook_fields(filepath)
        field_names = [f["name"] for f in fields]
        assert "SEC-USR-ID" in field_names
        assert "SEC-USR-PWD" in field_names
        assert "SEC-USR-TYPE" in field_names

    def test_transaction_record_has_amount(self, cpy_dir):
        filepath = cpy_dir / "CVTRA05Y.cpy"
        fields = parse_copybook_fields(filepath)
        tran_amt = next(f for f in fields if f["name"] == "TRAN-AMT")
        assert "S9" in tran_amt["pic"] or "S" in filepath.read_text()

    def test_commarea_has_user_type_field(self, cpy_dir):
        filepath = cpy_dir / "COCOM01Y.cpy"
        fields = parse_copybook_fields(filepath)
        field_names = [f["name"] for f in fields]
        assert "CDEMO-USER-TYPE" in field_names
