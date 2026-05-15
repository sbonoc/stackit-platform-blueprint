# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.
- **Gate status: OPEN — `SPEC_READY: true` confirmed.**

## Constitution Gates (Pre-Implementation)
- Simplicity gate: All changes are additive prose edits to two existing files and one new file. No new scripts, no new Make targets, no new abstractions introduced.
- Anti-abstraction gate: Direct prose additions to SKILL.md and AGENTS.md. No wrapper layer added.
- Integration-first testing gate: N/A — docs-only change; no code integration boundaries.
- Positive-path filter/transform test gate: N/A — no filter or payload-transform logic.
- Finding-to-test translation gate: N/A — no reproducible deterministic pre-PR finding to automate; the incident that triggered this work item was a human-review gap, not a repeatable CI assertion.

## Parallel-Safe Execution Model

This work item has **two parallel phases**. Phase 1 contains two slices that are
file-collision-free and can be executed concurrently by independent subagents.
Phase 2 has a single slice that depends on Phase 1A (content derives from SKILL.md).

```
Phase 1 (parallel — no file overlap):
  ├── Slice 1A — SKILL.md only   (T-001–T-005)
  └── Slice 1B — AGENTS.md only  (T-007–T-010)

Phase 2 (sequential — after Slice 1A completes):
  └── Slice 2  — implement_checklist.md  (T-006)
               depends on: Slice 1A
               file: new file, no collision risk
```

**Collision-free guarantee**: Slice 1A and Slice 1B touch different files
(`SKILL.md` vs `AGENTS.md`). They share no write surface. Slice 2 creates a new
file; it must wait for Slice 1A to be committed so the checklist content accurately
reflects the final SKILL.md guardrail text.

## Delivery Slices

### Slice 1A — Update SKILL.md (Phase 1, parallel-safe)

**Owner**: agent (single-agent model; distributable to a subagent)
**Input**: `spec.md` FR-001–FR-005 + AC-001–AC-005; current SKILL.md
**Output**: SKILL.md with Guardrails #13, #14, #15; updated bundle table; numbered smoke step 3
**Files touched**: `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` only
**Blocks**: Slice 2

Tasks: T-001, T-002, T-003, T-004, T-005

**Changes**:
1. Add Guardrail #13 (API response field coverage) after existing #12 — exact normative text from FR-001 / AC-001.
2. Add Guardrail #14 (Vue component test per rendering branch) after #13 — exact normative text from FR-002 / AC-002.
3. Add Guardrail #15 (Pact consumer + provider) after #14 — exact normative text from FR-003 / AC-003.
4. Update "After All Slices Complete — Minimum validation bundle" table: add REQUIRED row for HTTP scope and REQUIRED row for HTTP+UI rendering scope — both non-optional (FR-004 / AC-004).
5. Promote local smoke gate: add numbered main workflow step "3. Local smoke gate (HTTP and UI-rendering scope)" before "After All Slices Complete"; remove the now-duplicated HTTP block from "Special cases" (FR-005 / AC-005).

**Verification**: Read SKILL.md to confirm all three guardrails are present at #13–#15, table has two new REQUIRED HTTP rows, and step 3 exists before "After All Slices Complete". Run `make quality-hooks-fast`.

### Slice 1B — Update AGENTS.md (Phase 1, parallel-safe)

**Owner**: agent (single-agent model; distributable to a subagent)
**Input**: `spec.md` FR-007–FR-010 + AC-008–AC-011; current AGENTS.md
**Output**: AGENTS.md with four additive prose additions across four sections
**Files touched**: `AGENTS.md` only
**Blocked by**: nothing (independent of Slice 1A)
**Blocks**: nothing (Slice 2 depends on Slice 1A, not 1B)

Tasks: T-007, T-008, T-009, T-010

**Changes** (all additive — no existing text altered):
1. § Cross-Cutting Guardrails: add field-coverage gate requirement (canonical normative home for Guardrail #13). Extends the existing "Positive-path filter/payload-transform test coverage" bullet. (FR-007 / AC-008)
2. § Testing and Quality Ratios: add per-SFC rendering-branch coverage rule (canonical normative home for Guardrail #14; audit confirmed this rule does not currently exist in AGENTS.md). (FR-008 / AC-009)
3. § Contract Testing Standards: add same-repo Pact provider timing requirement (canonical normative home for Guardrail #15 same-repo clause). (FR-009 / AC-010)
4. § Minimum Validation Bundles: add two HTTP-scope entries — "HTTP route / filter / query scope" and "HTTP route + UI rendering scope" — resolving drift with § Cross-Cutting Guardrails. (FR-010 / AC-011)

**NFR constraint**: All four additions MUST use MUST/MUST NOT normative language and MUST follow the existing section format (NFR-MAINT-001, NFR-COMPAT-001).

**Verification**: Read each updated AGENTS.md section to confirm the four additions are present and consistent with the corresponding SKILL.md guardrails. Run `make quality-hooks-fast`.

### Slice 2 — Create `references/implement_checklist.md` (Phase 2, sequential)

**Owner**: agent (single-agent model)
**Input**: Slice 1A SKILL.md (committed) — Guardrails #13, #14, #15 and the smoke step text
**Output**: `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` created
**Files touched**: new file only — no collision risk
**Blocked by**: Slice 1A (content is derived from the final SKILL.md guardrail text)

Tasks: T-006

**Change**: Create the checklist file. The file is listed as a `required_file` in
`blueprint/contract.yaml` but absent on disk (contract compliance gap). Content
MUST be a concise checklist summary of Guardrails #13, #14, #15 and the promoted
smoke gate. SKILL.md is the normative source; the checklist MUST NOT introduce
requirements beyond SKILL.md.

**Verification**: Confirm file exists at the correct path. Confirm content is consistent with the SKILL.md guardrail text and introduces no additional requirements. Run `make quality-hooks-fast`.

## Dependency Map

```
FR-001 → T-001 (Guardrail #13 in SKILL.md)   ┐
FR-002 → T-002 (Guardrail #14 in SKILL.md)   │ Slice 1A ──► Slice 2 (T-006)
FR-003 → T-003 (Guardrail #15 in SKILL.md)   │
FR-004 → T-004 (bundle table update)          │
FR-005 → T-005 (numbered smoke step)          ┘

FR-007 → T-007 (AGENTS.md § Cross-Cutting Guardrails) ┐
FR-008 → T-008 (AGENTS.md § Testing Quality Ratios)   │ Slice 1B (independent)
FR-009 → T-009 (AGENTS.md § Contract Testing)         │
FR-010 → T-010 (AGENTS.md § Minimum Validation)       ┘

FR-006 → T-006 (implement_checklist.md)   Slice 2 — after Slice 1A
```

## Change Strategy
- Migration/rollout sequence: Phase 1 (1A + 1B parallel) → Phase 2. No dependency inversion.
- Backward compatibility policy: all changes are additive. No existing guardrail text is removed.
- Rollback plan: `git revert` the slice commit(s). Consumer repos receive the checklist update only on next blueprint upgrade; reverting in the blueprint repo before the next consumer upgrade prevents propagation.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no code changes.
- Contract checks: N/A — no API or event contract changes.
- Integration checks: N/A — no code integration boundaries.
- E2E checks: N/A — no runtime path affected.
- Per-slice fast check: `make quality-hooks-fast` after each slice.
- Governance/docs bundle: `make quality-hooks-run` · `make infra-validate` (T-201, post all slices).

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
- Risk 3: Slice 1B (AGENTS.md) and Slice 1A (SKILL.md) introduce inconsistent wording → mitigation: spec FRs define the canonical text for each; both slices reference the same spec. After both slices complete, a consistency check against the spec is required before merging.
