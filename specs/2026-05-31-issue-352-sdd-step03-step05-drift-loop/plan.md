# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: one new check function in `check_sdd_assets.py`; SKILL.md edits are text-only; no new module hierarchy or authoring tooling
  - One new check function in `check_sdd_assets.py`; no new module hierarchy.
  - SKILL.md edits are text-only; no new authoring tooling.
- Anti-abstraction gate: reuse `_PHASES` enum and existing `[METRIC]` log format; no inline re-declarations or structured metric envelope
  - Reuse the existing `_PHASES` enum constant from `scripts/lib/sdd/c7_emit.py` rather than re-declaring `"spec-complete"` inline.
  - Reuse the existing `[METRIC] name=...` log format rather than introducing a structured JSON metric envelope.
- Integration-first testing gate: new check exercised against fixture JSONL files in a tmp work-item directory; no live blueprint fixture mutated
  - The new check is exercised against fixture JSONL files in a tmp work-item directory, mirroring the existing `test_sdd_asset_checker.py` patterns. No live blueprint fixture is mutated.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic in this work item.
- Finding-to-test translation gate: any deterministic pre-PR failure MUST become a failing automated test before the fix lands; exceptions documented in publish artifacts
  - Any deterministic failure observed during pre-PR `make quality-hooks-fast` MUST be translated into a failing automated test before the fix lands. Documented in this plan's Validation Strategy.

## Delivery Slices

1. **Slice 1 — AGENTS.md governance amendment (FR-001 text-only)**
   Add the mandatory-gate clause and exempt-track list to `§ Mandatory Workflow`. Cross-reference the new check in `§ SDD Readiness Gate (Mandatory Before Implementation)`. No code path changes — text contract only. Red: add a test in `tests/blueprint/test_quality_gating.py` (or equivalent) asserting AGENTS.md contains the literal phrase `mandatory gate` paired with `blueprint-sdd-step03-spec-complete` and the exempt tokens `upgrade`, `chore-with-no-specs` (AC-010). Green: amend AGENTS.md. Commit + push.

2. **Slice 2 — Step03 SKILL.md AC authoring rule (FR-004) + step01 shift-left + scaffold templates (FR-012)**
   Add the AC authoring section to `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` requiring the canonical `which MUST assert ...` form and the spec-complete checklist item that rejects label-only ACs. Mirror the same canonical-form guidance into `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` Discover-phase authoring guidance (FR-012). Replace the legacy `AC-001 MUST be objectively testable.` placeholder in both `.spec-kit/templates/blueprint/spec.md` and `.spec-kit/templates/consumer/spec.md` with a canonical-form seeded example so the scaffold itself teaches the pattern. Red: pytest cases asserting (a) both the canonical phrase and the rejection rule appear in step03 SKILL.md (AC-006), AND (b) the canonical-form substrings appear in step01 SKILL.md + both scaffold templates (AC-011). Green: edit all four files. Commit + push.

3. **Slice 3 — Step05 SKILL.md four guardrails + per-profile table (FR-005..FR-010)**
   Add four numbered guardrails (spec-value regression, union types, SSOT enums, mandatory rendered-output) and the per-profile examples table to `.agents/skills/blueprint-sdd-step05-implement/SKILL.md`. Weave FR-009 Vitest Browser Mode satisfaction + Playwright escalation rule into the FR-008 guardrail body. Red: pytest cases asserting the four guardrails exist and the per-profile table contains TS/Python/Kotlin/Go rows (AC-007, AC-008, AC-009). Green: edit SKILL.md. Commit + push.

4. **Slice 4 — `check_sdd_assets.py` FR-002 enforcement + FR-003 exemptions + NFR-OBS-001 metric**
   Add `_check_step03_complete_event(work_item_dir, spec_data)`. Read `artifacts/c7/<slug>.jsonl`. Skip when `SPEC_READY_EXCEPTION == "upgrade"` or no `specs/` dir (FR-003). Skip when `BLUEPRINT_SDD_C7_EMIT=0` opt-out scenario matches an exempt track (otherwise FAIL). On missing `spec-complete` event for the ticket, emit the deterministic error and the `[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>` line, return failure. Red: extend `tests/infra/test_sdd_asset_checker.py` with fixture cases for AC-001..AC-005 (happy path, missing event, upgrade exemption, chore-no-specs exemption, opt-out event does not satisfy gate). Green: implement the function and wire it into the existing implementation-ready validator path. Commit + push.

5. **Slice 5 — Forward-only application constant (FR-011) + documentation sync**
   Add the merge-date constant to `check_sdd_assets.py` (initial value `2026-05-31` — updated to actual merge date in the pre-merge commit). Update the AGENTS.md `§ Generated SDD Policy Snapshot` if the snapshot generator surfaces any of the new fields. Run `make sdd-policy-snapshot` (if it exists) or the equivalent regeneration target. Commit + push.

## Change Strategy
- Migration/rollout sequence: governance text first (slice 1) so the policy is documented before machine enforcement lands; SKILL.md authoring rules next (slices 2–3) so the human-facing instructions match the policy; machine enforcement last (slice 4) so contributors see the new rule documented before it can block their work. Slice 5 grandfathers in-flight work.
- Backward compatibility policy: existing in-flight work items are grandfathered via FR-011's merge-date constant. The first work item to land after merge will need a `spec-complete` C7 event in its JSONL — this is already produced by step03 since the ADR-issue-347 work item shipped, so no human action is required for compliant contributors.
- Rollback plan: clean revert of this work item's commits restores the prior governance text, SKILL.md content, and validator behaviour. No data migration; the JSONL files already in place remain valid (no schema change).

## Validation Strategy (Shift-Left)
- Unit checks: pytest cases in `tests/infra/test_sdd_asset_checker.py` and `tests/blueprint/test_quality_gating.py` (or the closest existing module — confirm path during slice 1) cover AC-001..AC-011.
- Contract checks: none (no new contracts).
- Integration checks: end-to-end run of `make quality-sdd-check` against this work item's own `specs/` directory MUST pass after slice 5 lands.
- E2E checks: N/A — no UI surface.

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
- Notes: governance + SDD-check changes; no make-target additions affect app delivery workflows.

## Documentation Plan (Document Phase)
- Blueprint docs updates: AGENTS.md `§ Mandatory Workflow`; `.agents/skills/blueprint-sdd-step01-intake/SKILL.md`; `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md`; `.agents/skills/blueprint-sdd-step05-implement/SKILL.md`; `.spec-kit/templates/blueprint/spec.md`; `.spec-kit/templates/consumer/spec.md`; `CLAUDE.md` if the skill table caption requires reflection (Slice 1 verifies).
- Consumer docs updates: none (skill propagation is implicit; no consumer-facing template change).
- Mermaid diagrams updated: ADR diagram only (the SDD lifecycle flow).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — this work item does not touch HTTP route handlers, query/filter logic, or API endpoints. The local-smoke gate is not applicable.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `[METRIC] name=sdd_step03_missing_spec_complete value=1 work_item=<slug>` emitted by `check_sdd_assets.py` on FR-002 violation (NFR-OBS-001). Visible in CI job logs alongside the existing `sdd_exception_gate_total` metric.
- Alerts/ownership: none — the failure surface is the existing `make quality-sdd-check` CI status check; platform-team owns the runbook.
- Runbook updates: `docs/blueprint/governance/sdd_execution_guide.md` (if present — confirm during slice 5) gains a short subsection on the new metric and the canonical fix path (run `/blueprint-sdd-step03-spec-complete` to record the missing event, OR set the appropriate `SPEC_READY_EXCEPTION` value).

## Risks and Mitigations
- Risk 1 → mitigation: A contributor running `BLUEPRINT_SDD_C7_EMIT=0` on a full-SDD work item will hit the gate at PR-CI time. Mitigation: the failure message names the canonical fix (run step03 to emit the event, or set the appropriate exception value). Documented in `pr_context.md` Validation Evidence.
- Risk 2 → mitigation: Per-profile examples table drifts as new stack profiles are added. Mitigation: introduce-a-profile is documented as "update the per-profile examples table in the same commit"; the table sits adjacent to the existing `## Stack-specific test isolation` section so reviewers see both.
- Risk 3 → mitigation: AC authoring rule (FR-004) is human-enforced and may be ignored in early adoption. Mitigation: ADR D-7 explicitly documents this as a deliberate scope choice; revisit with a machine check if adoption is poor after ≥5 work items.
