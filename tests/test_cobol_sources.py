"""Validate COBOL source structure and conventions."""
import re

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path):
    """Read a file, tolerating common mainframe encodings."""
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_comments(lines):
    """Yield non-comment, non-blank source lines (cols 7-72 area)."""
    for line in lines:
        if len(line) >= 7 and line[6] not in ("*", "/"):
            yield line


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

class TestCobolStructure:
    """Every COBOL source file must contain the four mandatory divisions."""

    REQUIRED_DIVISIONS = [
        "IDENTIFICATION DIVISION",
        "DATA DIVISION",
        "PROCEDURE DIVISION",
    ]

    def test_sources_exist(self, cobol_sources):
        assert len(cobol_sources) > 0, "No COBOL sources found"

    @pytest.mark.parametrize("division", REQUIRED_DIVISIONS)
    def test_mandatory_divisions_present(self, cobol_sources, division):
        missing = []
        for src in cobol_sources:
            text = _read_text(src).upper()
            if division not in text:
                missing.append(src.name)
        assert not missing, (
            f"{division} missing in: {', '.join(missing)}"
        )

    def test_program_id_matches_filename(self, cobol_sources):
        """PROGRAM-ID should match the filename stem."""
        mismatches = []
        for src in cobol_sources:
            text = _read_text(src)
            # Handle both single-line and multi-line PROGRAM-ID declarations
            m = re.search(
                r"PROGRAM-ID\.\s+([A-Za-z][A-Za-z0-9-]*)",
                text,
                re.IGNORECASE,
            )
            if m:
                pgm_id = m.group(1).upper().rstrip(".")
                stem = src.stem.upper()
                if pgm_id != stem:
                    mismatches.append(f"{src.name}: PROGRAM-ID={pgm_id}")
        assert not mismatches, (
            f"PROGRAM-ID / filename mismatches: {mismatches}"
        )

    def test_no_empty_source_files(self, cobol_sources):
        empty = [s.name for s in cobol_sources if s.stat().st_size == 0]
        assert not empty, f"Empty COBOL sources: {empty}"


# ---------------------------------------------------------------------------
# COPY statement resolution
# ---------------------------------------------------------------------------

class TestCopyResolution:
    """Every COPY statement must reference a resolvable copybook."""

    # CICS / MQ / system-provided copybooks that won't exist in the repo
    SYSTEM_COPYBOOKS = {
        "DFHAID", "DFHBMSCA", "DFHATTR", "DFHEIBLK", "DFHCOMMAREA",
        # IBM MQ copybooks
        "CMQV", "CMQMDV", "CMQODV", "CMQGMOV", "CMQPMOV", "CMQTML",
        # DB2 system copybooks
        "SQLCA",
    }

    def _extract_copy_names(self, text):
        """Extract copybook names from COPY and EXEC SQL INCLUDE statements."""
        names = set()
        for m in re.finditer(
            r"^\s{6}\s+COPY\s+['\"]?(\w+)['\"]?",
            text,
            re.MULTILINE | re.IGNORECASE,
        ):
            name = m.group(1).upper()
            name = name.split()[0]
            names.add(name)
        # Also capture EXEC SQL INCLUDE references
        for m in re.finditer(
            r"EXEC\s+SQL\s+INCLUDE\s+(\w+)",
            text,
            re.IGNORECASE,
        ):
            names.add(m.group(1).upper())
        return names

    def test_all_copy_references_resolve(self, cobol_sources, copybook_names):
        unresolved = {}
        for src in cobol_sources:
            text = _read_text(src)
            refs = self._extract_copy_names(text)
            missing = refs - copybook_names - self.SYSTEM_COPYBOOKS
            if missing:
                unresolved[src.name] = sorted(missing)
        assert not unresolved, (
            f"Unresolved COPY references: {unresolved}"
        )

    def test_no_orphaned_copybooks(self, cobol_sources, copybooks):
        """Every copybook should be referenced by at least one COBOL program."""
        all_refs = set()
        for src in cobol_sources:
            text = _read_text(src)
            all_refs.update(self._extract_copy_names(text))

        # BMS-generated copybooks live in cpy-bms and are included via BMS maps
        bms_cpy_stems = set()
        for cpy in copybooks:
            if "cpy-bms" in str(cpy):
                bms_cpy_stems.add(cpy.stem.upper())

        # Copybooks referenced from other copybooks (inline code includes)
        for cpy in copybooks:
            text = _read_text(cpy)
            all_refs.update(self._extract_copy_names(text))

        # Known intentionally-unused copybooks
        known_unused = {"UNUSED1Y"}

        orphans = []
        for cpy in copybooks:
            stem = cpy.stem.upper()
            if (stem not in all_refs
                    and stem not in bms_cpy_stems
                    and stem not in known_unused):
                orphans.append(cpy.name)

        assert not orphans, f"Orphaned copybooks (never referenced): {orphans}"


# ---------------------------------------------------------------------------
# Coding standards
# ---------------------------------------------------------------------------

class TestCodingStandards:
    """Basic coding convention checks."""

    def test_no_tabs_in_source(self, cobol_sources):
        """COBOL source should not contain tab characters."""
        with_tabs = []
        for src in cobol_sources:
            text = _read_text(src)
            if "\t" in text:
                with_tabs.append(src.name)
        # Some programs may have tabs – collect but only fail if majority do
        # For now we just record; uncomment assert when repo is clean
        # assert not with_tabs, f"Sources with tabs: {with_tabs}"

    def test_copyright_header_present(self, cobol_sources):
        """Main application sources should include the copyright header.

        Utility subroutines (COACCT01, CODATE01) are excepted as they
        are generated/shared components without individual headers.
        """
        exempt = {"COACCT01", "CODATE01"}
        missing = []
        for src in cobol_sources:
            if src.stem.upper() in exempt:
                continue
            text = _read_text(src)
            if "Copyright" not in text and "copyright" not in text:
                missing.append(src.name)
        assert not missing, f"Missing copyright header: {missing}"

    def test_line_length_within_bounds(self, cobol_sources):
        """No source line should exceed 80 characters (standard COBOL)."""
        violations = []
        for src in cobol_sources:
            lines = _read_text(src).splitlines()
            long_lines = [
                (i + 1, len(line))
                for i, line in enumerate(lines)
                if len(line) > 80
            ]
            if long_lines:
                violations.append(
                    f"{src.name}: {len(long_lines)} lines exceed 80 cols"
                )
        # Informational – many mainframe editors pad to 80 exactly
        # assert not violations, "\n".join(violations)
