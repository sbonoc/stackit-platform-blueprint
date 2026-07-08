"""Tests for issue #394 — stackit_ske_kubeconfig force-taint on every refresh.

AC-001: terraform taint stackit_ske_kubeconfig.foundation[0] is invoked before
        terraform apply in execute mode.
AC-002: taint step is unconditionally skipped when DRY_RUN=true.
AC-003: script aborts (exit non-zero) when terraform taint exits non-zero, before
        reaching terraform output.
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

_FETCH_KUBECONFIG_SCRIPT = (
    REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_foundation_fetch_kubeconfig.sh"
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
if [[ "${{1:-}}" == "init" ]]; then
  exit 0
fi
# Handle taint with configurable exit code
if [[ "${{1:-}}" == "taint" ]]; then
  exit {taint_exit_code}
fi
# Handle apply silently
if [[ "${{1:-}}" == "apply" ]]; then
  exit 0
fi
# Handle output: emit placeholder kubeconfig to stdout when -raw ske_kubeconfig
if [[ "${{1:-}}" == "-chdir="* && "$*" == *"output"* && "$*" == *"ske_kubeconfig"* ]]; then
  printf '%s' '{_PLACEHOLDER_KUBECONFIG}'
  exit 0
fi
# Default: succeed silently
exit 0
""",
        encoding="utf-8",
    )
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub


def _base_env(
    bin_dir: Path,
    log_path: Path,
    kubeconfig_output: Path,
    *,
    dry_run: bool,
) -> dict[str, str]:
    """Build the environment dict for invoking the fetch script."""
    env = os.environ.copy()
    env["BLUEPRINT_PROFILE"] = "stackit-dev"
    env["DRY_RUN"] = "false" if not dry_run else "true"
    env["STACKIT_PROJECT_ID"] = "test-project-id"
    env["STACKIT_REGION"] = "eu01"
    env["STACKIT_FOUNDATION_KUBECONFIG_OUTPUT"] = str(kubeconfig_output)
    # Override terraform dir lookup so preflight doesn't fail on missing infra dir.
    env["STACKIT_FOUNDATION_TERRAFORM_DIR"] = str(REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation")
    env["TERRAFORM_STUB_LOG"] = str(log_path)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    # Suppress metric/state side-effects that would fail outside a real env.
    env["BLUEPRINT_SDD_C7_EMIT"] = "0"
    return env


def _run_script(
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(_FETCH_KUBECONFIG_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class AC001TaintInvokedBeforeApply(unittest.TestCase):
    """T-101: static-analysis check — taint call appears before apply in script source."""

    def test_taint_precedes_apply_in_script_source(self) -> None:
        """T-101: 'terraform taint stackit_ske_kubeconfig.foundation[0]' MUST appear before
        'terraform ... apply' in the execute-mode code path of the script."""
        source = _FETCH_KUBECONFIG_SCRIPT.read_text(encoding="utf-8")
        taint_pos = source.find("terraform taint")
        apply_pos = source.find("terraform")
        # Find actual apply occurrence (not taint)
        idx = 0
        apply_pos = -1
        while True:
            found = source.find("terraform", idx)
            if found == -1:
                break
            segment = source[found : found + 40]
            if "taint" not in segment and ("apply" in segment or "-chdir" in segment):
                apply_pos = found
                break
            idx = found + 1
        self.assertGreater(
            taint_pos,
            0,
            msg="Script MUST contain 'terraform taint' invocation (FR-001)",
        )
        self.assertIn(
            "stackit_ske_kubeconfig",
            source[taint_pos : taint_pos + 80],
            msg="terraform taint MUST target 'stackit_ske_kubeconfig' resource (FR-001)",
        )
        self.assertGreater(
            apply_pos,
            taint_pos,
            msg=(
                "terraform taint MUST appear before terraform apply/output in the script "
                "(AC-001: taint must precede any subsequent terraform operation)"
            ),
        )


class AC002TaintSkippedInDryRun(unittest.TestCase):
    """T-102: DRY_RUN=true — script completes without invoking terraform taint, exits 0."""

    def test_no_taint_call_in_dry_run_mode(self) -> None:
        """T-102: when DRY_RUN=true the script MUST exit 0 and MUST NOT invoke terraform taint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            log_path = tmp / "terraform_calls.log"
            kubeconfig_out = tmp / "kubeconfig.yaml"

            _write_terraform_stub(bin_dir, taint_exit_code=0)

            env = _base_env(bin_dir, log_path, kubeconfig_out, dry_run=True)
            result = _run_script(env)

            self.assertEqual(
                result.returncode,
                0,
                msg=(
                    f"DRY_RUN=true: script MUST exit 0 (AC-002). "
                    f"stdout={result.stdout!r} stderr={result.stderr!r}"
                ),
            )
            # In dry-run mode the stub terraform is not invoked at all (DRY_RUN branch
            # writes a placeholder without calling terraform). Confirm no taint call.
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
    """T-103: when terraform taint exits non-zero, script MUST abort before terraform output."""

    def test_script_aborts_when_taint_fails(self) -> None:
        """T-103: non-zero terraform taint exit MUST cause script to exit non-zero
        before reaching the terraform output -raw ske_kubeconfig call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            log_path = tmp / "terraform_calls.log"
            kubeconfig_out = tmp / "kubeconfig.yaml"

            _write_terraform_stub(bin_dir, taint_exit_code=1)

            env = _base_env(bin_dir, log_path, kubeconfig_out, dry_run=False)
            result = _run_script(env)

            self.assertNotEqual(
                result.returncode,
                0,
                msg=(
                    f"Script MUST exit non-zero when terraform taint fails (AC-003 / NFR-REL-001). "
                    f"stdout={result.stdout!r} stderr={result.stderr!r}"
                ),
            )
            # The terraform output (ske_kubeconfig) call MUST NOT have been reached.
            self.assertFalse(
                kubeconfig_out.exists(),
                msg=(
                    "kubeconfig output file MUST NOT be written when taint fails "
                    "(AC-003: abort before terraform output)"
                ),
            )
            if log_path.exists():
                calls = log_path.read_text(encoding="utf-8")
                self.assertNotIn(
                    "ske_kubeconfig",
                    calls,
                    msg=(
                        f"terraform output ske_kubeconfig MUST NOT be called after taint failure (AC-003). "
                        f"Recorded calls: {calls!r}"
                    ),
                )


class AC004LogMessageOnTaint(unittest.TestCase):
    """T-104: static-analysis check — log_info call with resource address precedes taint."""

    def test_log_info_with_resource_address_precedes_taint(self) -> None:
        """T-104: script MUST emit a log_info message containing the kubeconfig resource
        address before invoking terraform taint (AC-004 / NFR-OBS-001)."""
        source = _FETCH_KUBECONFIG_SCRIPT.read_text(encoding="utf-8")
        taint_pos = source.find("terraform taint")
        self.assertGreater(taint_pos, 0, msg="terraform taint must be present in script")

        # Find the closest log_info or log_metric call before the taint line.
        pre_taint = source[:taint_pos]
        log_pos = max(pre_taint.rfind("log_info"), pre_taint.rfind("log_metric"))
        self.assertGreater(
            log_pos,
            0,
            msg=(
                "A log_info or log_metric call MUST appear before terraform taint "
                "so the forced taint is observable in telemetry (AC-004 / NFR-OBS-001)"
            ),
        )
        log_segment = pre_taint[log_pos : log_pos + 120]
        self.assertTrue(
            "stackit_ske_kubeconfig" in log_segment or "taint" in log_segment.lower() or "kubeconfig" in log_segment.lower(),
            msg=(
                f"The log call immediately before terraform taint MUST mention the "
                f"resource or action being taken. Found: {log_segment!r}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
