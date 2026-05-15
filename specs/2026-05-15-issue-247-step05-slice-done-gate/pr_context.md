# PR Context

## Summary

Closes four structural gaps in the `blueprint-sdd-step05-implement` skill's per-slice definition of done that allowed a spec-compliant, green-test implementation to ship with six missing API response fields visible and wrong in the browser. Three new guardrails (#13 API field coverage, #14 Vue branch coverage, #15 Pact same-repo provider) are added to SKILL.md; the local smoke gate is promoted from "Special cases" to numbered main workflow step 3; the minimum validation bundle table gains two distinct REQUIRED HTTP rows; `references/implement_checklist.md` is created (contract compliance gap — required by `blueprint/contract.yaml` but absent on disk). AGENTS.md receives four additive additions providing the canonical normative home for each new guardrail (FR-007–FR-010, mandated by § Assistant Interoperability). Two blueprint governance docs (`spec_driven_development.md`, `sdd_execution_guide.md`) and their bootstrap template mirrors are updated to reflect the new gates. All changes are additive — no existing guardrails (1–12) are altered.

## Requirement Coverage

| Requirement | Implementation path | Test / verification evidence |
|---|---|---|
| FR-001 — Guardrail #13 in SKILL.md | `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` guardrail #13 (lines 152–160) | AC-001: human review confirms exact text; FR-007 → AGENTS.md canonical normative home |
| FR-002 — Guardrail #14 in SKILL.md | SKILL.md guardrail #14 (lines 161–166) | AC-002: human review; FR-008 → AGENTS.md canonical normative home |
| FR-003 — Guardrail #15 in SKILL.md | SKILL.md guardrail #15 (lines 167–181) | AC-003: human review; FR-009 → AGENTS.md canonical normative home |
| FR-004 — Bundle table two REQUIRED HTTP rows | SKILL.md § After All Slices Complete bundle table | AC-004: human review confirms two REQUIRED HTTP rows |
| FR-005 — Numbered smoke step 3 | SKILL.md `## 3. Local smoke gate` section before § After All Slices Complete | AC-005: human review confirms step 3 exists, marked REQUIRED, PR MUST NOT open until passes |
| FR-006 — implement_checklist.md on disk | `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` updated | AC-006: file exists; content consistent with SKILL.md; introduces no extra requirements |
| FR-007 — AGENTS.md § Cross-Cutting Guardrails | `AGENTS.md` field-coverage gate bullet (new) | AC-008: human review; `make quality-hooks-run` clean |
| FR-008 — AGENTS.md § Testing and Quality Ratios | `AGENTS.md` Vue SFC rendering-branch coverage rule (new) | AC-009: human review |
| FR-009 — AGENTS.md § Contract Testing Standards | `AGENTS.md` same-repo Pact provider timing (new) | AC-010: human review |
| FR-010 — AGENTS.md § Minimum Validation Bundles | `AGENTS.md` two HTTP-scope entries (new) | AC-011: human review confirms two HTTP entries present |
| NFR-MAINT-001 — additive-only guardrail format | SKILL.md diff — no deletions in guardrails 1–12; AGENTS.md additions use MUST/MUST NOT | PR diff review |
| NFR-COMPAT-001 — additive-only changes | SKILL.md diff — additions only; AGENTS.md diff — additions only | PR diff review |
| NFR-A11Y-001 — N/A no UI | — | Declared in spec.md; accessibility gate all N/A in hardening_review.md |
| AC-007 — make quality-hooks-run passes | Post-all-slices validation bundle | `make infra-validate` PASS; `make quality-hooks-run` PASS except pre-existing blueprint-template-smoke (Bash 3.2/4) |

## Key Reviewer Files

- Primary files to review first:
  - `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` — guardrails #13–#15, numbered smoke step 3, updated bundle table
  - `AGENTS.md` — four additive prose additions across four canonical normative sections
  - `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` — contract compliance gap resolved

| File | Why reviewer-relevant |
|---|---|
| `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` | **Primary deliverable.** Guardrails #13–#15 (lines 152–181). Numbered smoke gate step 3. Updated bundle table with two REQUIRED HTTP rows. Confirm exact text matches spec ACs. |
| `AGENTS.md` | **Canonical governance source.** Four additive additions across four sections (§ Cross-Cutting Guardrails, § Testing and Quality Ratios, § Contract Testing Standards, § Minimum Validation Bundles). Confirm additions are additive, use MUST/MUST NOT, and are consistent with SKILL.md guardrail text. |
| `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` | **Contract compliance gap resolved.** File was required by `blueprint/contract.yaml` but absent. Confirm content is a derived summary of SKILL.md guardrails #13–#15 and smoke gate; introduces no additional requirements. |
| `docs/blueprint/architecture/decisions/ADR-issue-247-step05-slice-done-gate.md` | **Architecture decision record.** Documents four gaps, three guardrail decisions, smoke gate promotion, Option A selected, Option B rejected and parked. Also documents AGENTS.md scope extension (FR-007–FR-010). |
| `docs/blueprint/governance/spec_driven_development.md` | **Blueprint governance doc updated.** § Guardrails to Capture in Specs: three new bullets for Guardrails #13–#15; local smoke gate wording updated (curl → `make test-smoke-all-local`; now mandatory numbered step). |
| `docs/blueprint/governance/sdd_execution_guide.md` | **SDD guide updated.** Step 6 gains Step 3 local smoke gate block and per-scope guardrails #13–#15 reference. Mirror synced to bootstrap template. |
| `specs/2026-05-15-issue-247-step05-slice-done-gate/spec.md` | **Normative reference.** FR-001–FR-010, AC-001–AC-011 provide the canonical text for each guardrail. Use as the source of truth when reviewing SKILL.md and AGENTS.md prose. |
| `specs/2026-05-15-issue-247-step05-slice-done-gate/traceability.md` | **Traceability matrix.** Full REQ→implementation→test evidence mapping; validation summary with post-implementation results. |

## Validation Evidence

| Command | Result |
|---|---|
| `make infra-validate` | PASS — contract validation passed |
| `make quality-hooks-run` | PASS (1 pre-existing failure: `blueprint-template-smoke` — Bash 3.2 vs Bash 4 `declare -A` in `prune_codex_skills.sh`; confirmed pre-existing by reverting all changes and reproducing) |
| `make docs-build` | PASS (MDX `<name>` escape fixed in ADR — unescaped angle-bracket tag) |
| `make docs-smoke` | PASS |
| `make quality-hardening-review` | PASS |
| `make quality-sdd-check` | PASS |
| bootstrap template sync | 2 files updated (`sdd_execution_guide.md`, `spec_driven_development.md`) |

## Risk and Rollback

- **Main risks:**
  1. SKILL.md guardrail prose wording diverges from AGENTS.md canonical text — mitigated by spec FRs providing the normative reference for both files; human review during PR verifies alignment.
  2. `implement_checklist.md` drifts from SKILL.md guardrails over time — mitigated by normative hierarchy (SKILL.md is canonical, checklist is derived); Option B (automated scanner) parked in backlog as future safety net.
  3. `blueprint-template-smoke` pre-existing failure masks future regressions — pre-existing condition; not introduced by this work item; confirmed by reverting all changes; tracked separately.
- **Blast radius:** docs-only. No runtime, no Make targets, no API contracts. Consumer repos receive `implement_checklist.md` update on next blueprint upgrade; no breaking changes.
- **Feature flags:** none — no runtime behavior.
- **Rollback strategy:** `git revert` the slice commits (`e228b61`, `92967a3`, `c54e605`, `19f6d6d`). For consumer repos: reverting in the blueprint repo before the next consumer upgrade prevents `implement_checklist.md` propagation. SKILL.md and AGENTS.md changes would need to be reverted separately in consumer repos if already upgraded (low risk — additive prose).

## Deferred Proposals

- **Proposal 1** — Automated SKILL.md content scanner (Option B):
  - Outcome: **Parked** — `trigger: on-scope: skills`
  - Rationale: The skill runbook is human-authored governance prose, not a machine-verifiable interface contract. An automated guardrail-text scanner couples the check to prose phrasing, requiring updates on any reword, and provides limited incremental value over the spec-to-code review gap already enforced by SDD review. See ADR for full rationale.
  - Backlog entry: `AGENTS.backlog.md` § on-scope: skills — `proposal(issue-247-step05-slice-done-gate): automated SKILL.md content scanner`
