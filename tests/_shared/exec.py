from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess
from typing import Mapping, Sequence


DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS = int(os.environ.get("BLUEPRINT_TEST_COMMAND_TIMEOUT_SECONDS", "900"))


def _ensure_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def format_completed_process(
    result: subprocess.CompletedProcess[str],
    *,
    cmd: Sequence[str],
    cwd: Path,
    timeout_seconds: int,
) -> str:
    return "\n".join(
        (
            f"command: {shlex.join(list(cmd))}",
            f"cwd: {cwd}",
            f"exit: {result.returncode}",
            f"timeout_seconds: {timeout_seconds}",
            f"stdout:\n{result.stdout}",
            f"stderr:\n{result.stderr}",
        )
    )


def run_command(
    cmd: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    effective_timeout = timeout_seconds or DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        return subprocess.run(
            list(cmd),
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            env=merged_env,
            timeout=effective_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _ensure_text(exc.stdout)
        stderr = _ensure_text(exc.stderr)
        timeout_message = (
            f"[test-exec] timeout after {effective_timeout}s while running {shlex.join(list(cmd))} in {cwd}\n"
        )
        return subprocess.CompletedProcess(
            args=list(cmd),
            returncode=124,
            stdout=stdout,
            stderr=stderr + timeout_message,
        )
