"""NFR-REL-001: helper failure MUST NOT block SDD step execution.

Spec: "Helper failure (disk full, malformed input, sink path not writable)
MUST NOT block SDD step execution. The helper MUST log the failure to
stderr and return success to its caller."
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Allow CLI module import
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.bin.sdd import c7_emit as c7_cli  # noqa: E402


class FailurePathTests(unittest.TestCase):
    """Helper failures must log to stderr and return exit code 0."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self._orig_cwd = Path.cwd()
        os.chdir(self.tmp)

    def tearDown(self) -> None:
        os.chdir(self._orig_cwd)
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sink_path_unwritable_returns_zero_and_logs_stderr(self) -> None:
        # Make artifacts/c7 a regular file so mkdir fails — disk-full proxy
        artifacts = self.tmp / "artifacts"
        artifacts.mkdir()
        (artifacts / "c7").write_text("blocker", encoding="utf-8")

        stderr = io.StringIO()
        with patch.object(sys, "stderr", stderr):
            rc = c7_cli.main([
                "emit", "--ticket", "347", "--phase", "intake",
                "--skill", "blueprint-sdd-step01-intake",
                "--owner-team", "platform-ops",
                "--slug", "test-slug",
            ])

        self.assertEqual(
            rc, 0,
            "NFR-REL-001 violation: helper must return success even on failure",
        )
        self.assertIn(
            "c7", stderr.getvalue().lower(),
            f"NFR-REL-001: helper must log failure to stderr; got: {stderr.getvalue()!r}",
        )

    def test_unexpected_exception_in_use_case_returns_zero(self) -> None:
        """Synthetic resolver failure must not propagate; CLI returns 0."""

        class _BoomResolver:
            def resolve(self):
                raise RuntimeError("synthetic resolver failure")

        stderr = io.StringIO()
        # Patch the CLI's local reference (imported by name at module load)
        with patch.object(sys, "stderr", stderr), \
             patch.object(c7_cli, "EnvVarModelResolver", _BoomResolver):
            rc = c7_cli.main([
                "emit", "--ticket", "347", "--phase", "intake",
                "--skill", "blueprint-sdd-step01-intake",
                "--owner-team", "platform-ops",
                "--slug", "test-slug-2",
            ])

        self.assertEqual(
            rc, 0,
            "NFR-REL-001: unhandled helper exception must not propagate",
        )


if __name__ == "__main__":
    unittest.main()
