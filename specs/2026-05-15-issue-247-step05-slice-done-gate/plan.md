# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - All changes are additive prose edits to two existing files. No new scripts, no new Make targets, no new abstractions introduced.
- Anti-abstraction gate:
  - Direct prose additions to SKILL.md. No wrapper layer added.
- Integration-first testing gate:
  - N/A — docs-only change; no code integration boundaries.
- Positive-path filter/transform test gate:
  - N/A — no filter or payload-transform logic.
- Finding-to-test translation gate:
  - N/A — no reproducible deterministic pre-PR finding to automate; the incident that triggered this work item was a human-review gap, not a repeatable CI assertion.

## Delivery Slices

### Slice 1 — Update SKILL.md
Add Guardrails #13, #14, #15 to the existing Guardrails section. Update the "After All Slices Complete — Minimum validation bundle" table with two distinct HTTP-scope rows (both REQUIRED and non-optional). Promote the "HTTP route / query scope" special-case block to a numbered main workflow step "3. Local smoke gate (HTTP and UI-rendering scope)".

Verification: read SKILL.md to confirm all three guardrails are present, the table has the new rows, and the numbered smoke step exists before "After All Slices Complete". Run `make quality-hooks-fast` to confirm no regressions.

### Slice 2 — Create `references/implement_checklist.md`
Create `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md`. The file is listed as a `required_file` in `blueprint/contract.yaml` but absent on disk; this slice resolves the contract compliance gap. Content is derived from the SKILL.md changes in Slice 1 — a concise checklist summary of Guardrails #13, #14, #15 and the promoted smoke gate. SKILL.md is the normative source; the checklist MUST NOT introduce additional requirements.

Verification: confirm file exists at the correct path. Confirm content is consistent with the SKILL.md guardrail text. Run `make quality-hooks-fast`.

## Change Strategy
- Migration/rollout sequence: Slice 1 then Slice 2. No dependency inversion — both can be done in either order, but Slice 1 is the primary change.
- Backward compatibility policy: all changes are additive. No existing guardrail text is removed.
- Rollback plan: `git revert` the slice commit(s). Consumer repos receive the checklist update only on next blueprint upgrade; reverting in the blueprint repo before the next consumer upgrade prevents propagation.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no code changes.
- Contract checks: N/A — no API or event contract changes.
- Integration checks: N/A — no code integration boundaries.
- E2E checks: N/A — no runtime path affected.
- Governance/docs bundle: `make quality-hooks-run` · `make infra-validate`.

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
- Notes: No Make targets added or removed. No code changes to delivery or deployment paths. All listed targets are pre-existing; none are affected by this work item.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none beyond SKILL.md and the checklist file (they are the primary output of this work item, not documentation of an underlying change).
- Consumer docs updates: none.
- Mermaid diagrams updated: none — no diagram required (see architecture.md).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: N/A — this work item does not touch HTTP route handlers, query/filter logic, or new API endpoints.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: none — no operated code paths.
- Alerts/ownership: none.
- Runbook updates: none — SKILL.md is self-contained governance documentation; no external runbook references the specific guardrail text.

## Risks and Mitigations
- Risk 1: SKILL.md prose reword changes meaning → mitigation: spec ACs provide the normative reference; ADR records the intent; human review confirms alignment.
- Risk 2: `references/implement_checklist.md` content drifts from SKILL.md guardrails over time → mitigation: the checklist is a companion to the guardrails, not a canonical source; Option B (automated scanner) is available as a future safety net.
