"""Tests for JCL structure and reference validation."""
import pathlib
import re

import pytest

from helpers import parse_jcl_datasets, parse_jcl_programs

# JCL files and the programs they execute
JCL_PROGRAM_MAP = {
    "POSTTRAN.jcl": ["CBTRN02C"],
    "INTCALC.jcl": ["CBACT04C"],
    "CREASTMT.JCL": ["CBSTM03A"],
}

# JCL files that use IDCAMS or IEBGENER (utility programs)
JCL_UTILITY_FILES = [
    "ACCTFILE.jcl",
    "CARDFILE.jcl",
    "CUSTFILE.jcl",
    "XREFFILE.jcl",
    "DISCGRP.jcl",
    "TCATBALF.jcl",
    "TRANCATG.jcl",
    "TRANTYPE.jcl",
    "TRANFILE.jcl",
    "DEFGDGB.jcl",
    "DUSRSECJ.jcl",
]

EXPECTED_JCL_FILES = [
    "ACCTFILE.jcl",
    "CARDFILE.jcl",
    "CLOSEFIL.jcl",
    "COMBTRAN.jcl",
    "CUSTFILE.jcl",
    "DEFGDGB.jcl",
    "DISCGRP.jcl",
    "DUSRSECJ.jcl",
    "INTCALC.jcl",
    "OPENFIL.jcl",
    "POSTTRAN.jcl",
    "TCATBALF.jcl",
    "TRANBKP.jcl",
    "TRANCATG.jcl",
    "TRANFILE.jcl",
    "TRANIDX.jcl",
    "TRANTYPE.jcl",
    "XREFFILE.jcl",
]


class TestJCLExistence:
    """Verify all expected JCL files exist."""

    @pytest.mark.parametrize("filename", EXPECTED_JCL_FILES)
    def test_jcl_file_exists(self, jcl_dir, filename):
        assert (jcl_dir / filename).exists(), f"Missing JCL: {filename}"

    def test_jcl_directory_not_empty(self, jcl_dir):
        jcl_files = list(jcl_dir.glob("*.jcl")) + list(jcl_dir.glob("*.JCL"))
        assert len(jcl_files) >= len(EXPECTED_JCL_FILES)


class TestJCLStructure:
    """Verify JCL structural elements."""

    @pytest.mark.parametrize("filename", EXPECTED_JCL_FILES)
    def test_starts_with_job_card(self, jcl_dir, filename):
        """Every JCL file should begin with a JOB card."""
        filepath = jcl_dir / filename
        text = filepath.read_text()
        first_content_line = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("//*"):
                first_content_line = stripped
                break
        assert "JOB" in first_content_line.upper(), (
            f"{filename}: does not start with a JOB card"
        )

    @pytest.mark.parametrize("filename", EXPECTED_JCL_FILES)
    def test_has_license_header(self, jcl_dir, filename):
        filepath = jcl_dir / filename
        text = filepath.read_text()
        assert "Apache License" in text or "Copyright" in text, (
            f"{filename}: missing license header"
        )

    @pytest.mark.parametrize("filename", EXPECTED_JCL_FILES)
    def test_uses_standard_hlq(self, jcl_dir, filename):
        """JCL should reference datasets with the AWS.M2.CARDDEMO HLQ."""
        filepath = jcl_dir / filename
        datasets = parse_jcl_datasets(filepath)
        if datasets:
            aws_datasets = [
                d for d in datasets if "AWS.M2.CARDDEMO" in d.upper()
            ]
            assert len(aws_datasets) >= 1, (
                f"{filename}: no datasets use AWS.M2.CARDDEMO HLQ"
            )


class TestJCLProgramReferences:
    """Verify JCL EXEC PGM references point to valid programs."""

    @pytest.mark.parametrize(
        "jcl_file,expected_programs",
        list(JCL_PROGRAM_MAP.items()),
        ids=list(JCL_PROGRAM_MAP.keys()),
    )
    def test_exec_pgm_matches_expected(
        self, jcl_dir, jcl_file, expected_programs
    ):
        filepath = jcl_dir / jcl_file
        programs = parse_jcl_programs(filepath)
        for expected in expected_programs:
            assert expected in programs, (
                f"{jcl_file}: expected PGM={expected}, found {programs}"
            )

    @pytest.mark.parametrize("filename", JCL_UTILITY_FILES)
    def test_utility_jcl_uses_known_programs(self, jcl_dir, filename):
        """Utility JCL should use IDCAMS, IEBGENER, or similar system utils."""
        filepath = jcl_dir / filename
        programs = parse_jcl_programs(filepath)
        known_utils = {
            "IDCAMS", "IEBGENER", "IEFBR14", "SORT", "ICEGENER",
            "DSNTEP4", "DSNTIAUL", "SDSF",
        }
        for pgm in programs:
            assert pgm.upper() in known_utils or pgm.startswith("CB"), (
                f"{filename}: unknown program {pgm}"
            )


class TestJCLDatasetConsistency:
    """Verify dataset references are consistent across JCL."""

    def test_posttran_references_required_datasets(self, jcl_dir):
        """POSTTRAN job should reference all required data files."""
        filepath = jcl_dir / "POSTTRAN.jcl"
        text = filepath.read_text().upper()
        required = [
            "TRANSACT", "DALYTRAN", "CARDXREF",
            "ACCTDATA", "TCATBALF",
        ]
        for ds in required:
            assert ds in text, (
                f"POSTTRAN.jcl missing reference to {ds}"
            )

    def test_batch_sequence_coverage(self, jcl_dir):
        """Key batch jobs from the README sequence should exist."""
        batch_sequence = [
            "CLOSEFIL.jcl",
            "ACCTFILE.jcl",
            "CARDFILE.jcl",
            "XREFFILE.jcl",
            "CUSTFILE.jcl",
            "POSTTRAN.jcl",
            "INTCALC.jcl",
            "TRANBKP.jcl",
            "COMBTRAN.jcl",
            "OPENFIL.jcl",
        ]
        for jcl in batch_sequence:
            assert (jcl_dir / jcl).exists(), (
                f"Batch sequence JCL missing: {jcl}"
            )
