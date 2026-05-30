#!/usr/bin/env python3
"""CLI entrypoint for local-cli C7 lifecycle event emission (issue #347).

Usage:
    python3 scripts/bin/sdd/c7_emit.py emit \\
        --ticket <ticket_id> \\
        --phase <phase> \\
        --skill <skill_basename> \\
        --owner-team <team_slug> \\
        [--outcome success|rejected|retried|human-handoff] \\
        [--slug <work_item_slug>]

The JSONL sink path defaults to artifacts/c7/<slug>.jsonl where <slug>
is derived from the ticket_id unless --slug is provided.

Set BLUEPRINT_SDD_C7_EMIT=0 to suppress emission (one opt-out audit event
is written instead).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.lib.sdd.c7_emit import (
    EmitC7EventUseCase,
    EnvVarModelResolver,
    JsonlReaderAdapter,
    JsonlSinkAdapter,
    OptOutAuditUseCase,
)


def _default_slug(ticket_id: str) -> str:
    return ticket_id


def cmd_emit(args: argparse.Namespace) -> int:
    # NFR-REL-001: helper failure (disk full, malformed input, sink path not
    # writable, unexpected exception) MUST NOT block SDD step execution.
    # Log to stderr and return success — the SDD step's pass/fail is owned
    # by the step's own work product, not by C7 emission.
    try:
        slug = args.slug or _default_slug(args.ticket)
        sink_path = Path("artifacts") / "c7" / f"{slug}.jsonl"
        sink = JsonlSinkAdapter(sink_path)
        reader = JsonlReaderAdapter(sink_path)
        model_resolver = EnvVarModelResolver()

        if OptOutAuditUseCase.is_opted_out():
            audit = OptOutAuditUseCase(
                ticket_id=args.ticket,
                phase=args.phase,
                skill_basename=args.skill,
                owner_team=args.owner_team,
                sink=sink,
                reader=reader,
                model_resolver=model_resolver,
            )
            audit.emit_audit_event()
            print(f"c7: opted out — wrote audit event to {sink_path}", file=sys.stderr)
            return 0

        rerun_round = reader.compute_rerun_round(args.ticket, args.phase)
        use_case = EmitC7EventUseCase(
            ticket_id=args.ticket,
            phase=args.phase,
            skill_basename=args.skill,
            owner_team=args.owner_team,
            outcome=args.outcome,
            rerun_round=rerun_round,
            model_resolver=model_resolver,
        )
        event = use_case.build()
        sink.append(event)
        return 0
    except Exception as exc:  # noqa: BLE001 — NFR-REL-001 requires broad catch
        print(
            f"c7: emission failed (non-blocking, NFR-REL-001): {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C7 lifecycle event emitter (local-cli)")
    sub = parser.add_subparsers(dest="command")

    emit_p = sub.add_parser("emit", help="Emit a C7 lifecycle event")
    emit_p.add_argument("--ticket", required=True, help="GitHub ticket ID (e.g. 347)")
    emit_p.add_argument("--phase", required=True, help="SDD phase enum value")
    emit_p.add_argument("--skill", required=True, help="SDD step skill basename")
    emit_p.add_argument("--owner-team", required=True, dest="owner_team",
                        help="GitHub team slug owning the work item")
    emit_p.add_argument("--outcome", default="success",
                        choices=["success", "rejected", "retried", "human-handoff"],
                        help="Phase outcome (default: success)")
    emit_p.add_argument("--slug", default="",
                        help="Work item slug for JSONL path (default: ticket_id)")

    args = parser.parse_args(argv)
    if args.command == "emit":
        return cmd_emit(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
