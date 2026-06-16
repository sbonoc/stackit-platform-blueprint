#!/usr/bin/env python3
"""CLI entrypoint for local-cli C7 lifecycle event emission (issue #347).

Usage:
    python3 scripts/bin/sdd/c7_emit.py emit \\
        --ticket <ticket_id> \\
        --phase <phase> \\
        --skill <skill_basename> \\
        --owner-team <team_slug> \\
        [--outcome success|rejected|retried|human-handoff] \\
        [--slug <work_item_slug>] \\
        [--extension-json <path_or_inline_json>]

The JSONL sink path defaults to artifacts/c7/<slug>.jsonl where <slug>
is derived from the ticket_id unless --slug is provided.

`--extension-json` accepts either (a) a filesystem path to a JSON file
holding a single top-level object, or (b) an inline JSON object string
beginning with `{`. The decoded object is merged into the emitted event
as sibling top-level keys (per the C7 extension-field vocabulary in
design-contracts.md § C7 — e.g., `outcome_details`, `evidence_uri`,
`rejection_reason`). Keys that would shadow the eleven sealed minimum
fields are rejected.

Set BLUEPRINT_SDD_C7_EMIT=0 to suppress emission (one opt-out audit event
is written instead).
"""
from __future__ import annotations

import argparse
import json
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


def _load_extension_fields(source: str) -> dict:
    """Decode the --extension-json argument (file path OR inline JSON).

    An empty/missing value yields an empty dict. An inline value MUST start
    with `{` (object); any other input is treated as a filesystem path.
    Returns the decoded dict. Raises ValueError on malformed input — the
    caller wraps the failure under NFR-REL-001.
    """
    if not source:
        return {}
    stripped = source.strip()
    if stripped.startswith("{"):
        raw = stripped
    else:
        path = Path(source)
        if not path.is_file():
            raise ValueError(
                f"--extension-json path does not exist or is not a file: {source!r}"
            )
        raw = path.read_text(encoding="utf-8")
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--extension-json could not be parsed as JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ValueError(
            "--extension-json MUST decode to a JSON object at top level; "
            f"got {type(decoded).__name__}"
        )
    return decoded


def cmd_emit(args: argparse.Namespace) -> int:
    # Fail hard on empty required args: these are shell expansion errors
    # (e.g. unset $TICKET_ID) not infrastructure failures — NFR-REL-001 does
    # not apply here, and silently writing a blank-field event is worse than
    # blocking (it corrupts the audit trail).
    missing_args = [
        name for name, val in [
            ("--ticket", args.ticket),
            ("--skill", args.skill),
            ("--owner-team", args.owner_team),
        ]
        if not val
    ]
    if missing_args:
        print(
            f"c7: missing or empty required arguments: {', '.join(missing_args)}",
            file=sys.stderr,
        )
        return 1
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
            wrote = audit.emit_audit_event()
            if wrote:
                print(f"c7: opted out — wrote audit event to {sink_path}", file=sys.stderr)
            else:
                print(
                    f"c7: opted out — prior audit event already present in {sink_path} (FR-007 dedup)",
                    file=sys.stderr,
                )
            return 0

        extension_fields = _load_extension_fields(args.extension_json)

        rerun_round = reader.compute_rerun_round(args.ticket, args.phase)
        use_case = EmitC7EventUseCase(
            ticket_id=args.ticket,
            phase=args.phase,
            skill_basename=args.skill,
            owner_team=args.owner_team,
            outcome=args.outcome,
            rerun_round=rerun_round,
            model_resolver=model_resolver,
            extension_fields=extension_fields,
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
    emit_p.add_argument("--extension-json", default="", dest="extension_json",
                        help="Path to JSON file OR inline JSON object string carrying "
                             "C7 extension fields (e.g. outcome_details, evidence_uri, "
                             "rejection_reason) to merge into the emitted event. "
                             "Inline JSON MUST start with `{`; anything else is treated "
                             "as a filesystem path. Reserved minimum-schema keys MUST "
                             "NOT be shadowed.")

    args = parser.parse_args(argv)
    if args.command == "emit":
        return cmd_emit(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
