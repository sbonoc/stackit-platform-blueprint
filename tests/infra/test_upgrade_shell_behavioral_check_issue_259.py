"""Regression tests for issue #259 — transitive source resolution in behavioral check.

Three fixtures:
  A) Transitive resolution: function defined at depth-2 (a.sh → b.sh → c.sh);
     run_behavioral_check must report 0 failures.
  B) Bare-command suppression: script references 'uv' and 'validate' as bare
     call-site tokens; run_behavioral_check must report 0 failures.
  C) Cycle guard: a.sh sources b.sh sources a.sh; check must complete without
     RecursionError and report 0 failures.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from scripts.lib.blueprint.upgrade_shell_behavioral_check import run_behavioral_check


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TransitiveResolutionIssue259Tests(unittest.TestCase):
    """Fixture A — function defined at depth-2 in a 3-file source chain."""

    def test_function_at_depth_two_is_resolved(self) -> None:
        """run_behavioral_check must find 'deep_helper' defined in c.sh via a.sh→b.sh→c.sh chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # c.sh defines 'deep_helper'
            c = root / "c.sh"
            _write(c, "#!/usr/bin/env bash\nfunction deep_helper() {\n  echo 'hello'\n}\n")

            # b.sh sources c.sh
            b = root / "b.sh"
            _write(b, f"#!/usr/bin/env bash\nsource {c}\n")

            # a.sh sources b.sh and calls deep_helper
            a = root / "a.sh"
            _write(a, f"#!/usr/bin/env bash\nsource {b}\ndeep_helper\n")

            result = run_behavioral_check([a], root)

        self.assertEqual(
            result.status,
            "pass",
            msg=(
                f"Transitive depth-2 function 'deep_helper' must be resolved via BFS. "
                f"unresolved_symbols={result.unresolved_symbols}"
            ),
        )
        self.assertEqual(
            result.unresolved_symbols,
            [],
            msg=(
                f"Expected 0 unresolved symbols but got: {result.unresolved_symbols}"
            ),
        )

    def test_function_at_depth_one_still_resolved(self) -> None:
        """Depth-1 resolution (existing behaviour) must continue to work after the BFS change."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            b = root / "b.sh"
            _write(b, "#!/usr/bin/env bash\nfunction shallow_helper() {\n  echo 'hi'\n}\n")

            a = root / "a.sh"
            _write(a, f"#!/usr/bin/env bash\nsource {b}\nshallow_helper\n")

            result = run_behavioral_check([a], root)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.unresolved_symbols, [])


class BareCommandSuppressionIssue259Tests(unittest.TestCase):
    """Fixture B — bare shell command tokens not in _EXCLUDED_TOKENS must not be flagged."""

    def test_uv_bare_token_not_flagged(self) -> None:
        """'uv' as a bare call site token must not be flagged as an unresolved symbol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            a = root / "a.sh"
            _write(a, "#!/usr/bin/env bash\nuv run python3 -m pytest\n")

            result = run_behavioral_check([a], root)

        uv_findings = [f for f in result.unresolved_symbols if f.get("symbol") == "uv"]
        self.assertEqual(
            uv_findings,
            [],
            msg=(
                f"'uv' must not be reported as unresolved. "
                f"All findings: {result.unresolved_symbols}"
            ),
        )

    def test_validate_bare_token_not_flagged(self) -> None:
        """'validate' as a bare call-site token that is not a function definition must not be flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            a = root / "a.sh"
            _write(
                a,
                "#!/usr/bin/env bash\n"
                "# validate is called here as an external command\n"
                "validate --config config.yaml\n",
            )

            result = run_behavioral_check([a], root)

        validate_findings = [f for f in result.unresolved_symbols if f.get("symbol") == "validate"]
        self.assertEqual(
            validate_findings,
            [],
            msg=(
                f"'validate' must not be reported as unresolved when it is not a "
                f"function definition in any reachable source file. "
                f"All findings: {result.unresolved_symbols}"
            ),
        )

    def test_zero_failures_for_mixed_bare_commands(self) -> None:
        """Script using both 'uv' and 'validate' as bare tokens must produce 0 failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            a = root / "a.sh"
            _write(
                a,
                "#!/usr/bin/env bash\n"
                "uv run python3 script.py\n"
                "validate --config config.yaml\n",
            )

            result = run_behavioral_check([a], root)

        self.assertEqual(
            result.status,
            "pass",
            msg=(
                f"Script with bare 'uv' and 'validate' tokens must produce 0 failures. "
                f"unresolved_symbols={result.unresolved_symbols}"
            ),
        )


class CycleGuardIssue259Tests(unittest.TestCase):
    """Fixture C — circular source chain must not cause RecursionError."""

    def test_cycle_completes_without_recursion_error(self) -> None:
        """a.sh→b.sh→a.sh cycle must terminate and report 0 failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # a.sh defines 'func_a', sources b.sh, calls func_b
            a = root / "a.sh"
            b = root / "b.sh"

            _write(
                a,
                f"#!/usr/bin/env bash\n"
                f"source {b}\n"
                f"function func_a() {{\n  echo 'a'\n}}\n"
                f"func_b\n",
            )
            # b.sh sources a.sh (cycle), defines 'func_b', calls func_a
            _write(
                b,
                f"#!/usr/bin/env bash\n"
                f"source {a}\n"
                f"function func_b() {{\n  echo 'b'\n}}\n"
                f"func_a\n",
            )

            try:
                result = run_behavioral_check([a], root)
            except RecursionError as exc:
                self.fail(
                    f"run_behavioral_check raised RecursionError on circular source chain: {exc}"
                )

        self.assertEqual(
            result.unresolved_symbols,
            [],
            msg=(
                f"Both func_a and func_b must be resolved despite the source cycle. "
                f"unresolved_symbols={result.unresolved_symbols}"
            ),
        )

    def test_cycle_with_only_one_file_checked(self) -> None:
        """Checking only a.sh in a a.sh→b.sh→a.sh cycle must not recurse infinitely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            a = root / "cycle_a.sh"
            b = root / "cycle_b.sh"

            _write(a, f"#!/usr/bin/env bash\nsource {b}\nfunction fa() {{ echo; }}\nfb\n")
            _write(b, f"#!/usr/bin/env bash\nsource {a}\nfunction fb() {{ echo; }}\nfa\n")

            try:
                result = run_behavioral_check([a, b], root)
            except RecursionError as exc:
                self.fail(f"RecursionError on cycle: {exc}")

        self.assertEqual(result.unresolved_symbols, [])
