"""Regression tests — stale extra_excluded_tokens warning (workaround removal migration).

When a consumer's blueprint/contract.yaml still lists tokens in
spec.upgrade.behavioral_check.extra_excluded_tokens that are now part of the
base _EXCLUDED_TOKENS set (e.g. 'uv', 'validate' added in the v1.10.0 fix),
run_behavioral_check must emit a per-token WARNING to stderr prompting removal.

Covered scenarios:
  A) Single stale token ('uv') — warning emitted; check still passes.
  B) Two stale tokens ('uv', 'validate') — both warned; check still passes.
  C) Non-stale custom token — no warning emitted.
  D) Mix of stale and non-stale tokens — only stale tokens warned.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.lib.blueprint.upgrade_shell_behavioral_check import (
    _EXCLUDED_TOKENS,
    run_behavioral_check,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class StaleExtraExcludedTokensWarningTests(unittest.TestCase):
    """Fixture A/B/C/D — stale token detection and warning in run_behavioral_check."""

    def _run_capture_stderr(
        self,
        extra: frozenset[str],
        script_content: str = "#!/usr/bin/env bash\necho hello\n",
    ) -> tuple[object, str]:
        """Run behavioral check with given extra tokens; return (result, stderr_text)."""
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            a = root / "a.sh"
            _write(a, script_content)
            old_stderr = sys.stderr
            sys.stderr = buf
            try:
                result = run_behavioral_check([a], root, extra_excluded_tokens=extra)
            finally:
                sys.stderr = old_stderr
        return result, buf.getvalue()

    def test_stale_uv_token_warns(self) -> None:
        """'uv' in extra_excluded_tokens must produce a WARNING mentioning 'uv'."""
        self.assertIn("uv", _EXCLUDED_TOKENS, "'uv' must be in base set for this test to be valid")
        _, stderr = self._run_capture_stderr(frozenset({"uv"}))
        self.assertIn(
            "'uv'",
            stderr,
            msg=f"Expected WARNING for stale token 'uv' in stderr. Got: {stderr!r}",
        )
        self.assertIn("WARNING", stderr)
        self.assertIn("extra_excluded_tokens", stderr)

    def test_stale_validate_token_warns(self) -> None:
        """'validate' in extra_excluded_tokens must produce a WARNING mentioning 'validate'."""
        self.assertIn("validate", _EXCLUDED_TOKENS, "'validate' must be in base set")
        _, stderr = self._run_capture_stderr(frozenset({"validate"}))
        self.assertIn("'validate'", stderr)
        self.assertIn("WARNING", stderr)

    def test_both_stale_tokens_both_warned(self) -> None:
        """Both 'uv' and 'validate' in extra_excluded_tokens must each produce a WARNING."""
        _, stderr = self._run_capture_stderr(frozenset({"uv", "validate"}))
        self.assertIn("'uv'", stderr)
        self.assertIn("'validate'", stderr)
        self.assertEqual(stderr.count("WARNING"), 2, msg=f"Expected 2 WARNINGs. Got: {stderr!r}")

    def test_non_stale_token_no_warning(self) -> None:
        """A token not in _EXCLUDED_TOKENS must not produce a WARNING."""
        custom = "my_consumer_helper_fn"
        self.assertNotIn(custom, _EXCLUDED_TOKENS)
        _, stderr = self._run_capture_stderr(frozenset({custom}))
        self.assertNotIn("WARNING", stderr, msg=f"No WARNING expected for non-stale token. Got: {stderr!r}")

    def test_mix_only_stale_warned(self) -> None:
        """Only stale tokens (already in base set) produce warnings; non-stale are silent."""
        custom = "my_consumer_fn"
        self.assertNotIn(custom, _EXCLUDED_TOKENS)
        _, stderr = self._run_capture_stderr(frozenset({"uv", custom}))
        self.assertIn("'uv'", stderr)
        self.assertNotIn(f"'{custom}'", stderr)
        self.assertEqual(stderr.count("WARNING"), 1, msg=f"Expected exactly 1 WARNING. Got: {stderr!r}")

    def test_stale_token_check_still_passes(self) -> None:
        """Warning must not affect check outcome — a clean script must still pass."""
        result, _ = self._run_capture_stderr(frozenset({"uv", "validate"}))
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.unresolved_symbols, [])
