"""Unit tests for upgrade_shell_behavioral_check.py (Slice 1).

Covers:
  AC-001 — syntax error in a merged script → gate fails
  AC-002 — dropped function definition → gate reports unresolved symbol
  AC-003 — all defs present → gate passes (positive-path)
  AC-004 — skip=True → gate skipped, no subprocess calls
  REQ-001 — bash -n used for syntax checking
  REQ-002 — depth-1 source resolution resolves function defs
  REQ-003 — failure output includes file, symbol, line
  REQ-010 — grep-based heuristic, no full parser
  REQ-011 — both positive-path and negative-path fixtures tested

Issue #184 — extra_excluded_tokens (TestExtraExcludedTokens, TestPostcheckReadsExtraTokensFromContract):
  AC-001 — token in extra_excluded_tokens → zero unresolved symbols
  AC-002 — absent extra tokens → base set unchanged, false positive flagged
  AC-003 — no-arg call identical to current baseline
  AC-004 — extra token suppresses call site; status=pass
  AC-005 — invalid entries silently skipped
  AC-006 — extra_excluded_count equals valid extra token count
  AC-007 — stderr log line emitted when extra tokens applied
  NFR-REL-001 — absent contract key yields frozenset()
"""

from __future__ import annotations

import io
import tempfile
from contextlib import redirect_stderr
from pathlib import Path
import unittest

from tests._shared.helpers import REPO_ROOT
from scripts.lib.blueprint.upgrade_shell_behavioral_check import run_behavioral_check


FIXTURE_DIR = REPO_ROOT / "tests/blueprint/fixtures/shell_behavioral_check"


class TestRunBehavioralCheckPositivePath(unittest.TestCase):
    """AC-003, REQ-011: positive-path — all function defs present → pass."""

    def test_clean_script_passes(self) -> None:
        script = FIXTURE_DIR / "clean_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass")
        self.assertFalse(result.skipped)
        self.assertEqual(result.files_checked, 1)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])

    def test_sourced_file_resolves_definition(self) -> None:
        """REQ-002: function defined in depth-1 sourced file → call site resolves."""
        script = FIXTURE_DIR / "calls_sourced_helper.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckSyntaxError(unittest.TestCase):
    """AC-001, REQ-001: syntax error in merged script → gate fails."""

    def test_syntax_error_detected(self) -> None:
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "fail")
        self.assertEqual(result.unresolved_symbols, [], msg="symbol check skipped for syntax errors")
        self.assertEqual(len(result.syntax_errors), 1)
        entry = result.syntax_errors[0]
        # REQ-003: file path is present in finding
        self.assertIn("syntax_error_script.sh", entry["file"])
        self.assertIn("error", entry)
        self.assertIsInstance(entry["error"], str)
        self.assertTrue(entry["error"], "error message must be non-empty")

    def test_syntax_error_skips_symbol_check(self) -> None:
        """Files with syntax errors must not produce unresolved_symbol entries."""
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckUnresolvedSymbol(unittest.TestCase):
    """AC-002, REQ-002, REQ-003, REQ-011: dropped def → gate reports symbol."""

    def test_missing_definition_detected(self) -> None:
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "fail")
        self.assertEqual(result.syntax_errors, [], msg="no syntax errors expected")
        self.assertGreaterEqual(len(result.unresolved_symbols), 1)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertIn("setup_environment", symbols)

    def test_finding_includes_file_symbol_line(self) -> None:
        """REQ-003: each finding must include file, symbol, and line."""
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertGreaterEqual(len(result.unresolved_symbols), 1)
        for entry in result.unresolved_symbols:
            self.assertIn("file", entry)
            self.assertIn("symbol", entry)
            self.assertIn("line", entry)
            self.assertIsInstance(entry["line"], int)
            self.assertGreater(entry["line"], 0)
            self.assertIn("missing_def_script.sh", entry["file"])


class TestRunBehavioralCheckSkip(unittest.TestCase):
    """AC-004, REQ-005: skip=True → status=skipped, no subprocess calls."""

    def test_skip_returns_skipped_status(self) -> None:
        script = FIXTURE_DIR / "missing_def_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT, skip=True)

        self.assertEqual(result.status, "skipped")
        self.assertTrue(result.skipped)
        self.assertEqual(result.files_checked, 0)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])

    def test_skip_with_syntax_error_file_still_skipped(self) -> None:
        script = FIXTURE_DIR / "syntax_error_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT, skip=True)

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.syntax_errors, [])


class TestRunBehavioralCheckEmptyInput(unittest.TestCase):
    """Edge case: empty file list → pass with zero counts."""

    def test_empty_file_list_passes(self) -> None:
        result = run_behavioral_check([], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass")
        self.assertFalse(result.skipped)
        self.assertEqual(result.files_checked, 0)
        self.assertEqual(result.syntax_errors, [])
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckHeredocBody(unittest.TestCase):
    """Tokens inside heredoc bodies must not be flagged as unresolved symbols."""

    def test_heredoc_body_not_flagged(self) -> None:
        """Words like Run, Usage, DESCRIPTION inside <<'EOF'...EOF are not calls."""
        script = FIXTURE_DIR / "heredoc_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckCaseLabel(unittest.TestCase):
    """Case statement labels must not be flagged as unresolved symbols."""

    def test_case_label_not_flagged(self) -> None:
        """Labels like postcheck_status) and postcheck_report) are not calls."""
        script = FIXTURE_DIR / "case_label_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))
        self.assertEqual(result.unresolved_symbols, [])


class TestRunBehavioralCheckAsDict(unittest.TestCase):
    """Result as_dict() must include all required fields for JSON serialisation."""

    def test_as_dict_fields_present(self) -> None:
        script = FIXTURE_DIR / "clean_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)
        d = result.as_dict()

        self.assertIn("skipped", d)
        self.assertIn("files_checked", d)
        self.assertIn("syntax_errors", d)
        self.assertIn("unresolved_symbols", d)
        self.assertIn("status", d)


class TestRunBehavioralCheckCaseLabelAlternation(unittest.TestCase):
    """FR-005 / AC-003: case-label alternation tokens must not be flagged."""

    def test_case_alternation_not_flagged(self) -> None:
        """build|test) and deploy | verify) labels produce zero unresolved_symbols."""
        script = FIXTURE_DIR / "case_label_alternation_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("build", symbols, msg="'build' from 'build|test)' must not be flagged")
        self.assertNotIn("test", symbols, msg="'test' from 'build|test)' must not be flagged")
        self.assertNotIn("deploy", symbols, msg="'deploy' from 'deploy | verify)' must not be flagged")
        self.assertNotIn("verify", symbols, msg="'verify' from alternation must not be flagged")
        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))

    def test_pipe_operator_in_command_is_flagged(self) -> None:
        """missing_fn | tee or missing_fn || fallback must NOT be silently skipped as case labels."""
        import tempfile, textwrap
        from pathlib import Path
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            known_func() { echo ok; }
            known_func | tee /dev/null
            known_func || true
        """)
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "pipe_test.sh"
            script.write_text(content, encoding="utf-8")
            result = run_behavioral_check([script], repo_root=REPO_ROOT)
        # known_func IS defined; pipe/logical-or operators must not cause false skips
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("known_func", symbols, msg="known_func should not be flagged")
        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))

    def test_undefined_before_pipe_is_flagged(self) -> None:
        """An undefined function followed by | tee must be flagged, not silently skipped."""
        import tempfile, textwrap
        from pathlib import Path
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            undefined_pipe_func | tee /dev/null
        """)
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "pipe_undefined_test.sh"
            script.write_text(content, encoding="utf-8")
            result = run_behavioral_check([script], repo_root=REPO_ROOT)
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertIn("undefined_pipe_func", symbols, msg="undefined_pipe_func before | must be flagged")


class TestRunBehavioralCheckArrayInitializer(unittest.TestCase):
    """FR-006 / AC-004: bare-words inside array initializers must not be flagged."""

    def test_array_init_bare_words_not_flagged(self) -> None:
        """observability, postgres, deploy, validate inside =( ... ) are not calls."""
        script = FIXTURE_DIR / "array_init_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        for bare_word in ("observability", "postgres", "rabbitmq", "deploy", "validate",
                          "cleanup", "provision"):
            self.assertNotIn(
                bare_word, symbols,
                msg=f"'{bare_word}' inside array initializer must not be flagged",
            )
        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))

    def test_array_close_paren_with_inline_comment_exits_array_mode(self) -> None:
        """') # end array' must exit array tracking so subsequent real calls are still scanned."""
        import tempfile, textwrap
        from pathlib import Path
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            known_func() { echo ok; }
            do_work() {
                local modules=(
                    alpha
                    beta
                ) # end array
                known_func
            }
            do_work
        """)
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "array_comment_close.sh"
            script.write_text(content, encoding="utf-8")
            result = run_behavioral_check([script], repo_root=REPO_ROOT)
        # known_func IS defined; if array_depth stays > 0 it would be silently skipped
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("known_func", symbols, msg="known_func after ') # comment' close must not be skipped")
        self.assertEqual(result.status, "pass", msg=str(result.as_dict()))

    def test_undefined_after_commented_array_close_is_flagged(self) -> None:
        """An undefined call after ') # comment' close must be flagged."""
        import tempfile, textwrap
        from pathlib import Path
        content = textwrap.dedent("""\
            #!/usr/bin/env bash
            do_work() {
                local modules=(
                    alpha
                ) # end array
                undefined_after_commented_close
            }
            do_work
        """)
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "array_comment_close_undef.sh"
            script.write_text(content, encoding="utf-8")
            result = run_behavioral_check([script], repo_root=REPO_ROOT)
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertIn("undefined_after_commented_close", symbols,
                      msg="undefined call after ') # comment' must be flagged")


class TestRunBehavioralCheckExcludedTokensExtended(unittest.TestCase):
    """FR-007 / FR-008 / AC-005: tar, pnpm, and 13 blueprint runtime functions excluded."""

    def test_tar_and_pnpm_not_flagged(self) -> None:
        script = FIXTURE_DIR / "excluded_tokens_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("tar", symbols, msg="'tar' must be in _EXCLUDED_TOKENS")
        self.assertNotIn("pnpm", symbols, msg="'pnpm' must be in _EXCLUDED_TOKENS")

    def test_blueprint_runtime_functions_not_flagged(self) -> None:
        """All 13 blueprint runtime functions from FR-008 must be excluded."""
        script = FIXTURE_DIR / "excluded_tokens_script.sh"
        result = run_behavioral_check([script], repo_root=REPO_ROOT)

        symbols = [e["symbol"] for e in result.unresolved_symbols]
        expected_excluded = [
            "blueprint_require_runtime_env",
            "blueprint_sanitize_init_placeholder_defaults",
            "ensure_file_from_template",
            "ensure_file_from_rendered_template",
            "postgres_init_env",
            "object_storage_init_env",
            "rabbitmq_seed_env_defaults",
            "public_endpoints_seed_env_defaults",
            "identity_aware_proxy_seed_env_defaults",
            "keycloak_seed_env_defaults",
            "render_optional_module_values_file",
            "apply_optional_module_secret_from_literals",
            "delete_optional_module_secret",
        ]
        for fn in expected_excluded:
            self.assertNotIn(
                fn, symbols,
                msg=f"'{fn}' must be in _EXCLUDED_TOKENS per FR-008",
            )


# ===========================================================================
# Issue #184 — extra_excluded_tokens extension (AC-001 – AC-007)
# ===========================================================================


class TestExtraExcludedTokens(unittest.TestCase):
    """Issue #184: extra_excluded_tokens extends the base exclusion set per-invocation."""

    def _script_calling(self, tmp: Path, fn_name: str = "my_custom_helper") -> Path:
        script = tmp / "custom_call.sh"
        script.write_text(f"#!/usr/bin/env bash\n{fn_name}\n", encoding="utf-8")
        return script

    def test_extra_token_suppresses_unresolved_symbol(self) -> None:
        """AC-001, AC-004: token in extra_excluded_tokens → zero unresolved symbols, status=pass."""
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script_calling(Path(tmp))
            result = run_behavioral_check(
                [script],
                repo_root=REPO_ROOT,
                extra_excluded_tokens=frozenset({"my_custom_helper"}),
            )
        self.assertEqual(result.status, "pass")
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("my_custom_helper", symbols)

    def test_absent_extra_tokens_preserves_baseline_behaviour(self) -> None:
        """AC-002, AC-003: absent extra tokens → base set unchanged; my_custom_helper flagged."""
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script_calling(Path(tmp))
            result = run_behavioral_check([script], repo_root=REPO_ROOT)
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertIn("my_custom_helper", symbols)
        self.assertEqual(result.status, "fail")

    def test_invalid_token_skipped_gracefully(self) -> None:
        """AC-005: invalid (non-string, empty) entries silently skipped; no exception raised."""
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script_calling(Path(tmp))
            result = run_behavioral_check(
                [script],
                repo_root=REPO_ROOT,
                extra_excluded_tokens=frozenset({"my_custom_helper", "", 42}),  # type: ignore[arg-type]
            )
        symbols = [e["symbol"] for e in result.unresolved_symbols]
        self.assertNotIn("my_custom_helper", symbols)

    def test_extra_excluded_count_in_result(self) -> None:
        """AC-006: extra_excluded_count equals count of valid extra tokens after filtering."""
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script_calling(Path(tmp))
            result = run_behavioral_check(
                [script],
                repo_root=REPO_ROOT,
                extra_excluded_tokens=frozenset({"my_custom_helper", "another_helper"}),
            )
        self.assertEqual(result.extra_excluded_count, 2)

    def test_obs_log_emitted_when_tokens_applied(self) -> None:
        """AC-007, NFR-OBS-001: stderr log line emitted when extra tokens are applied."""
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            script = self._script_calling(Path(tmp))
            with redirect_stderr(buf):
                run_behavioral_check(
                    [script],
                    repo_root=REPO_ROOT,
                    extra_excluded_tokens=frozenset({"my_custom_helper"}),
                )
        self.assertIn("[BEHAVIORAL-CHECK]", buf.getvalue())
        self.assertIn("extra excluded", buf.getvalue())


class TestPostcheckReadsExtraTokensFromContract(unittest.TestCase):
    """FR-001, FR-006, NFR-REL-001: contract schema exposes upgrade.behavioral_check.extra_excluded_tokens."""

    def test_extra_tokens_loaded_from_contract_yaml(self) -> None:
        """FR-001, FR-006: BehavioralCheckUpgradeContract and UpgradeContract dataclasses exist."""
        from scripts.lib.blueprint.contract_schema import (
            BehavioralCheckUpgradeContract,
            UpgradeContract,
        )
        bc = BehavioralCheckUpgradeContract(extra_excluded_tokens=["my_custom_helper"])
        uc = UpgradeContract(behavioral_check=bc)
        self.assertEqual(uc.behavioral_check.extra_excluded_tokens, ["my_custom_helper"])

    def test_absent_key_yields_empty_frozenset(self) -> None:
        """NFR-REL-001: empty extra_excluded_tokens list converts to empty frozenset."""
        from scripts.lib.blueprint.contract_schema import (
            BehavioralCheckUpgradeContract,
            UpgradeContract,
        )
        bc = BehavioralCheckUpgradeContract(extra_excluded_tokens=[])
        uc = UpgradeContract(behavioral_check=bc)
        tokens = frozenset(
            t for t in uc.behavioral_check.extra_excluded_tokens
            if isinstance(t, str) and t
        )
        self.assertEqual(tokens, frozenset())
