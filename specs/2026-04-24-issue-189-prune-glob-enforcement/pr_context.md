# PR Context

## Summary
- Work item: issue-189-prune-glob-enforcement (sbonoc/stackit-platform-blueprint#190)
- Objective: Detect and block blueprint-source files (`specs/YYYY-MM-DD-*`, `ADR-*.md`) that have been accidentally introduced into a generated-consumer repo during blueprint upgrade apply. Closes the detection gap identified in issue #189.
- Scope boundaries: Tooling-only change. No app onboarding surface, no Makefile targets, no infrastructure scripts. Only `upgrade_consumer_validate.py`, `upgrade_consumer_postcheck.py`, JSON schemas, `SKILL.md`, and `execution_model.md` are modified.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005
- NFRs covered: NFR-SEC-001 (no shell glob expansion; symlink escape check), NFR-OBS-001 (stderr per-violation line), NFR-REL-001 (skip on non-consumer mode; backward-compatible schema), NFR-OPS-001 (remediation hint in report)
- Contract surfaces changed: `upgrade_validate.schema.json` (additive: `prune_glob_check`), `upgrade_postcheck.schema.json` (additive: `prune_glob_violations`, `prune_glob_violation_count`)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer_validate.py` — `_scan_prune_glob_violations()` function and its integration into `main()`
  - `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — `prune_glob_violations` extraction and `blocked_reasons` extension
  - `tests/blueprint/test_upgrade_consumer.py` — unit + integration tests (REQ-010 through REQ-013)
  - `tests/blueprint/test_upgrade_postcheck.py` — integration test (REQ-014)
- High-risk files:
  - `scripts/lib/blueprint/upgrade_consumer_validate.py` — all schema additions are additive; stale validate reports (no `prune_glob_check` key) are handled gracefully via `.get()` defaults

## Validation Evidence
- Required commands executed: pytest (unit + integration), docs sync, quality-docs-check-changed, quality-hooks-fast
  - `python3 -m pytest tests/blueprint/ -v -k "prune_glob"` — 7 tests, all PASSED
  - `python3 -m pytest tests/blueprint/ -v -q` — 365 passed, 6 pre-existing failures (unrelated to this work item; caused by missing `.spec-kit/policy-mapping.md.tmpl` template, confirmed failing on clean main)
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py` — 1 updated (execution_model.md bootstrap template), 0 errors
  - `make quality-docs-check-changed` — passed (test pyramid ratios within bounds)
  - `make quality-hooks-fast` — passed
- Result summary: All 5 new prune-glob tests green; 2 pre-existing quality contract tests for prune globs also pass (covering contract field presence and ownership matrix documentation); no regressions in existing 360 tests.
- Artifact references:
  - `artifacts/blueprint/upgrade_validate.json` — will contain `prune_glob_check` after this change
  - `artifacts/blueprint/upgrade_postcheck.json` — will contain `prune_glob_violations` after this change

## Risk and Rollback
- Main risks: low — performance and false-positive risks are both mitigated by design
  - Low: `rglob()` on large repos. Mitigated — only 2 glob patterns; both are non-recursive in practical use (one matches top-level `specs/`, one matches `docs/blueprint/architecture/decisions/`).
  - Low: False positives if a legitimate consumer file accidentally matches a prune glob. Mitigated — the patterns are highly specific and carry the same risk in `blueprint-init-repo` today; no change in pattern surface.
  - None: Schema changes are additive (not in `required` arrays); existing postcheck + validate consumers are unaffected.
- Rollback strategy: Revert `upgrade_consumer_validate.py` and `upgrade_consumer_postcheck.py` changes. The JSON schemas remain valid with or without the new fields. No migration required; stale reports without `prune_glob_check` are treated as zero violations.

## Deferred Proposals
- Proposal 1 (not implemented): Standalone `make blueprint-check-prune-globs` target for ad-hoc consumer lifecycle checks outside the upgrade flow.
- Proposal 2 (not implemented): Surface prune glob violations in `upgrade_summary.md` human-readable report alongside merge-required entries.
