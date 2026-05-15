# PR Context

## Summary
- Work item: 2026-05-15-issue-247-step05-slice-done-gate
- Objective: Close four structural gaps in the blueprint-sdd-step05-implement skill's per-slice definition of done. Adds Guardrails #13 (API field coverage), #14 (Vue branch coverage), #15 (Pact same-repo provider). Promotes smoke gate to numbered main workflow step. Adds AGENTS.md canonical normative home for all four gaps. Creates references/implement_checklist.md (contract compliance gap).
- Scope boundaries: .agents/skills/blueprint-sdd-step05-implement/SKILL.md (guardrails #13–#15, bundle table, workflow step 3); AGENTS.md (§ Cross-Cutting Guardrails, § Testing and Quality Ratios, § Contract Testing Standards, § Minimum Validation Bundles); .agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md (new file). No code, Make targets, or blueprint/contract.yaml changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-MAINT-001, NFR-COMPAT-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011
- Contract surfaces changed: Docs contract only — SKILL.md and AGENTS.md updated per spec. references/implement_checklist.md created (resolves blueprint/contract.yaml required_file gap).

## Key Reviewer Files
- Primary files to review first:
  - `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` — Guardrails #13–#15 (lines 152–181), numbered workflow step 3, updated bundle table
  - `AGENTS.md` — four additive additions to §§ Cross-Cutting Guardrails, Testing and Quality Ratios, Contract Testing Standards, Minimum Validation Bundles
  - `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` — new derived checklist file
- High-risk files:
  - `AGENTS.md` — canonical governance source; additions are prose-only and additive

## Validation Evidence
- Required commands executed: make quality-hooks-run · make infra-validate · make docs-build · make docs-smoke · make quality-hardening-review
- Result summary: PASS — make infra-validate clean; make docs-build clean (MDX `<name>` escaped in ADR); make docs-smoke clean; make quality-hardening-review clean. make quality-hooks-run: blueprint-template-smoke FAIL (pre-existing Bash 3.2 vs Bash 4 declare -A incompatibility in prune_codex_skills.sh — not introduced by this work item, confirmed by reverting all changes and reproducing same failure).
- Artifact references: traceability.md, evidence_manifest.json, hardening_review.md

## Risk and Rollback
- Main risks: (1) SKILL.md guardrail prose wording diverges from AGENTS.md canonical text across slices — mitigated by spec FRs providing normative reference for both. (2) implement_checklist.md drifts from SKILL.md guardrails over time — mitigated by normative hierarchy (SKILL.md is canonical, checklist is derived); Option B (automated scanner) parked in backlog.
- Rollback strategy: git revert the slice commits. Consumer repos receive checklist update only on next blueprint upgrade; reverting before next upgrade prevents propagation.

## Deferred Proposals
- Proposal 1 (not implemented): automated SKILL.md content scanner (Option B) — verify SKILL.md contains required guardrail patterns and smoke gate step as automated regression protection. Parked in AGENTS.backlog.md (on-scope: skills). See ADR for rejection rationale.
