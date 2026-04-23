#!/usr/bin/env python3
"""JSON report module for the fresh-environment smoke gate.

Provides:
  - FreshEnvGateResult dataclass
  - compute_divergences(): file-set diff between worktree and working tree
  - write_report(): serialize FreshEnvGateResult to JSON

CLI usage (invoked by the shell wrapper):
  python3 upgrade_fresh_env_gate.py \\
      --worktree-path /tmp/wt-abc123 \\
      --working-tree-path /path/to/consumer-repo \\
      --output-path artifacts/blueprint/fresh_env_gate.json \\
      --status pass|fail|error \\
      --targets-run "make infra-validate" \\
      --targets-run "make blueprint-upgrade-consumer-postcheck" \\
      [--error "error message"] \\
      --exit-code 0
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GATE_REPORT_DEFAULT_PATH = "artifacts/blueprint/fresh_env_gate.json"

# Top-level directory names excluded from divergence file-set comparisons.
_EXCLUDE_TOP_DIRS: frozenset[str] = frozenset({
    ".git",
    "artifacts",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
})


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FreshEnvGateResult:
    status: str               # "pass" | "fail" | "error"
    worktree_path: str
    targets_run: list[str]
    divergences: list[dict[str, str]]
    error: str | None
    exit_code: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "worktree_path": self.worktree_path,
            "targets_run": list(self.targets_run),
            "divergences": list(self.divergences),
            "error": self.error,
            "exit_code": self.exit_code,
        }


# ---------------------------------------------------------------------------
# Divergence computation
# ---------------------------------------------------------------------------

def _walk_files(root: Path) -> set[str]:
    """Return relative POSIX paths of all tracked files, excluding top-level excluded dirs."""
    result: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        # Exclude if the first path component is in the exclusion set
        if rel.parts[0] in _EXCLUDE_TOP_DIRS:
            continue
        result.add(rel.as_posix())
    return result


def compute_divergences(
    worktree_path: str | Path,
    working_tree_path: str | Path,
) -> list[dict[str, str]]:
    """Compute file-set differences between a fresh worktree and the working tree.

    Returns divergence dicts with keys:
      - "file": repo-relative POSIX path of the diverging file
      - "reason":
          "missing_in_fresh_env"     — present in working tree, absent in worktree
                                       (file exists locally but would be absent on a
                                       fresh CI checkout or bootstrap run)
          "unexpected_in_fresh_env"  — present in worktree, absent in working tree
                                       (file was created by targets in the worktree
                                       but not present in the working tree)
    """
    wt_path = Path(working_tree_path)
    wk_path = Path(worktree_path)

    working_files = _walk_files(wt_path)
    worktree_files = _walk_files(wk_path)

    divergences: list[dict[str, str]] = []

    for f in sorted(working_files - worktree_files):
        divergences.append({"file": f, "reason": "missing_in_fresh_env"})

    for f in sorted(worktree_files - working_files):
        divergences.append({"file": f, "reason": "unexpected_in_fresh_env"})

    return divergences


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(result: FreshEnvGateResult, output_path: str | Path) -> None:
    """Serialize FreshEnvGateResult to JSON, creating parent directories as needed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.as_dict(), indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI entry point (called by the shell wrapper)
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree-path", required=True, help="Absolute path to the temporary worktree.")
    parser.add_argument("--working-tree-path", required=True, help="Absolute path to the consumer repo root (working tree).")
    parser.add_argument(
        "--output-path",
        default=GATE_REPORT_DEFAULT_PATH,
        help="Gate report output path (absolute or consumer-repo-relative).",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=["pass", "fail", "error"],
        help="Gate outcome status.",
    )
    parser.add_argument(
        "--targets-run",
        action="append",
        default=[],
        metavar="TARGET",
        help="Make target that was run inside the worktree (repeatable).",
    )
    parser.add_argument("--error", default=None, help="Error message when status=error.")
    parser.add_argument("--exit-code", type=int, default=0, help="Combined target exit code.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    worktree = Path(args.worktree_path)
    working_tree = Path(args.working_tree_path)

    output_path = Path(args.output_path)
    if not output_path.is_absolute():
        output_path = (working_tree / output_path).resolve()

    divergences: list[dict[str, str]] = []
    if args.status == "fail" and worktree.exists():
        divergences = compute_divergences(worktree, working_tree)

    result = FreshEnvGateResult(
        status=args.status,
        worktree_path=str(worktree),
        targets_run=args.targets_run,
        divergences=divergences,
        error=args.error,
        exit_code=args.exit_code,
    )
    write_report(result, output_path)


if __name__ == "__main__":
    main()
