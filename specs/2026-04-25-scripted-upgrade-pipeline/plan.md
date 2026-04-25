# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Each new script (resolver, coverage fetcher, mirror sync, doc checker, residual reporter) must be independently testable with fixture inputs; no shared global state between stages.
  - The pipeline entry wrapper orchestrates by invoking existing and new scripts sequentially — no new framework or abstraction layer.
- Anti-abstraction gate:
  - Use Python stdlib only (no third-party libraries beyond what is already in the repo); bash for the entry wrapper.
  - No wrapper layer around existing make targets — invoke them directly via subprocess/shell.
- Integration-first testing gate:
  - Contract resolver tests use representative fixture conflict JSON inputs before implementation details.
  - Coverage gap detection tests use a minimal fixture consumer directory structure.
- Positive-path filter/transform test gate:
  - Contract resolver must have at least one unit test asserting that `name` and `repo_mode` from consumer input are preserved (not overwritten by source content) — AC-002.
  - Empty-result-only assertions do not satisfy this gate.
- Finding-to-test translation gate:
  - Each observed failure mode (F-001–F-010) that is addressed by a new script stage must have a corresponding unit test asserting the fix. Translate into failing tests first, then implement the fix.

## Delivery Slices

1. **Slice 1 — Pre-flight validation (Stage 1)**
   - FR-001, FR-002, FR-003
   - Write `scripts/bin/blueprint/upgrade_consumer.sh` stub with Stage 1 logic only.
   - Test: unit test for each pre-flight abort condition (dirty working tree, unresolved ref, bad contract).
   - Red→green: write failing tests for each condition, then implement.

2. **Slice 2 — Contract resolver (Stage 3)**
   - FR-005, FR-006, FR-007, FR-008
   - Write `scripts/lib/blueprint/resolve_contract_upgrade.py`.
   - Test: fixture conflict JSON with known identity fields, required_files (consumer-added existing, consumer-added missing, blueprint entries), and prune globs (matching and non-matching paths).
   - Red→green: fixture-driven unit tests assert preserved identity, merged required_files, dropped prune globs, decision JSON contents.
   - AC-002 satisfied here.

3. **Slice 3 — Coverage gap detection and file fetch (Stage 5)**
   - FR-009, FR-010, NFR-SEC-001
   - Write `scripts/lib/blueprint/upgrade_coverage_fetch.py`.
   - Test: fixture consumer disk state with one contract-referenced file absent; assert file is fetched via local git `git show`; assert no subprocess call to any HTTP URL.
   - Red→green: test with mocked `git show` subprocess, then integration test against a minimal fixture source repo.
   - AC-003 satisfied here.

4. **Slice 4 — Bootstrap template mirror sync (Stage 6)**
   - FR-011
   - Write `scripts/lib/blueprint/upgrade_mirror_sync.py`.
   - Test: fixture workspace path that has a corresponding mirror; assert mirror is overwritten when workspace file is modified; assert no-op when mirror does not exist.
   - Red→green: unit tests with temp directory fixture.

5. **Slice 5 — Make target validation for new/changed docs (Stage 7)**
   - FR-012
   - Write `scripts/lib/blueprint/upgrade_doc_target_check.py`.
   - Test: fixture markdown file with `make known-target` (present in `.PHONY`) and `make missing-target` (absent); assert warning emitted for missing-target only; assert stage does not abort (exit 0 with warnings).
   - Red→green: unit tests with temp mk file fixture.

6. **Slice 6 — Residual report (Stage 10)**
   - FR-015, FR-016, FR-017, FR-018, FR-019 (independent callability preserved via separate targets)
   - Write `scripts/lib/blueprint/upgrade_residual_report.py`.
   - Test: fixture JSON inputs from Stages 3, 5, 7 + reconcile report consumer-owned list; assert every item in rendered Markdown has a prescribed action matching the templates in FR-016.
   - Red→green: unit tests with fixture JSON inputs.
   - Also verify independent callability of existing targets (no regression).

7. **Slice 7 — Pipeline wiring + Makefile target**
   - FR-004, FR-013, FR-014, FR-019, NFR-REL-001, NFR-OPS-001, NFR-OBS-001
   - Complete `scripts/bin/blueprint/upgrade_consumer.sh`: wire all 10 stages in sequence; emit stage-labeled progress lines (NFR-OBS-001); guarantee Stage 10 execution even on partial failure; propagate `BLUEPRINT_UPGRADE_ALLOW_DELETE`.
   - Add `blueprint-upgrade-consumer` target to `make/blueprint.mk`; add `make help` entry.
   - Update `SKILL.md` to 6-step flow.
   - Test: idempotency test — run twice on clean fixture, assert no file changes and exit 0 on second run (NFR-REL-001).

8. **Slice 8 — Docs sync + validation**
   - Generated reference docs sync, `make infra-validate`, `make quality-hooks-run`.
   - Verify AC-001, AC-004, AC-005, AC-006.
   - Run full test suite; attach evidence to `pr_context.md`.

## Change Strategy
- Migration/rollout sequence: all existing individual make targets remain unchanged; `blueprint-upgrade-consumer` is a new additive target. No consumer migration needed.
- Backward compatibility policy: existing targets (`blueprint-upgrade-consumer-apply`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-preflight`, `blueprint-upgrade-consumer-postcheck`, `blueprint-upgrade-fresh-env-gate`) must pass their existing tests unmodified (AC-006).
- Rollback plan: the new entry wrapper and new scripts are additive; removing the `blueprint-upgrade-consumer` target and new scripts is a complete rollback with no effect on existing targets.

## Validation Strategy (Shift-Left)
- Unit checks: pytest for each new script (resolver, coverage fetcher, mirror sync, doc checker, residual reporter) with fixture inputs; aim for per-stage isolation.
- Contract checks: existing `infra-contract-test-fast` must pass without modification (AC-006).
- Integration checks: end-to-end test against a minimal fixture consumer directory exercising the full pipeline (AC-003); idempotency verification (NFR-REL-001).
- E2E checks: existing `blueprint-upgrade-fresh-env-gate` exercises the apply+delete path (AC-004); no new E2E infrastructure required.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: this work item adds Python scripts, shell orchestration, and Makefile targets only; no app delivery, build, or runtime changes.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md` (ADR, already drafted as proposed); `references/manual_merge_checklist.md` updated to reference new residual report format.
- Consumer docs updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` reduced from ~30-step runbook to 6-step flow (run command, read report, apply prescribed actions, re-run hooks, commit, PR).
- Mermaid diagrams updated: architecture.md pipeline flowchart.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or new API endpoints introduced.
- Publish checklist:
  - include requirement/contract coverage (all FR/NFR/AC traced)
  - include key reviewer files (`resolve_contract_upgrade.py`, `upgrade_consumer.sh`, test fixtures)
  - include validation evidence (pytest output, `make quality-hooks-fast` result)
  - include rollback notes (additive only; rollback = remove new target + scripts)

## Operational Readiness
- Logging/metrics/traces: stage-labeled progress lines to stdout (NFR-OBS-001); JSON decision artifacts per stage; residual report always emitted.
- Alerts/ownership: no runtime alerting; gate chain exit code surfaces in make output.
- Runbook updates: `SKILL.md` reduced to 6-step flow; `references/manual_merge_checklist.md` updated.

## Risks and Mitigations
- Risk 1: Q-1 (Stage 5 fetch scope) and Q-2 (ALLOW_DELETE default) are open pending user decision → implementation of FR-004 and FR-010 is gated on those answers; all other slices can proceed independently.
- Risk 2: contract resolver fixture coverage may not include all production conflict JSON shapes → mitigation: collect real conflict JSON from the dhe-marketplace upgrade run as an additional fixture input.
