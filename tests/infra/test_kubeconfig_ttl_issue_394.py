"""Tests for issue #394 — stackit_ske_kubeconfig force-taint on every foundation apply.

The taint is placed in stackit_foundation_apply.sh (before terraform apply), not in
stackit_foundation_fetch_kubeconfig.sh (which only reads terraform output and never calls apply).

AC-001: terraform taint stackit_ske_kubeconfig.foundation[0] is invoked before
        terraform apply in stackit_foundation_apply.sh in execute mode.
AC-002: taint step is unconditionally skipped when DRY_RUN=true.
AC-003: script aborts (exit non-zero) when terraform taint exits non-zero, before
        reaching terraform apply.
AC-004: a log_info message containing the resource address appears before the
        taint invocation.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_APPLY_SCRIPT = (
    REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_foundation_apply.sh"
)

# Minimal placeholder kubeconfig content the stub will emit for
# `terraform output -raw ske_kubeconfig`.
_PLACEHOLDER_KUBECONFIG = """\
apiVersion: v1
kind: Config
clusters: []
contexts: []
current-context: ""
users: []
"""


def _write_terraform_stub(bin_dir: Path, *, taint_exit_code: int = 0) -> Path:
    """Write a terraform stub that records every invocation and controls taint exit code."""
    stub = bin_dir / "terraform"
    stub.write_text(
        f"""\
#!/usr/bin/env bash
set -euo pipefail
LOG="${{TERRAFORM_STUB_LOG:-/dev/null}}"
printf '%s\\n' "$*" >> "$LOG"
# Handle init silently
if [[ "${{1:-}}" == "init" || "${{1:-}}" == "-chdir="* && "${{2:-}}" == "init" ]]; then
  exit 0
fi
# Match -chdir=... as first arg
first="${{1:-}}"
second="${{2:-}}"
if [[ "$first" == "-chdir="* && "$second" == "init" ]]; then
  exit 0
fi
if [[ "$first" == "-chdir="* && "$second" == "taint" ]]; then
  exit {taint_exit_code}
fi
if [[ "$first" == "-chdir="* && "$second" == "apply" ]]; then
  exit 0
fi
if [[ "$first" == "-chdir="* && "$second" == "output" ]]; then
  printf '%s' '{_PLACEHOLDER_KUBECONFIG}'
  exit 0
fi
if [[ "${{1:-}}" == "taint" ]]; then
  exit {taint_exit_code}
fi
if [[ "${{1:-}}" == "apply" ]]; then
  exit 0
fi
exit 0
""",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub


def _base_env(
    bin_dir: Path,
    log_path: Path,
    *,
    dry_run: bool,
) -> dict[str, str]:
    """Build the environment dict for invoking the foundation apply script."""
    env = os.environ.copy()
    env["BLUEPRINT_PROFILE"] = "stackit-dev"
    env["DRY_RUN"] = "false" if not dry_run else "true"
    env["STACKIT_PROJECT_ID"] = "test-project-id"
    env["STACKIT_REGION"] = "eu01"
    # Override terraform dir lookup so preflight does not fail on missing infra dir.
    foundation_tf_dir = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation"
    env["STACKIT_FOUNDATION_TERRAFORM_DIR"] = str(foundation_tf_dir)
    env["STACKIT_TFSTATE_ACCESS_KEY_ID"] = "stub-key-id"
    env["STACKIT_TFSTATE_SECRET_ACCESS_KEY"] = "stub-secret"
    env["TERRAFORM_STUB_LOG"] = str(log_path)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    # Suppress metric/state side-effects that would fail outside a real env.
    env["BLUEPRINT_SDD_C7_EMIT"] = "0"
    return env


def _run_apply(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(_APPLY_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class AC001TaintInvokedBeforeApply(unittest.TestCase):
    """T-101: static-analysis check — taint call appears before apply in stackit_foundation_apply.sh."""

    def test_taint_precedes_apply_in_script_source(self) -> None:
        """T-101: a terraform taint call targeting stackit_ske_kubeconfig.foundation[0] MUST
        appear before the run_terraform_action_with_backend apply call in stackit_foundation_apply.sh."""
        source = _APPLY_SCRIPT.read_text(encoding="utf-8")

        taint_pos = source.find("stackit_ske_kubeconfig.foundation[0]")
        self.assertGreater(
            taint_pos,
            0,
            msg=(
                "stackit_foundation_apply.sh MUST contain a taint invocation targeting "
                "'stackit_ske_kubeconfig.foundation[0]' (FR-001)"
            ),
        )
        # The word 'taint' must appear on the same run_cmd line as the resource address.
        taint_line_start = source.rfind("\n", 0, taint_pos) + 1
        taint_line = source[taint_line_start : source.find("\n", taint_pos)]
        self.assertIn(
            "taint",
            taint_line,
            msg=(
                f"The line containing the resource address MUST include the 'taint' subcommand. "
                f"Line: {taint_line!r}"
            ),
        )

        # run_terraform_action_with_backend apply call MUST appear after the taint.
        apply_pos = source.find("run_terraform_action_with_backend apply", taint_pos)
        self.assertGreater(
            apply_pos,
            taint_pos,
            msg=(
                "terraform taint MUST appear before run_terraform_action_with_backend apply "
                "in stackit_foundation_apply.sh source (AC-001)"
            ),
        )

    def test_taint_not_in_fetch_kubeconfig_script(self) -> None:
        """Regression: the taint MUST NOT be in stackit_foundation_fetch_kubeconfig.sh,
        which never calls terraform apply and where the taint would be inert."""
        fetch_script = (
            REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_foundation_fetch_kubeconfig.sh"
        )
        source = fetch_script.read_text(encoding="utf-8")
        # Only non-comment occurrences count.
        for line in source.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            self.assertNotIn(
                "taint",
                stripped,
                msg=(
                    "stackit_foundation_fetch_kubeconfig.sh MUST NOT contain a terraform taint call — "
                    "taint without a subsequent terraform apply is inert and misleading (regression check)"
                ),
            )


class AC002TaintSkippedInDryRun(unittest.TestCase):
    """T-102: DRY_RUN=true — apply script completes without invoking terraform taint, exits 0."""

    def test_no_taint_call_in_dry_run_mode(self) -> None:
        """T-102: when DRY_RUN=true the apply script MUST exit 0 and MUST NOT invoke terraform taint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            log_path = tmp / "terraform_calls.log"

            _write_terraform_stub(bin_dir, taint_exit_code=0)

            env = _base_env(bin_dir, log_path, dry_run=True)
            result = _run_apply(env)

            self.assertEqual(
                result.returncode,
                0,
                msg=(
                    f"DRY_RUN=true: script MUST exit 0 (AC-002). "
                    f"stdout={result.stdout!r} stderr={result.stderr!r}"
                ),
            )
            if log_path.exists():
                calls = log_path.read_text(encoding="utf-8")
                self.assertNotIn(
                    "taint",
                    calls,
                    msg=(
                        f"DRY_RUN=true: 'terraform taint' MUST NOT be invoked (AC-002). "
                        f"Recorded calls: {calls!r}"
                    ),
                )


class AC003AbortOnTaintFailure(unittest.TestCase):
    """T-103: when terraform taint exits non-zero, apply script MUST abort before terraform apply."""

    def test_script_aborts_when_taint_fails(self) -> None:
        """T-103: non-zero terraform taint exit MUST cause script to exit non-zero
        before reaching terraform apply."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            log_path = tmp / "terraform_calls.log"

            _write_terraform_stub(bin_dir, taint_exit_code=1)

            env = _base_env(bin_dir, log_path, dry_run=False)
            result = _run_apply(env)

            self.assertNotEqual(
                result.returncode,
                0,
                msg=(
                    f"Script MUST exit non-zero when terraform taint fails (AC-003 / NFR-REL-001). "
                    f"stdout={result.stdout!r} stderr={result.stderr!r}"
                ),
            )
            # terraform apply MUST NOT have been called.
            if log_path.exists():
                calls = log_path.read_text(encoding="utf-8")
                apply_lines = [l for l in calls.splitlines() if "apply" in l and "taint" not in l]
                self.assertEqual(
                    apply_lines,
                    [],
                    msg=(
                        f"terraform apply MUST NOT be called after taint failure (AC-003). "
                        f"Recorded calls: {calls!r}"
                    ),
                )


class AC004LogMessageOnTaint(unittest.TestCase):
    """T-104: static-analysis check — log_info call with resource address precedes taint."""

    def test_log_info_with_resource_address_precedes_taint(self) -> None:
        """T-104: stackit_foundation_apply.sh MUST emit a log_info message containing the
        kubeconfig resource address before invoking terraform taint (AC-004 / NFR-OBS-001)."""
        import re

        source = _APPLY_SCRIPT.read_text(encoding="utf-8")
        # Locate the actual taint command line (not a comment).
        taint_cmd_pos = -1
        for m in re.finditer(r'\btaint\b', source):
            line_start = source.rfind("\n", 0, m.start()) + 1
            line_end = source.find("\n", m.start())
            line = source[line_start:line_end].lstrip()
            if line.startswith("#"):
                continue
            if "stackit_ske_kubeconfig" in source[line_start:line_end]:
                taint_cmd_pos = line_start
                break
        self.assertGreater(
            taint_cmd_pos, 0,
            msg="terraform taint targeting stackit_ske_kubeconfig.foundation[0] must be present in apply script"
        )

        pre_taint = source[:taint_cmd_pos]
        log_pos = max(pre_taint.rfind("log_info"), pre_taint.rfind("log_metric"))
        self.assertGreater(
            log_pos,
            0,
            msg=(
                "A log_info or log_metric call MUST appear before the taint invocation "
                "so the forced taint is observable in telemetry (AC-004 / NFR-OBS-001)"
            ),
        )
        log_segment = pre_taint[log_pos : log_pos + 160]
        self.assertTrue(
            "stackit_ske_kubeconfig" in log_segment or "taint" in log_segment.lower() or "kubeconfig" in log_segment.lower(),
            msg=(
                f"The log call immediately before the taint MUST mention the "
                f"resource or action being taken. Found: {log_segment!r}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
