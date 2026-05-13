# PR Context

## Summary
- Work item: Issues #265 + #271 — conflict resolution UX (branch `codex/2026-05-13-issue-265-271-conflict-resolution-ux`, PR #283)
- Objective: Reduce upgrade conflict resolution from ~25 minutes of ad-hoc scripting and manual classification to a single `make blueprint-upgrade-consumer-resolve` invocation that auto-applies all classifiable conflicts and presents a residual table of only the rows requiring human judgement.
- Scope boundaries: new triage JSON emission in upgrade engine (Stage 2), new resolve script + make target, schema, 14 new tests. No changes to Stage 3 contract resolver, no HTTP routes, no app delivery targets, no production services.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, NFR-IDM-001, NFR-SCH-001, NFR-SEC-001, NFR-REL-001, NFR-OBS-001, NFR-A11Y-001 (N/A), NFR-OPS-001 (N/A)
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010
- Contract surfaces changed: new make target `blueprint-upgrade-consumer-resolve` in `blueprint.generated.mk`; new artifact paths `artifacts/blueprint/upgrade_triage.json` and `artifacts/blueprint/upgrade_resolve.json`; new schema `scripts/lib/blueprint/schemas/upgrade_triage.schema.json`; new env var `INTERACTIVE` and flags `--dry-run`, `--accept-source ALL`, `--accept-target ALL` for resolve script.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `_recommended_action()`, `_write_upgrade_triage()`, call site in `_run_apply()`
  - `scripts/lib/blueprint/upgrade_consumer_resolve.py` — `_resolve()`, `_apply_take()`, `_print_residual_table()`
  - `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` — schema definition
  - `tests/infra/test_conflict_triage_issue_265.py` — 5 triage tests
  - `tests/infra/test_conflict_resolve_issue_265.py` — 9 resolve tests
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer.py` — existing engine modified to add triage emission; regression risk on `_apply_entries()` call site
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — template that drives `make/blueprint.generated.mk`; must stay in sync

## Validation Evidence
- Required commands executed: `uv run pytest tests/infra/test_conflict_triage_issue_265.py tests/infra/test_conflict_resolve_issue_265.py -v` (14/14 GREEN); `make quality-hooks-fast` (pass); `make quality-docs-check-changed` (pass); `make docs-build` + `make docs-smoke` (pass); `make quality-hardening-review` (pass)
- Result summary: 14 new tests green; all quality hooks pass; 11 pre-existing failures in `tests/blueprint/test_upgrade_consumer.py` confirmed pre-existing before this branch (verified via `git stash`)
- Artifact references: `specs/2026-05-13-issue-265-271-conflict-resolution-ux/hardening_review.md`, `evidence_manifest.json`, `traceability.md`

## Risk and Rollback
- Main risks: (1) triage emission call site in `upgrade_consumer.py` — added after `_apply_entries()` when `conflict_count > 0`; failure raises and causes Stage 2 exit non-zero; 5 dedicated tests cover the emission path; (2) schema mismatch — resolve script validates at startup (NFR-REL-001); schema evolution requires `schema_version` bump.
- Rollback strategy: remove the `_write_upgrade_triage()` call from `_run_apply()` in `upgrade_consumer.py` and delete `upgrade_consumer_resolve.py` + `upgrade_consumer_resolve.sh` + the make target. All other files (schema, tests) are additive and harmless if left in place. The resolve make target is new so its absence from a consumer's `blueprint.generated.mk` (pre-upgrade) is a no-op.

## Deferred Proposals
- **Option B** — source-exists inference for blueprint-managed catch-all: Parked — trigger: after: issue-270 — safe only once Issue #270 ships explicit consumer ownership markers; conservative Option A catch-all is the correct first-release trade-off. Backlog: `proposal(issue-265-271-conflict-resolution-ux): Option B`.
- **Interactive TUI** (ncurses/lazygit-style conflict resolver): Rejected at PR closure — heavy external dependency, not portable across consumer environments; residual table is typically under 10 rows; explicitly rejected in ADR at design time.
- **HTML conflict report**: Rejected at PR closure — browser context-switch adds friction for a small residual table; CLI display is sufficient; explicitly rejected in ADR at design time.
- Issue #270 (explicit consumer ownership markers): separate work item already tracked in backlog.
- Issue #267 (`blueprint-upgrade-consumer-finalize` target): separate work item already tracked in backlog.
- Issue #269 (auto-clone upgrade source URL): separate work item already tracked in backlog.
