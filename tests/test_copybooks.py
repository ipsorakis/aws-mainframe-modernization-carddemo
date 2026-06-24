"""Validate copybook structure and record definitions."""
import re

import pytest


def _read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


class TestCopybookStructure:
    """Copybooks must define valid COBOL data structures."""

    def test_copybooks_exist(self, copybooks):
        assert len(copybooks) > 0, "No copybooks found"

    def test_no_empty_copybooks(self, copybooks):
        empty = [c.name for c in copybooks if c.stat().st_size == 0]
        assert not empty, f"Empty copybooks: {empty}"

    def test_copybooks_contain_data_definitions(self, copybooks):
        """Each copybook should define at least one data item or SQL/procedure code."""
        no_data = []
        for cpy in copybooks:
            text = _read_text(cpy)
            has_data = re.search(r"\b(01|05|10|15|88)\b", text)
            has_sql = "EXEC SQL" in text.upper()
            has_procedure = "PERFORM" in text.upper() or "CALL" in text.upper()
            if not (has_data or has_sql or has_procedure):
                no_data.append(cpy.name)
        assert not no_data, (
            f"Copybooks with no data definitions: {no_data}"
        )

    def test_no_procedure_division_in_copybooks(self, copybooks):
        """Copybooks should not contain PROCEDURE DIVISION.

        Inline-code copybooks (CSUTLDPY, etc.) that are designed to be
        COPYed into the PROCEDURE DIVISION are exempt.
        """
        inline_code_copybooks = {"CSUTLDPY"}
        violations = []
        for cpy in copybooks:
            if cpy.stem.upper() in inline_code_copybooks:
                continue
            text = _read_text(cpy).upper()
            if "PROCEDURE DIVISION" in text:
                violations.append(cpy.name)
        assert not violations, (
            f"Copybooks with PROCEDURE DIVISION: {violations}"
        )


class TestRecordLengths:
    """Validate that key copybook record lengths match data files."""

    # Expected record lengths from copybook comments / PIC clauses
    EXPECTED_RECORD_LENGTHS = {
        "CVACT01Y": 300,  # ACCOUNT-RECORD (RECLN 300)
        "CUSTREC": 500,   # CUSTOMER-RECORD (RECLN 500)
        "CVTRA05Y": 350,  # TRAN-RECORD (RECLN = 350)
    }

    # Corresponding ASCII data files (line length = record length + newline)
    DATA_FILE_LENGTHS = {
        "acctdata.txt": 300,
        "custdata.txt": 500,
        "dailytran.txt": 350,
    }

    @pytest.mark.parametrize(
        "filename,expected_len",
        DATA_FILE_LENGTHS.items(),
        ids=DATA_FILE_LENGTHS.keys(),
    )
    def test_data_file_record_length(self, ascii_data_dir, filename, expected_len):
        """Each line in the ASCII data file should match the copybook record length."""
        data_file = ascii_data_dir / filename
        if not data_file.exists():
            pytest.skip(f"{filename} not found")
        lines = data_file.read_text().splitlines()
        assert len(lines) > 0, f"{filename} is empty"
        bad_lines = [
            (i + 1, len(line))
            for i, line in enumerate(lines)
            if len(line) != expected_len
        ]
        assert not bad_lines, (
            f"{filename}: {len(bad_lines)} lines have wrong length "
            f"(expected {expected_len}). First few: {bad_lines[:5]}"
        )

    def test_consistent_record_lengths_per_file(self, ascii_data_dir):
        """Within each data file, all records should have the same length."""
        for data_file in sorted(ascii_data_dir.glob("*.txt")):
            lines = data_file.read_text().splitlines()
            if not lines:
                continue
            lengths = {len(line) for line in lines}
            assert len(lengths) == 1, (
                f"{data_file.name}: inconsistent record lengths {lengths}"
            )
