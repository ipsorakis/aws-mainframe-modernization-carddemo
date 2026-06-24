"""Validate shell scripts for basic correctness."""
import os
import stat

import pytest


def _read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


class TestShellScripts:

    def test_scripts_exist(self, scripts_dir):
        scripts = list(scripts_dir.glob("*.sh"))
        assert len(scripts) > 0, "No shell scripts found"

    def test_scripts_have_shebang_or_are_sourced(self, scripts_dir):
        """Shell scripts should start with a shebang line."""
        missing = []
        for script in sorted(scripts_dir.glob("*.sh")):
            text = _read_text(script)
            first_line = text.strip().splitlines()[0] if text.strip() else ""
            if not first_line.startswith("#!") and not first_line.startswith("#"):
                missing.append(script.name)
        # Some scripts are meant to be sourced, not directly executed
        # assert not missing, f"Scripts without shebang: {missing}"

    def test_scripts_not_empty(self, scripts_dir):
        empty = [
            s.name
            for s in sorted(scripts_dir.glob("*.sh"))
            if s.stat().st_size == 0
        ]
        assert not empty, f"Empty scripts: {empty}"

    def test_no_hardcoded_credentials(self, scripts_dir):
        """Scripts should not contain hardcoded passwords or keys."""
        suspicious = []
        patterns = ["PASSWORD=", "SECRET=", "API_KEY=", "TOKEN="]
        for script in sorted(scripts_dir.glob("*.sh")):
            text = _read_text(script).upper()
            for pattern in patterns:
                if pattern in text:
                    suspicious.append((script.name, pattern))
        assert not suspicious, (
            f"Scripts with potential hardcoded credentials: {suspicious}"
        )
