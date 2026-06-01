# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1: Consumer-init template drift — `.spec-kit/templates/consumer/spec.md` was updated in slice 2 (canonical AC placeholder) but its mirror at `scripts/templates/consumer/init/.spec-kit/templates/consumer/spec.md.tmpl` was not synced in the same commit. Caught by the pre-push `blueprint-test-unit` hook (`test_consumer_init_sdd_assets_in_sync`). Fixed in a follow-up commit via `sync_consumer_init_sdd_assets.py`.

## Observability and Diagnostics Changes

- New metric emitted to stderr by `scripts/bin/quality/check_sdd_assets.py` when the spec-complete gate fails: `[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>`. Operators can grep CI logs for this token to identify contributors who skipped step03.
- The metric is text-output only — not wired to Grafana or PagerDuty alerting. This is intentional: the gate is a pre-merge block, not a runtime alarm. Wiring to alerting is deferred.
- No new log lines added to application code (this is a governance-only change).
- No traces added (no HTTP boundary crossed).

## Architecture and Code Quality Compliance

- SOLID: `_check_step03_complete_event()` is a single-responsibility function with a clear input/output contract. It does not mutate caller state.
- Clean Architecture: function is a pure validator — reads from filesystem, returns `list[Violation]`, never writes. Side-effect (metric print to stderr) is explicit and isolated.
- No new dependencies introduced; `json` stdlib already imported.
- Test pyramid (74 tests total): `test_sdd_asset_checker.py` adds 5 new integration-style tests (AC-001..AC-005) using temp dirs; `test_quality_gating.py` adds 19 new unit tests (AC-006..AC-011). All pass. Pyramid ratios unchanged (within bounds).
- No stale TODOs, dead code, or placeholder text in implementation files.
- Documentation drift check: `quality-docs-check-changed` and `quality-bootstrap-template-drift` both pass after template mirrors were synced.
- CI template alignment: no CI pipeline files changed; existing gates remain unchanged.
- Skill runbooks: step03 and step01 SKILL.md updated; step05 SKILL.md updated; all seven step skills retain the required structural sections (Guardrails, Workflow, Required Report Format).

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI surface; this is a pure governance/tooling change
- [x] SC 2.1.1 (Keyboard): N/A — no UI surface
- [x] SC 2.4.7 (Focus Visible): N/A — no UI surface
- [x] SC 1.4.1 (Use of Color): N/A — no UI surface
- [x] SC 3.3.1 (Error Identification): N/A — no UI surface
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI surface (per NFR-A11Y-001: governance change with no UI surface)

## Proposals Only (Not Implemented)

- Proposal 1 (deferred): Machine-enforced AC format scanner — FR-004 enforces the canonical AC form `AC-NNN [description] — verified by T-N, which MUST assert <exact condition>.` via SKILL.md guidance and human review at step03. A machine-readable parser in `check_sdd_assets.py` that rejects label-only ACs was explicitly deferred (ADR D-7): the cognitive overhead is low and the SKILL.md gate is adequate for now. A regex scanner could be added as a follow-on chore.
- Proposal 2 (deferred): Metric wiring to alerting — `sdd_step03_missing_spec_complete` is emitted to stderr only. Wiring to a Grafana dashboard or PagerDuty alert is not implemented — the gate is a blocking pre-merge check and does not need runtime alerting. Deferred as low-priority operational improvement.
