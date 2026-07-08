# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Implementation is confined to one new internal function + one intercept in `_apply_entries`; no new public API, no new CLI flag.
- Anti-abstraction gate: YAML parsing uses `yaml.safe_load` directly; no wrapper or strategy pattern. The merge is a targeted special-case for `.pre-commit-config.yaml` only.
- Integration-first testing gate: Fixture-driven unit tests (T-101–T-108) cover all acceptance criteria before implementation code is written.
- Positive-path filter/transform test gate: T-101 asserts that a consumer hook ID matching the fixture returns that hook in the merged output. T-103 asserts multiple hooks are all present. T-107 asserts no duplication on a second pass.
- Finding-to-test translation gate: The issue's reproduction case (consumer hook silently dropped on upgrade) is directly translated into T-101, T-106. Implementation fix turns these green.

## Delivery Slices
1. **Slice 1 — Red tests:** Add test fixtures and failing unit tests T-101–T-108 in `tests/blueprint/test_upgrade_precommit_merge.py` and `tests/blueprint/fixtures/upgrade_precommit/`.
2. **Slice 2 — Implementation:** Add `PrecommitYamlParseError`, `_yaml_merge_precommit_hooks`, intercept in `_apply_entries`, preserved-hooks section in `_write_summary`. All T-101–T-108 turn green.
3. **Slice 3 — Classification check:** Verify T-106 (plan step `_classify_entries` produces `merge-required` for consumer-diverged file). No code change expected — existing divergence-from-baseline path already produces this; test makes it an explicit regression guard.
4. **Slice 4 — Quality gates:** Run full test suite, `make quality-sdd-check`, pre-commit.

## Change Strategy
- Migration/rollout sequence: No consumer migration needed. On next `make blueprint-upgrade-consumer` run against a newer blueprint tag, the YAML-aware path activates automatically for `.pre-commit-config.yaml` entries with `ACTION_MERGE_REQUIRED`.
- Backward compatibility policy: Fully backward compatible. When no consumer-only hooks exist the function writes the source content (same as the existing `ACTION_UPDATE` path). Parse failure falls back to `_three_way_merge` (same as before).
- Rollback plan: Revert the merge-intercept in `_apply_entries`; the engine reverts to the existing 3-way merge behaviour. Consumer must manually re-add dropped hooks.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/blueprint/test_upgrade_precommit_merge.py -q` — 8 tests.
- Contract checks: N/A — no API or event contract changes.
- Integration checks: N/A — the upgrade engine is tested via unit tests with fixture files; no running cluster needed.
- E2E checks: N/A — `has-user-facing-flow: false`.

## App Onboarding Contract (Normative)
- Required minimum make targets: no change
- App onboarding impact: no-impact

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/platform/architecture/decisions/ADR-issue-346-upgrade-precommit-clobber.md` (already drafted).
- Consumer docs updates: none — upgrade pipeline output is self-documenting via `upgrade_summary.md`.
- Mermaid diagrams updated: flowchart in ADR (no separate diagram file needed).
- Docs validation commands: `make docs-build`, `make docs-smoke`.

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — no HTTP route, query/filter, or new API endpoint changes.
- Publish checklist: include requirement/contract coverage, key reviewer files, validation evidence (test run output), rollback notes.

## Operational Readiness
- Logging/metrics/traces: `NFR-OBS-001` — preserved hook IDs logged at `log_info` during upgrade apply; parse fallback WARNING to stderr.
- Alerts/ownership: none — upgrade is a developer-facing CLI tool; no production alert surface.
- Runbook updates: ADR serves as the operator reference.

## Risks and Mitigations
- Risk 1: YAML round-trip via `safe_load` + `dump` may alter ordering of non-hook YAML keys (e.g. repo-level `rev`/`hooks` ordering). Mitigation: source content is written verbatim as a string; only the consumer-only hook blocks are re-serialised via `yaml.dump`. The source file body is never round-tripped through YAML — only the target consumer-only hooks are extracted and re-emitted. This preserves the blueprint file exactly as authored.
- Risk 2: A consumer might add a hook with the same `id` as a future blueprint hook, causing a silent collision. Mitigation: duplicate-id guard in `_yaml_merge_precommit_hooks` — if a consumer hook ID already exists in the source, it is not appended (the source version wins). NFR-REL-001 idempotency test (T-107) covers this scenario.
