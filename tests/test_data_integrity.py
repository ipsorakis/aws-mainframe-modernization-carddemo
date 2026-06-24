"""Validate ASCII data files for referential integrity and format correctness."""
import re

import pytest


def _read_lines(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


# ---------------------------------------------------------------------------
# Account data (acctdata.txt) – CVACT01Y layout (300 bytes)
# Positions: ACCT-ID 9(11) | ACTIVE-STATUS X(1) | ...
# ---------------------------------------------------------------------------

class TestAccountData:

    def test_account_ids_are_unique(self, ascii_data_dir):
        path = ascii_data_dir / "acctdata.txt"
        lines = _read_lines(path)
        ids = [line[:11] for line in lines]
        assert len(ids) == len(set(ids)), "Duplicate account IDs found"

    def test_account_ids_are_numeric(self, ascii_data_dir):
        path = ascii_data_dir / "acctdata.txt"
        lines = _read_lines(path)
        non_numeric = [
            (i + 1, line[:11])
            for i, line in enumerate(lines)
            if not line[:11].isdigit()
        ]
        assert not non_numeric, f"Non-numeric account IDs: {non_numeric[:5]}"

    def test_active_status_valid(self, ascii_data_dir):
        path = ascii_data_dir / "acctdata.txt"
        lines = _read_lines(path)
        invalid = [
            (i + 1, line[11])
            for i, line in enumerate(lines)
            if line[11] not in ("Y", "N")
        ]
        assert not invalid, f"Invalid active status values: {invalid[:5]}"

    def test_account_dates_format(self, ascii_data_dir):
        """Open / expiration / reissue dates should be YYYY-MM-DD."""
        path = ascii_data_dir / "acctdata.txt"
        lines = _read_lines(path)
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        # Positions based on copybook: open=36..45, expiry=46..55, reissue=56..65
        # After accounting for signed numerics:
        # ACCT-ID(11) + STATUS(1) + CURR-BAL(12) + CREDIT-LIMIT(12) + CASH-LIMIT(12) = 48
        # open_date starts at byte 48
        bad = []
        for i, line in enumerate(lines):
            open_dt = line[48:58]
            exp_dt = line[58:68]
            reis_dt = line[68:78]
            for dt_name, dt_val in [
                ("open", open_dt),
                ("expiry", exp_dt),
                ("reissue", reis_dt),
            ]:
                if not date_pattern.match(dt_val):
                    bad.append((i + 1, dt_name, dt_val))
        assert not bad, f"Invalid date formats: {bad[:5]}"


# ---------------------------------------------------------------------------
# Customer data (custdata.txt) – CUSTREC layout (500 bytes)
# ---------------------------------------------------------------------------

class TestCustomerData:

    def test_customer_ids_are_unique(self, ascii_data_dir):
        path = ascii_data_dir / "custdata.txt"
        lines = _read_lines(path)
        ids = [line[:9] for line in lines]
        assert len(ids) == len(set(ids)), "Duplicate customer IDs found"

    def test_customer_ids_are_numeric(self, ascii_data_dir):
        path = ascii_data_dir / "custdata.txt"
        lines = _read_lines(path)
        non_numeric = [
            (i + 1, line[:9])
            for i, line in enumerate(lines)
            if not line[:9].isdigit()
        ]
        assert not non_numeric, f"Non-numeric customer IDs: {non_numeric[:5]}"

    def test_state_codes_not_empty(self, ascii_data_dir):
        """State code field (2 chars) should not be all spaces."""
        path = ascii_data_dir / "custdata.txt"
        lines = _read_lines(path)
        # CUST-ID(9) + FIRST(25) + MIDDLE(25) + LAST(25) + ADDR1(50) + ADDR2(50) + ADDR3(50) = 234
        # STATE-CD at byte 234, length 2
        blank_states = [
            i + 1 for i, line in enumerate(lines) if line[234:236].strip() == ""
        ]
        assert not blank_states, (
            f"Customers with blank state codes at lines: {blank_states[:5]}"
        )


# ---------------------------------------------------------------------------
# Card cross-reference (cardxref.txt)
# Format: CARD-NUM(16) + ACCT-ID(11) + CUST-ID(9) = 36 bytes
# ---------------------------------------------------------------------------

class TestCardXref:
    """Validate card cross-reference file (CVACT03Y layout).

    Layout: XREF-CARD-NUM X(16) | XREF-CUST-ID 9(09) | XREF-ACCT-ID 9(11)
    """

    def _parse_xref(self, ascii_data_dir):
        path = ascii_data_dir / "cardxref.txt"
        lines = _read_lines(path)
        records = []
        for line in lines:
            card_num = line[:16]
            cust_id = line[16:25]
            acct_id = line[25:36]
            records.append((card_num, acct_id, cust_id))
        return records

    def test_card_numbers_are_unique(self, ascii_data_dir):
        records = self._parse_xref(ascii_data_dir)
        card_nums = [r[0] for r in records]
        assert len(card_nums) == len(set(card_nums)), "Duplicate card numbers"

    def test_xref_account_ids_exist(self, ascii_data_dir):
        """Every account ID in the xref should exist in acctdata."""
        acct_path = ascii_data_dir / "acctdata.txt"
        acct_ids = {line[:11] for line in _read_lines(acct_path)}
        records = self._parse_xref(ascii_data_dir)
        missing = [
            r[1] for r in records if r[1] not in acct_ids
        ]
        assert not missing, (
            f"XREF references non-existent account IDs: {sorted(set(missing))}"
        )

    def test_xref_customer_ids_exist(self, ascii_data_dir):
        """Every customer ID in the xref should exist in custdata."""
        cust_path = ascii_data_dir / "custdata.txt"
        cust_ids = {line[:9] for line in _read_lines(cust_path)}
        records = self._parse_xref(ascii_data_dir)
        missing = [
            r[2] for r in records if r[2] not in cust_ids
        ]
        assert not missing, (
            f"XREF references non-existent customer IDs: {sorted(set(missing))}"
        )


# ---------------------------------------------------------------------------
# Card data (carddata.txt) – 150 bytes
# CARD-NUM(16) + ... + CARD-ACTIVE-STATUS X(1)
# ---------------------------------------------------------------------------

class TestCardData:

    def test_card_numbers_are_unique(self, ascii_data_dir):
        path = ascii_data_dir / "carddata.txt"
        lines = _read_lines(path)
        card_nums = [line[:16] for line in lines]
        assert len(card_nums) == len(set(card_nums)), "Duplicate card numbers"

    def test_card_numbers_are_numeric(self, ascii_data_dir):
        path = ascii_data_dir / "carddata.txt"
        lines = _read_lines(path)
        non_numeric = [
            (i + 1, line[:16])
            for i, line in enumerate(lines)
            if not line[:16].isdigit()
        ]
        assert not non_numeric, (
            f"Non-numeric card numbers: {non_numeric[:5]}"
        )

    def test_card_data_and_xref_match(self, ascii_data_dir):
        """Every card in carddata should appear in cardxref and vice-versa."""
        card_path = ascii_data_dir / "carddata.txt"
        xref_path = ascii_data_dir / "cardxref.txt"
        card_nums = {line[:16] for line in _read_lines(card_path)}
        xref_nums = {line[:16] for line in _read_lines(xref_path)}
        only_card = card_nums - xref_nums
        only_xref = xref_nums - card_nums
        assert not only_card, (
            f"Cards in carddata but not xref: {sorted(only_card)}"
        )
        assert not only_xref, (
            f"Cards in xref but not carddata: {sorted(only_xref)}"
        )


# ---------------------------------------------------------------------------
# Transaction type / category reference data
# ---------------------------------------------------------------------------

class TestTransactionReferenceData:

    def test_trantype_not_empty(self, ascii_data_dir):
        path = ascii_data_dir / "trantype.txt"
        lines = _read_lines(path)
        assert len(lines) > 0, "trantype.txt is empty"

    def test_trancatg_not_empty(self, ascii_data_dir):
        path = ascii_data_dir / "trancatg.txt"
        lines = _read_lines(path)
        assert len(lines) > 0, "trancatg.txt is empty"

    def test_trantype_codes_are_numeric(self, ascii_data_dir):
        """First 2 characters of each trantype record should be numeric."""
        path = ascii_data_dir / "trantype.txt"
        lines = _read_lines(path)
        bad = [
            (i + 1, line[:2])
            for i, line in enumerate(lines)
            if not line[:2].isdigit()
        ]
        assert not bad, f"Non-numeric transaction type codes: {bad}"

    def test_trancatg_type_codes_exist(self, ascii_data_dir):
        """Transaction category type codes should reference valid trantypes."""
        type_path = ascii_data_dir / "trantype.txt"
        catg_path = ascii_data_dir / "trancatg.txt"
        type_codes = {line[:2] for line in _read_lines(type_path)}
        catg_lines = _read_lines(catg_path)
        bad = [
            (i + 1, line[:2])
            for i, line in enumerate(catg_lines)
            if line[:2] not in type_codes
        ]
        assert not bad, (
            f"Transaction categories reference unknown types: {bad[:5]}"
        )


# ---------------------------------------------------------------------------
# Daily transactions (dailytran.txt) – CVTRA05Y layout (350 bytes)
# ---------------------------------------------------------------------------

class TestDailyTransactions:

    def test_transaction_count(self, ascii_data_dir):
        path = ascii_data_dir / "dailytran.txt"
        lines = _read_lines(path)
        assert len(lines) > 0, "dailytran.txt is empty"

    def test_transaction_ids_are_numeric(self, ascii_data_dir):
        """First 16 chars (TRAN-ID) should be numeric."""
        path = ascii_data_dir / "dailytran.txt"
        lines = _read_lines(path)
        bad = [
            (i + 1, line[:16])
            for i, line in enumerate(lines)
            if not line[:16].isdigit()
        ]
        assert not bad, f"Non-numeric transaction IDs: {bad[:5]}"

    def test_transaction_card_nums_exist(self, ascii_data_dir):
        """Card numbers in transactions should exist in carddata."""
        tran_path = ascii_data_dir / "dailytran.txt"
        card_path = ascii_data_dir / "carddata.txt"
        card_nums = {line[:16] for line in _read_lines(card_path)}
        tran_lines = _read_lines(tran_path)
        # TRAN-CARD-NUM starts at position 198 (after TRAN-ID(16)+TYPE(2)+CAT(4)+SRC(10)+DESC(100)+AMT(11)+MERCH-ID(9)+MERCH-NAME(50)--> but let's compute)
        # TRAN-ID(16) + TYPE-CD(2) + CAT-CD(4) + SOURCE(10) + DESC(100) + AMT(11) + MERCHANT-ID(9) + MERCHANT-NAME(50) + MERCHANT-CITY(50) + MERCHANT-ZIP(10) = 262
        # TRAN-CARD-NUM at byte 262, length 16
        missing_cards = set()
        for line in tran_lines:
            tran_card = line[262:278]
            if tran_card.strip() and tran_card not in card_nums:
                missing_cards.add(tran_card)
        assert not missing_cards, (
            f"Transactions reference non-existent cards: {sorted(missing_cards)[:5]}"
        )
