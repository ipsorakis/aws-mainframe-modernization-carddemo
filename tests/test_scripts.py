"""Tests for shell script structure and correctness."""
import os
import pathlib
import re
import stat

import pytest

EXPECTED_SCRIPTS = [
    "run_full_batch.sh",
    "run_posting.sh",
    "run_interest_calc.sh",
    "git-addSrcVersionInfo.sh",
    "remote_compile.sh",
    "remote_refresh.sh",
    "remote_submit.sh",
    "upld_module.sh",
]


class TestScriptExistence:
    """Verify all expected scripts exist."""

    @pytest.mark.parametrize("filename", EXPECTED_SCRIPTS)
    def test_script_exists(self, scripts_dir, filename):
        assert (scripts_dir / filename).exists(), f"Missing script: {filename}"

    def test_scripts_directory_not_empty(self, scripts_dir):
        scripts = [f for f in scripts_dir.iterdir() if f.suffix == ".sh"]
        assert len(scripts) >= 4


class TestScriptStructure:
    """Verify shell script structural elements."""

    @pytest.mark.parametrize("filename", EXPECTED_SCRIPTS)
    def test_has_shebang_or_is_shell(self, scripts_dir, filename):
        """Scripts should start with a shebang line."""
        filepath = scripts_dir / filename
        text = filepath.read_text()
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        assert first_line.startswith("#!") or "bin/bash" in text[:100], (
            f"{filename}: missing shebang line"
        )


class TestBatchRunScripts:
    """Verify batch run scripts reference the correct JCL files."""

    def test_full_batch_references_all_required_jcl(self, scripts_dir):
        filepath = scripts_dir / "run_full_batch.sh"
        text = filepath.read_text()
        required_jcl = [
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
        for jcl in required_jcl:
            assert jcl in text, (
                f"run_full_batch.sh missing reference to {jcl}"
            )

    def test_posting_script_references_required_jcl(self, scripts_dir):
        filepath = scripts_dir / "run_posting.sh"
        text = filepath.read_text()
        required_jcl = [
            "CLOSEFIL.jcl",
            "ACCTFILE.jcl",
            "POSTTRAN.jcl",
            "OPENFIL.jcl",
        ]
        for jcl in required_jcl:
            assert jcl in text, (
                f"run_posting.sh missing reference to {jcl}"
            )

    def test_interest_calc_references_required_jcl(self, scripts_dir):
        filepath = scripts_dir / "run_interest_calc.sh"
        text = filepath.read_text()
        required_jcl = [
            "CLOSEFIL.jcl",
            "INTCALC.jcl",
            "COMBTRAN.jcl",
            "OPENFIL.jcl",
        ]
        for jcl in required_jcl:
            assert jcl in text, (
                f"run_interest_calc.sh missing reference to {jcl}"
            )

    def test_batch_scripts_check_tunnel(self, scripts_dir):
        """Batch run scripts should check for FTP tunnel before executing."""
        for script_name in [
            "run_full_batch.sh",
            "run_posting.sh",
            "run_interest_calc.sh",
        ]:
            filepath = scripts_dir / script_name
            text = filepath.read_text()
            assert "2121" in text, (
                f"{script_name}: doesn't check for FTP tunnel on port 2121"
            )


class TestVersionInfoScript:
    """Verify the git version info script."""

    def test_supports_cobol_extensions(self, scripts_dir):
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "cbl" in text, "Version script doesn't handle .cbl files"
        assert "cpy" in text, "Version script doesn't handle .cpy files"

    def test_supports_jcl_extensions(self, scripts_dir):
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "jcl" in text, "Version script doesn't handle .jcl files"

    def test_supports_bms_extension(self, scripts_dir):
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "bms" in text, "Version script doesn't handle .bms files"

    def test_validates_input_parameter(self, scripts_dir):
        """Script should check for missing file_name parameter."""
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "-z" in text, "Script doesn't validate empty input parameter"

    def test_checks_file_exists(self, scripts_dir):
        """Script should verify the input file exists."""
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "! -f" in text, "Script doesn't check if input file exists"

    def test_sets_app_name_and_version(self, scripts_dir):
        filepath = scripts_dir / "git-addSrcVersionInfo.sh"
        text = filepath.read_text()
        assert "app_name=CardDemo" in text
        assert "app_version=" in text
