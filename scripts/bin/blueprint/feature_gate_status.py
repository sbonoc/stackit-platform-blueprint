#!/usr/bin/env python3
"""Report consumer-seeded feature gate adoption status and upsert backlog entries."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_yaml_subset  # noqa: E402

BLUEPRINT_UPGRADE_SOURCE_ENV = "BLUEPRINT_UPGRADE_SOURCE"
_REPO_INIT_ENV = "blueprint/repo.init.env"
_CONTRACT_PATH = "blueprint/contract.yaml"
_BACKLOG_FILE = "AGENTS.backlog.md"

_BACKLOG_HEADER = "# Blueprint Backlog\n"
_OPEN_MARKER = "[ ]"
_DONE_MARKER = "[x]"
_ENTRY_PREFIX = "(blueprint-feature) seed:"

_ENTRY_RE = re.compile(
    r"^- \[(?P<done>[x ])\] \(blueprint-feature\) seed: (?P<gate_id>\S+)\s*$"
)


def _read_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        result[k.strip()] = v.strip()
    return result


def _load_gates(repo_root: Path) -> list[dict]:
    contract_path = repo_root / _CONTRACT_PATH
    if not contract_path.is_file():
        return []
    raw = load_yaml_subset(contract_path)
    spec = raw.get("spec") if isinstance(raw, dict) else None
    if not isinstance(spec, dict):
        return []
    gates = spec.get("consumer_seeded_feature_gates")
    return gates if isinstance(gates, list) else []


def _is_adopted(gate: dict, repo_root: Path, env_defaults: dict[str, str]) -> bool:
    enable_flag = gate.get("enable_flag", "")
    if enable_flag:
        raw = env_defaults.get(enable_flag, "")
        if raw.strip().lower() in {"1", "true", "yes", "on"}:
            return True
    paths = gate.get("consumer_seeded_paths_when_enabled") or []
    return any((repo_root / p).exists() for p in paths if isinstance(p, str))


def _build_command(gate: dict, source_url: str) -> str:
    gate_id = gate.get("id", "")
    prefix = f"BLUEPRINT_UPGRADE_SOURCE={source_url} " if source_url else ""
    return f"{prefix}make blueprint-seed-feature FEATURE={gate_id}"


def _read_backlog(backlog_path: Path) -> list[str]:
    if not backlog_path.is_file():
        return []
    return backlog_path.read_text(encoding="utf-8").splitlines(keepends=True)


def _write_backlog(backlog_path: Path, lines: list[str]) -> None:
    backlog_path.write_text("".join(lines), encoding="utf-8")


def _entry_tag(gate_id: str) -> str:
    return f"{_ENTRY_PREFIX} {gate_id}"


def _find_entry_line(lines: list[str], gate_id: str) -> int | None:
    tag = _entry_tag(gate_id)
    for i, line in enumerate(lines):
        if tag in line and _ENTRY_RE.match(line.rstrip("\n")):
            return i
    return None


def _build_entry_lines(gate: dict, command: str) -> list[str]:
    gate_id = gate.get("id", "")
    description = gate.get("description", "")
    return [
        f"- [ ] {_ENTRY_PREFIX} {gate_id}\n",
        f"      command: {command}\n",
        f"      description: {description}\n",
    ]


def _upsert_entry(lines: list[str], gate: dict, command: str, *, adopted: bool) -> list[str]:
    gate_id = gate.get("id", "")
    idx = _find_entry_line(lines, gate_id)

    if adopted:
        if idx is not None:
            # Mark as done
            lines[idx] = lines[idx].replace(f"- [ ] {_ENTRY_PREFIX}", f"- [x] {_ENTRY_PREFIX}", 1)
        # If already done or absent: nothing to do
        return lines

    if idx is not None:
        m = _ENTRY_RE.match(lines[idx].rstrip("\n"))
        if m and m.group("done") == "x":
            # Already marked done — keep it
            return lines
        # Already open — no change needed
        return lines

    # Not found — append
    if not lines:
        lines = [_BACKLOG_HEADER, "\n"]
    elif not lines[-1].endswith("\n"):
        lines.append("\n")
    lines.extend(_build_entry_lines(gate, command))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report feature gate adoption and upsert backlog entries."
    )
    parser.add_argument("--repo-root", default=".", help="Consumer repository root (default: .).")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    env_defaults = _read_env_file(repo_root / _REPO_INIT_ENV)

    source_url = os.environ.get(BLUEPRINT_UPGRADE_SOURCE_ENV) or env_defaults.get(
        "BLUEPRINT_UPGRADE_SOURCE", ""
    )
    if not source_url:
        source_url = "<BLUEPRINT_UPGRADE_SOURCE>"

    gates = _load_gates(repo_root)
    if not gates:
        return

    backlog_path = repo_root / _BACKLOG_FILE
    lines = _read_backlog(backlog_path)

    changed = False
    for gate in gates:
        if not isinstance(gate, dict) or not gate.get("id"):
            continue
        adopted = _is_adopted(gate, repo_root, env_defaults)
        command = _build_command(gate, source_url if source_url != "<BLUEPRINT_UPGRADE_SOURCE>" else "")
        before = list(lines)
        lines = _upsert_entry(lines, gate, command, adopted=adopted)
        if lines != before:
            changed = True

    if changed:
        _write_backlog(backlog_path, lines)

    adopted_count = sum(
        1
        for g in gates
        if isinstance(g, dict) and g.get("id") and _is_adopted(g, repo_root, env_defaults)
    )
    unadopted_count = len(gates) - adopted_count
    print(
        f"feature gate status: {adopted_count} adopted, {unadopted_count} unadopted"
        + (f" — see {_BACKLOG_FILE}" if unadopted_count else "")
    )


if __name__ == "__main__":
    main()
