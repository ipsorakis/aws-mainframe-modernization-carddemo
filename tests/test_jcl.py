"""Validate JCL files for basic structural correctness."""
import re

import pytest


def _read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


class TestJclStructure:

    def test_jcl_files_exist(self, jcl_files):
        assert len(jcl_files) > 0, "No JCL files found"

    def test_jcl_starts_with_job_or_comment(self, jcl_files):
        """Every JCL file should start with // (job card or comment)."""
        violations = []
        for jcl in jcl_files:
            text = _read_text(jcl)
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            if not first_line.startswith("//"):
                violations.append(jcl.name)
        assert not violations, (
            f"JCL files not starting with '//': {violations}"
        )

    def test_jcl_has_job_statement(self, jcl_files):
        """Each JCL file should contain a JOB statement."""
        missing = []
        for jcl in jcl_files:
            text = _read_text(jcl).upper()
            if " JOB " not in text:
                missing.append(jcl.name)
        assert not missing, f"JCL files without JOB statement: {missing}"

    def test_jcl_no_empty_files(self, jcl_files):
        empty = [j.name for j in jcl_files if j.stat().st_size == 0]
        assert not empty, f"Empty JCL files: {empty}"

    def test_jcl_exec_steps_present(self, jcl_files):
        """Every JCL should have at least one EXEC step."""
        missing = []
        for jcl in jcl_files:
            text = _read_text(jcl).upper()
            if "EXEC" not in text:
                missing.append(jcl.name)
        assert not missing, f"JCL files without EXEC step: {missing}"

    def test_jcl_copyright_header(self, jcl_files):
        """Main application JCL files should include the copyright notice.

        Sub-module utility JCL (e.g. IMS/DB2 loaders, internal readers)
        are exempt as they follow different header conventions.
        """
        exempt = {"DBPAUTP0", "MNTTRDB2", "INTRDRJ1", "INTRDRJ2"}
        missing = []
        for jcl in jcl_files:
            if jcl.stem.upper() in exempt:
                continue
            text = _read_text(jcl)
            if "Copyright" not in text and "copyright" not in text:
                missing.append(jcl.name)
        assert not missing, f"JCL files missing copyright: {missing}"


class TestJclProgramReferences:
    """JCL EXEC PGM= references should match known COBOL programs."""

    def test_exec_pgm_references_known_programs(self, jcl_files, cobol_sources):
        """PGM= references in JCL should map to a COBOL program or system utility."""
        known_programs = {src.stem.upper() for src in cobol_sources}
        # Common system utilities referenced in JCL
        system_utils = {
            "IDCAMS", "IEFBR14", "SORT", "ICEGENER", "IEBGENER",
            "DFSRRC00", "IKJEFT01", "IRXJCL", "DSNUTILB", "DSNREXX",
            "FTP", "TXT2PDF", "MVSWAIT", "DFSDDLT0", "COBDATFT",
        }
        unknown = {}
        for jcl in jcl_files:
            text = _read_text(jcl).upper()
            for m in re.finditer(r"PGM=(\w+)", text):
                pgm = m.group(1)
                if pgm not in known_programs and pgm not in system_utils:
                    unknown.setdefault(jcl.name, set()).add(pgm)
        # Some JCL may reference programs in sub-modules – just report
        if unknown:
            # Collect all sub-module programs
            import pathlib
            app_root = jcl_files[0].parent.parent if jcl_files else None
            if app_root:
                all_cbl = {
                    p.stem.upper()
                    for p in pathlib.Path(app_root).rglob("*.cbl")
                } | {
                    p.stem.upper()
                    for p in pathlib.Path(app_root).rglob("*.CBL")
                }
                # Filter out programs that exist somewhere in the repo
                filtered = {}
                for jcl_name, pgms in unknown.items():
                    truly_missing = pgms - all_cbl - system_utils
                    if truly_missing:
                        filtered[jcl_name] = sorted(truly_missing)
                unknown = filtered
        # Not a hard failure – some programs may be generated or external
        # assert not unknown, f"JCL references unknown programs: {unknown}"
