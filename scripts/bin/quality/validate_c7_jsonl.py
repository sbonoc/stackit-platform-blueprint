#!/usr/bin/env python3
"""Validate artifacts/c7/*.jsonl files: each line must be valid JSON with required C7 fields."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REQUIRED_FIELDS = frozenset({
    "event_id", "ticket_id", "parent_ticket_id", "phase", "persona",
    "model", "timestamp", "outcome", "rerun_round", "owner_team", "emitter",
})
_VALID_EMITTERS = frozenset({"orchestrator", "webhook-handler", "local-cli"})


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"{path}: cannot read: {exc}"]
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{i}: invalid JSON: {exc}")
            continue
        missing = _REQUIRED_FIELDS - set(event.keys())
        if missing:
            errors.append(f"{path}:{i}: missing required C7 fields: {sorted(missing)}")
        emitter = event.get("emitter", "")
        if emitter not in _VALID_EMITTERS:
            errors.append(f"{path}:{i}: invalid emitter value: {emitter!r}")
        rerun_round = event.get("rerun_round")
        if not isinstance(rerun_round, int) or rerun_round < 0:
            errors.append(f"{path}:{i}: rerun_round must be a non-negative integer, got {rerun_round!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    paths = [Path(p) for p in (argv if argv is not None else sys.argv[1:])]
    if not paths:
        return 0
    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_file(path))
    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
