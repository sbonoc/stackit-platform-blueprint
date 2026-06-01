# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - `_check_vgate_classification` is a pure function; no I/O, no state. Single responsibility.
  - Do not introduce abstraction layers beyond what is needed to wire the check into the existing validator pipeline.
- Anti-abstraction gate:
  - Use the same field-parsing pattern already established in `_check_ac_format` (regex line scan). No new base classes or helpers.
- Integration-first testing gate:
  - Write all test cases (T-101..T-114) in RED state before any implementation code is written.
  - Tests use in-memory spec.md text fixtures; no filesystem mocks beyond what the existing test suite uses.
- Positive-path filter/transform test gate:
  - Not applicable — this check is a classification validator, not a filter or payload-transform function.
- Finding-to-test translation gate:
  - Any pre-PR failure found via `make quality-sdd-check` on real specs MUST be translated into a test case; add to T-101..T-112 range.

## Delivery Slices

1. Slice 1 (RED — tests): Write `TestVgateClassification` class in `tests/infra/test_sdd_asset_checker.py` covering AC-001..AC-009 and AC-014 (T-101..T-109, T-114). Write `TestVgateTemplateFields` class in `tests/blueprint/test_quality_gating.py` covering AC-010..AC-013 (T-110..T-113). All tests fail (nothing implemented yet).

2. Slice 2 (GREEN — core check): Implement `_check_vgate_classification(spec_text, slug)` in `check_sdd_assets.py`. Add `_VGATE_GATE_SINCE` constant. Wire into `_validate_work_item_specs`. Tests T-101..T-109 turn green.

3. Slice 3 (GREEN — templates): Update `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` to seed the two new Implementation Stack Profile fields (`has-user-facing-flow`, `E2E gate classification`) with inline signal-list comments. Run `sync_consumer_init_sdd_assets.py` to mirror into consumer init template. Tests T-110..T-111 turn green.

4. Slice 4 (GREEN — governance docs): (a) Add mandatory Playwright E2E artifact rule (three MUSTs) to AGENTS.md testing and quality section — T-112 turns green. (b) Update `docs/blueprint/governance/spec_driven_development.md` and bootstrap mirror. (c) Update `.agents/skills/blueprint-sdd-step05-implement/SKILL.md`. (d) Verify `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` V-gate inference step is in place (already committed as part of intake; confirm it satisfies AC-013) — T-113 turns green.

5. Slice 5 (VERIFY): Run `make quality-sdd-check` on full catalog; confirm zero new violations. Confirm this work item's own spec passes (has-user-facing-flow: false, E2E gate classification: N/A). Capture evidence.

## Change Strategy
- Migration/rollout sequence: Forward-only guard (`_VGATE_GATE_SINCE`) ensures no pre-existing spec is affected. Spec template update seeds the fields for every new scaffold from this point forward. AGENTS.md update documents the rule for future authors.
- Backward compatibility policy: All pre-gate-date specs are exempt. No backfill required for existing consumer or blueprint specs.
- Rollback plan: Revert the `check_sdd_assets.py` commit; gate behavior is immediately restored to pre-change state. Template changes can be reverted independently without breaking the check.

## Validation Strategy (Shift-Left)
- Unit checks: pytest unit tests (T-101..T-114) covering all AC cases; run via `uv run python3 -m pytest tests/infra/test_sdd_asset_checker.py tests/blueprint/test_quality_gating.py`.
- Contract checks: `make quality-sdd-check` on full spec catalog — confirms no pre-existing spec is broken.
- Integration checks: none required (check is pure Python, no service boundaries).
- E2E checks: none (tooling change, no UI, no runtime components).

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
- Notes: Tooling-only change to `check_sdd_assets.py` and spec templates. No new make targets added; no app delivery workflow targets affected. All listed targets are pre-existing and unaffected by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `AGENTS.md` — add mandatory Playwright E2E artifact rule with all three MUSTs verbatim (FR-007).
  - `docs/blueprint/governance/spec_driven_development.md` — add the V-gate classification section describing the two spec fields (`has-user-facing-flow`, `E2E gate classification`), the binary rule (`automated` passes; `manual` is a violation when `has-user-facing-flow: true` + playwright profile), and the step01 shift-left inference mechanism.
  - `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/spec_driven_development.md` — mirror the above (bootstrap-rendered copy for new consumer scaffolds).
  - `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` — reference the V-gate enforcement in the implementation step so authors see the rule at code-writing time, not only at quality-gate time.
  - `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` — add V-gate inference step in the Discover phase (signal list + frontend-stack cross-check), V-gate cross-check in the Specify phase, and mandatory V-gate inference result line item in the Required Report Format. This is the primary shift-left control: the agent infers `has-user-facing-flow` from the issue at intake time rather than leaving the author to set it from a passive default.
- Consumer docs updates: none beyond template seeding (the consumer template comment carries the field definition).
- Mermaid diagrams updated: `architecture.md` contains two Mermaid diagrams — the V-gate decision tree (`flowchart TD`) and the end-to-end lifecycle diagram (`flowchart LR`) showing issue → intake inference → spec → quality gate enforcement.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or filter logic.
- Publish checklist:
  - include requirement/contract coverage (FR-001..FR-009, NFR-OBS-001/REL-001/OPS-001, AC-001..AC-014)
  - include key reviewer files (check_sdd_assets.py, spec templates, AGENTS.md, blueprint-sdd-step01-intake/SKILL.md)
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: Metric `sdd_vgate_manual_e2e_violation=<count>` emitted to stderr on violation. No new runtime logging or tracing.
- Alerts/ownership: platform-team owns `check_sdd_assets.py`; no new alert wiring required.
- Runbook updates: AGENTS.md updated with mandatory Playwright E2E artifact rule (the authoritative runbook surface for this check).

## Risks and Mitigations
- Risk R-1: `_VGATE_GATE_SINCE` set to the wrong date — pre-existing specs caught retroactively. Mitigation: set `_VGATE_GATE_SINCE` to the actual merge date of this PR; forward-only guard test (AC-006 / T-106) catches regressions.
- Risk R-2 (primary): Author silently sets `has-user-facing-flow: false` on a work item that has a user-facing flow, bypassing the gate. Mitigation: step01 intake inference (FR-009) pre-sets `true` when signals are found, forcing conscious override; signal-list template comment (FR-006) gives manual authors the same checklist; frontend-stack cross-check flags the contradiction; AGENTS.md rule (FR-007) surfaces the obligation at implementation time.
- Risk R-3: Consumer init template mirror drifts from consumer spec template after field addition. Mitigation: Slice 3 explicitly runs `sync_consumer_init_sdd_assets.py`; existing sync test coverage will catch drift.
