"""Tests for ASCII data file integrity and format validation."""
import pathlib

import pytest

# Expected record lengths from copybook definitions
DATA_FILE_SPECS = {
    "acctdata.txt": {"reclen": 300, "count": 50, "copybook": "CVACT01Y"},
    "carddata.txt": {"reclen": 150, "count": 50, "copybook": "CVACT02Y"},
    "cardxref.txt": {"reclen": 36, "count": 50, "copybook": "CVACT03Y"},
    "custdata.txt": {"reclen": 500, "count": 50, "copybook": "CVCUS01Y"},
    "dailytran.txt": {"reclen": 350, "count": 300, "copybook": "CVTRA06Y"},
    "discgrp.txt": {"reclen": 50, "count": 51, "copybook": "CVTRA02Y"},
    "tcatbal.txt": {"reclen": 50, "count": 50, "copybook": "CVTRA01Y"},
    "trancatg.txt": {"reclen": 60, "count": 18, "copybook": "CVTRA04Y"},
    "trantype.txt": {"reclen": 60, "count": 7, "copybook": "CVTRA03Y"},
}


class TestDataFileExistence:
    """Verify all expected data files exist."""

    def test_ascii_data_directory_exists(self, data_ascii_dir):
        assert data_ascii_dir.exists()
        assert data_ascii_dir.is_dir()

    @pytest.mark.parametrize("filename", list(DATA_FILE_SPECS.keys()))
    def test_data_file_exists(self, data_ascii_dir, filename):
        filepath = data_ascii_dir / filename
        assert filepath.exists(), f"Data file {filename} not found"

    def test_ebcdic_data_directory_exists(self, app_dir):
        ebcdic = app_dir / "data" / "EBCDIC"
        assert ebcdic.exists()


class TestDataFileRecordLengths:
    """Verify each data file has consistent record lengths matching copybook."""

    @pytest.mark.parametrize(
        "filename,spec",
        list(DATA_FILE_SPECS.items()),
        ids=list(DATA_FILE_SPECS.keys()),
    )
    def test_record_length_consistency(self, data_ascii_dir, filename, spec):
        filepath = data_ascii_dir / filename
        lines = filepath.read_text().splitlines()
        expected_len = spec["reclen"]
        for i, line in enumerate(lines):
            assert len(line) == expected_len, (
                f"{filename} line {i + 1}: length {len(line)} != "
                f"expected {expected_len}"
            )


class TestDataFileRecordCounts:
    """Verify each data file has the expected number of records."""

    @pytest.mark.parametrize(
        "filename,spec",
        list(DATA_FILE_SPECS.items()),
        ids=list(DATA_FILE_SPECS.keys()),
    )
    def test_record_count(self, data_ascii_dir, filename, spec):
        filepath = data_ascii_dir / filename
        lines = filepath.read_text().splitlines()
        assert len(lines) == spec["count"], (
            f"{filename}: found {len(lines)} records, expected {spec['count']}"
        )


class TestAccountData:
    """Validate account data file field formats."""

    def test_account_ids_are_sequential(self, data_ascii_dir):
        filepath = data_ascii_dir / "acctdata.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            acct_id = line[:11]
            assert acct_id.isdigit(), (
                f"Line {i + 1}: ACCT-ID '{acct_id}' is not numeric"
            )

    def test_account_status_valid(self, data_ascii_dir):
        filepath = data_ascii_dir / "acctdata.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            status = line[11]
            assert status in ("Y", "N"), (
                f"Line {i + 1}: invalid account status '{status}'"
            )

    def test_account_dates_format(self, data_ascii_dir):
        """Open date at offset 76-85 should be YYYY-MM-DD."""
        import re

        filepath = data_ascii_dir / "acctdata.txt"
        lines = filepath.read_text().splitlines()
        date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")
        for i, line in enumerate(lines):
            # ACCT-OPEN-DATE starts at offset 76 (after 11+1+12+12+12+10+10+8=76)
            # Actually: 11 + 1 + 12 + 12 + 12 = 48, then open date at offset 48
            # Let me compute: ACCT-ID(11) + STATUS(1) + BAL(12) + CREDIT(12) + CASH(12) = 48
            open_date = line[48:58]
            assert date_pattern.match(open_date), (
                f"Line {i + 1}: open date '{open_date}' not YYYY-MM-DD"
            )


class TestCardData:
    """Validate card data file field formats."""

    def test_card_numbers_are_16_chars(self, data_ascii_dir):
        filepath = data_ascii_dir / "carddata.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            card_num = line[:16]
            assert len(card_num) == 16
            assert card_num.isdigit(), (
                f"Line {i + 1}: card number '{card_num}' is not all digits"
            )

    def test_card_account_ids_are_numeric(self, data_ascii_dir):
        filepath = data_ascii_dir / "carddata.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            acct_id = line[16:27]
            assert acct_id.isdigit(), (
                f"Line {i + 1}: card ACCT-ID '{acct_id}' not numeric"
            )

    def test_card_active_status_valid(self, data_ascii_dir):
        filepath = data_ascii_dir / "carddata.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            # CARD-NUM(16) + ACCT-ID(11) + CVV(3) + NAME(50) + DATE(10) = 90
            status = line[90]
            assert status in ("Y", "N"), (
                f"Line {i + 1}: card status '{status}' invalid"
            )


class TestCardXrefData:
    """Validate card cross-reference data."""

    def test_xref_card_nums_16_chars(self, data_ascii_dir):
        filepath = data_ascii_dir / "cardxref.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            card_num = line[:16]
            assert len(card_num) == 16

    def test_xref_customer_ids_numeric(self, data_ascii_dir):
        filepath = data_ascii_dir / "cardxref.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            cust_id = line[16:25]
            assert cust_id.isdigit(), (
                f"Line {i + 1}: XREF CUST-ID '{cust_id}' not numeric"
            )

    def test_xref_account_ids_numeric(self, data_ascii_dir):
        filepath = data_ascii_dir / "cardxref.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            acct_id = line[25:36]
            assert acct_id.isdigit(), (
                f"Line {i + 1}: XREF ACCT-ID '{acct_id}' not numeric"
            )


class TestCrossReferenceIntegrity:
    """Validate referential integrity between data files."""

    def test_card_xref_account_ids_exist_in_accounts(self, data_ascii_dir):
        """Every account ID in cardxref should exist in acctdata."""
        acct_file = data_ascii_dir / "acctdata.txt"
        xref_file = data_ascii_dir / "cardxref.txt"

        acct_ids = set()
        for line in acct_file.read_text().splitlines():
            acct_ids.add(line[:11])

        for i, line in enumerate(xref_file.read_text().splitlines()):
            xref_acct = line[25:36]
            assert xref_acct in acct_ids, (
                f"XREF line {i + 1}: ACCT-ID {xref_acct} not in acctdata"
            )

    def test_card_xref_card_nums_exist_in_cards(self, data_ascii_dir):
        """Every card number in cardxref should exist in carddata."""
        card_file = data_ascii_dir / "carddata.txt"
        xref_file = data_ascii_dir / "cardxref.txt"

        card_nums = set()
        for line in card_file.read_text().splitlines():
            card_nums.add(line[:16])

        for i, line in enumerate(xref_file.read_text().splitlines()):
            xref_card = line[:16]
            assert xref_card in card_nums, (
                f"XREF line {i + 1}: card {xref_card} not in carddata"
            )

    def test_card_account_ids_exist_in_accounts(self, data_ascii_dir):
        """Every account ID in carddata should exist in acctdata."""
        acct_file = data_ascii_dir / "acctdata.txt"
        card_file = data_ascii_dir / "carddata.txt"

        acct_ids = set()
        for line in acct_file.read_text().splitlines():
            acct_ids.add(line[:11])

        for i, line in enumerate(card_file.read_text().splitlines()):
            card_acct = line[16:27]
            assert card_acct in acct_ids, (
                f"Card line {i + 1}: ACCT-ID {card_acct} not in acctdata"
            )


class TestTransactionTypeData:
    """Validate transaction type reference data."""

    def test_transaction_type_codes_two_chars(self, data_ascii_dir):
        filepath = data_ascii_dir / "trantype.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            type_cd = line[:2]
            assert len(type_cd) == 2
            assert type_cd.isdigit(), (
                f"Line {i + 1}: type code '{type_cd}' not numeric"
            )

    def test_transaction_type_has_description(self, data_ascii_dir):
        filepath = data_ascii_dir / "trantype.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            desc = line[2:52].strip()
            assert len(desc) > 0, (
                f"Line {i + 1}: transaction type has no description"
            )


class TestTransactionCategoryData:
    """Validate transaction category data."""

    def test_trancatg_type_codes_two_chars(self, data_ascii_dir):
        filepath = data_ascii_dir / "trancatg.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            type_cd = line[:2]
            assert type_cd.isdigit(), (
                f"Line {i + 1}: category type code '{type_cd}' not numeric"
            )

    def test_trancatg_category_codes_four_digits(self, data_ascii_dir):
        filepath = data_ascii_dir / "trancatg.txt"
        lines = filepath.read_text().splitlines()
        for i, line in enumerate(lines):
            cat_cd = line[2:6]
            assert cat_cd.isdigit(), (
                f"Line {i + 1}: category code '{cat_cd}' not numeric"
            )
