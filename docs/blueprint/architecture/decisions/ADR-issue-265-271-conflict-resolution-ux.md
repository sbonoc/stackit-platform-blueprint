# ADR: Issues #265 + #271 — Conflict Resolution UX: Triage Manifest and Auto-Resolve Target

- **Status**: proposed
- **Date**: 2026-05-13
- **Issues**: #265, #271
- **Work item**: `specs/2026-05-13-issue-265-271-conflict-resolution-ux/`
- **ADR technical decision sign-off**: pending

## Context

Stage 2 (apply) of the upgrade pipeline writes one `.conflict.json` per conflicting file. During the real consumer upgrade (dhe-marketplace v1.7.0 → v1.10.0, PR #62), this produced 88 conflict files. The agent had to enumerate them via ad-hoc Python, manually classify each by path prefix, write a one-off resolution script, and prompt the user 7+ times for individual decisions. Wall-clock cost: ~25 minutes.

The engine already computes `UpgradeEntry.ownership` for every file (classifying it as `blueprint-managed-root`, `required-file`, `init-managed`, `conditional-scaffold`, `blueprint-managed`, or `consumer-seeded`). None of this classification is surfaced after apply. The recommended action for each ownership class is deterministic and well-understood; the engine simply does not emit it.

Two components are missing:
1. An aggregated triage manifest (`upgrade_triage.json`) with per-conflict ownership classification and recommended action — emitted by the engine immediately after `_apply_entries`.
2. A resolve target (`blueprint-upgrade-consumer-resolve`) that auto-applies all deterministic rows and surfaces only the genuinely ambiguous ones in a residual table.

## Decision

### Triage manifest emission (Issue #265, Part 1)

Add `_write_upgrade_triage()` to `upgrade_consumer.py`, called from `_run_apply()` when `conflict_count > 0`. The function:
- Correlates each `ApplyResult` (conflict) with its source `UpgradeEntry` by path to obtain `ownership`.
- Derives `recommended_action` from `ownership_class` via a deterministic mapping (see below).
- Computes `source_diff_summary` and `target_diff_from_baseline` using `difflib` on content from the per-file `.conflict.json` (diff summary strings only — no file contents stored in triage).
- Excludes `blueprint/contract.yaml` (owned exclusively by Stage 3, the contract resolver).
- Writes `artifacts/blueprint/upgrade_triage.json` conforming to `upgrade_triage.schema.json` (JSON Schema draft-07, `schema_version: 1`).

**Ownership → recommended_action mapping:**

| `ownership_class` | `recommended_action` |
|---|---|
| `blueprint-managed-root` | `take_source` |
| `required-file` | `take_source` |
| `init-managed` | `take_source` |
| `conditional-scaffold` | `take_source` |
| `consumer-seeded` | `take_target` |
| `blueprint-managed` (catch-all) | `human_required` |
| any unrecognised class | `human_required` |

The catch-all `blueprint-managed` → `human_required` is a conservative choice (Option A) that prevents auto-overwriting consumer-modified files not yet in any explicit blueprint ownership category. This will be revisited when Issue #270 ships explicit consumer test ownership markers.

### Resolve target (Issue #265, Part 2 + Issue #271)

New `scripts/lib/blueprint/upgrade_consumer_resolve.py`, invoked by the new `blueprint-upgrade-consumer-resolve` make target:
- Reads and validates `upgrade_triage.json` against the schema at startup.
- Applies `take_source`, `take_target`, `delete` rows: writes chosen content to the working-tree file; clears the corresponding `.conflict.json`.
- Writes `artifacts/blueprint/upgrade_resolve.json` with per-action audit trail.
- Prints a single residual table for `human_required` rows, sorted by ownership class then path, truncated >20 with a footer.
- Supports `--dry-run`, `--interactive` / `INTERACTIVE=true`, `--accept-source ALL`, `--accept-target ALL`.
- Is idempotent: re-running on an already-resolved tree produces no changes and exits 0.

## Alternatives Considered

### Option B — Source-exists inference for catch-all classification
Use `UpgradeEntry.source_exists` to infer blueprint ownership for catch-all files: if `source_exists=True` and ownership is `blueprint-managed`, treat as `take_source`. This would reduce `human_required` rows before Issue #270 ships.

**Rejected**: `source_exists=True` is a necessary but not sufficient condition for blueprint ownership. A consumer can create files in blueprint-tracked directories (e.g. `tests/infra/test_my_custom.py`) and they will appear in the blueprint source only if they were seeded from the template. Option B risks auto-overwriting consumer modifications. Option A's conservative approach is correct for a first release.

### Full TUI (lazygit-style conflict resolver)
**Rejected**: heavy external dependency; not portable across all consumer environments; the residual table is typically <10 rows once blueprint-managed-root conflicts are auto-resolved.

### HTML conflict report
**Rejected**: adds browser context-switch friction; residual table is compact enough for CLI display.

### Auto-resolve everything in the engine (no separate target)
**Rejected**: separation of concerns. The engine's job is "classify and record"; the resolve target's job is "apply decisions". Keeping them separate allows the human or agent to inspect `upgrade_triage.json` before any auto-resolution, and allows `--dry-run` to be a meaningful pre-flight.

## Consequences

- **Positive**: 85 of 88 conflicts from the real upgrade evidence will auto-resolve in a single `blueprint-upgrade-consumer-resolve` invocation. The 3 catch-all `human_required` rows require human review — as expected. Wall-clock cost drops from ~25 minutes to <2 minutes.
- **Positive**: `upgrade_triage.json` and `upgrade_resolve.json` give agents a structured machine-readable audit trail; no more ad-hoc Python enumeration scripts.
- **Positive**: `--dry-run` enables safe inspection before any write.
- **Limitation**: until Issue #270 ships, files in the `blueprint-managed` catch-all that are conceptually blueprint-owned (but not in `blueprint_managed_roots`) will appear as `human_required`. In practice this affects only files the blueprint added to directories outside `blueprint_managed_roots` without also listing them in `required_files` or `init_managed` — a small set.
- **Backward compatibility**: triage emission is purely additive; `.conflict.json` files continue to be written unchanged. Existing consumers who do not use the resolve target are unaffected.
