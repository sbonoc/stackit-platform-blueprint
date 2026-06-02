# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Update contract/governance surfaces: AGENTS.md persona section retitle + rewrite (operator-default scope note per ADR-issue-364 § 8.1); `docs/blueprint/autonomous-factory/design-contracts.md` § C3 reshape with the SDD-step × expert matrix AND removal of the old persona `Activation Triggers` / `Skills Invoked` prose (FR-002); design-contracts § C8 Category (c) persona-list rows replaced with the 8 expert-slug rows (FR-009); design-contracts § C7 `persona` field description and surrounding emission-mechanism prose updated to align with skill-as-actor + `expert_verdicts[]` attribution (FR-010); `MEMORY.md` index + the three project memory files reflect the post-#364 model.
- [ ] T-002 Author 8 expert-persona files at `.agents/personas/<slug>/PERSONA.md` with the 6 required sections and none of the forbidden sections (FR-001). The `data-privacy` persona MUST carry the distinguishing posture per FR-001 (data minimization, lawful basis, retention, subject rights as first-order concerns; push-back triggers distinct from `security-paranoid`).
- [ ] T-003 Re-home 10 skill runbooks from PR #362 onto this branch with persona-coupling language stripped (FR-006 a, b); reshape `blueprint-sdd-step08-agent-pr-review/SKILL.md` to take panel-input and emit a per-expert verdict array (FR-006 c).
- [ ] T-004 Author `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` with the supersession + amendment clauses, the JSON Schema for the verdict object, the flowchart-TD three-layer diagram, and the sequence-diagram of parallel-then-merge convergence. Cross-reference design-contracts § C3 by relative path (FR-002, FR-003, FR-004).
- [ ] T-005 Flip `Status: superseded by ADR-issue-364-expert-persona-model.md` on ADR-issue-360-factory-personas-skills-roster.md; add `Amended by ADR-issue-364-expert-persona-model.md` lines to the three #337 ADRs naming clause(s) amended (FR-005).
- [ ] T-006 Amend `ADR-issue-337-c7-emission-mechanism.md` with the additive `outcome.details.expert_verdicts[]` field clause (FR-007).
- [ ] T-007 Resync bootstrap template mirrors under `scripts/templates/blueprint/bootstrap/` via `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py` (NFR-OPS-001).
- [ ] T-008 Post cross-ticket amendment comments per FR-008: #333, #361, #335, #336, #342, #343, #332; close-with-reference #360 + PR #362. Capture all URLs in `pr_context.md` "Cross-Ticket Amendments" section.

## Test Automation
- [ ] T-101 Author shell-based AC-001 assertion (per-slug PERSONA.md existence + section presence/absence grep); capture in `pr_context.md` or as `tests/contracts/test_expert_personas_shape.sh`.
- [ ] T-102 Author shell-based AC-002 assertion (ADR-issue-364 existence + supersession + 3 amendment substrings).
- [ ] T-103 Author shell-based AC-003 assertion (design-contracts § C3 header + table header exact match + ADR cross-reference path).
- [ ] T-104 Author shell-based AC-004 assertion (`grep -rE "...(persona)" .agents/skills/blueprint-*/SKILL.md` returns zero).
- [ ] T-105 Author shell-based AC-005 assertion (parse pr_context.md "Cross-Ticket Amendments" URLs; `gh api` HTTP-200 each).
- [ ] T-108 Author shell-based AC-008 assertion (grep design-contracts.md for absence of the 10 old stage-persona paths AND presence of the 8 expert-slug `.agents/personas/<slug>/PERSONA.md` paths).
- [ ] T-109 Author shell-based AC-009 assertion (grep design-contracts.md § C7 for absence of the legacy substrings `the persona file basename (matches Contract C3 microagent name)` and `wraps each persona invocation`, AND presence of `skill basename` rewording in the `persona` field description block).
- [ ] T-110 Author shell-based AC-010 assertion (`uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py --check` exits 0; if no `--check` flag, fall back to `diff -u` between live design-contracts.md and the bootstrap-template mirror, asserting zero diff).
- [ ] T-111 Author shell-based AC-011 assertion (extract `## Required Output Schema` block from `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md`; assert absence of `reviewer_persona`, presence of `expert_slug` AND presence of `expert_verdicts`).
- [ ] T-103-pos N/A — no filter/payload-transform logic in this ticket. Documented in `pr_context.md` Validation Evidence.
- [ ] T-104-trans N/A — no deterministic pre-PR smoke failure surface. Quality gates (T-106) are the deterministic check.
- [ ] T-105-bnd N/A — no boundary/integration test surface; dispatch boundary tests are owned by #361.

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 NFR-A11Y-001 = "N/A — no user-facing UI; this work item ships persona files, ADRs, skill runbooks, and GH-issue amendments only."
- [ ] T-A02 N/A — no UI to scan.
- [ ] T-A03 N/A — no interactive elements.
- [ ] T-A04 N/A — no focus indicators.
- [ ] T-A05 N/A — no non-text content.

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check`, `make quality-hooks-fast`, `make quality-hooks-slow`; all exit 0 (AC-006).
- [ ] T-202 Attach evidence to `traceability.md` (per-FR/NFR/AC test/doc/ops paths) and `evidence_manifest.json` (file list with hashes if hash-on-publish is in scope).
- [ ] T-203 Confirm no stale TODOs / dead code / drift in persona files, skill runbooks, ADRs.
- [ ] T-204 Run `make docs-build` and `make docs-smoke`.
- [ ] T-205 Run `make quality-hardening-review`.

## Publish
- [ ] P-001 Update `hardening_review.md` with the proposals-only section reflecting the expert-sprawl ceiling, convergence-dedup follow-up, and per-expert prompt-cache discipline.
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files (ADR + design-contracts § C3 + 7 persona files), Cross-Ticket Amendments section, validation evidence, rollback notes.
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`.

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 N/A — `apps-bootstrap` and `apps-smoke` are not affected by this work item; declared `App onboarding impact: no-impact` in `plan.md`
- [ ] A-002 N/A — backend app lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are unaffected
- [ ] A-003 N/A — frontend app lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are unaffected
- [ ] A-004 N/A — aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are unaffected
- [ ] A-005 N/A — port-forward operational wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are unaffected

## Cross-Ticket Amendments (this work item's step06 deliverable — FR-008)
- [ ] X-001 Post comment on #333 (epic body retitle proposal + scope amendment to factory execution layer framing).
- [ ] X-002 Post comment on #361 (dispatch table becomes `step → {skill, expert_panel, convergence, model_per_expert}`; empty-findings sentinel; per-expert C7 audit).
- [ ] X-003 Post comment on #335 (per-expert LiteLLM routing key; capacity sizing note for higher concurrent-workspaces-per-step).
- [ ] X-004 Post comment on #336 (FR-008 model-rotation audit invariant reformulated as panel-disjointness rule).
- [ ] X-005 Post comment on #342 (per-artifact versioning extends to expert-persona files as a new artifact category).
- [ ] X-006 Post comment on #343 (Phase 1 ingestion schema accounts for additive `expert_verdicts[]` in C7 outcome.details).
- [ ] X-007 Post comment on #332 (epic body framing update reflecting new model).
- [ ] X-008 Close #360 as superseded with reference to #364 and cherry-pick list.
- [ ] X-009 Close PR #362 as superseded with reference to this PR and cherry-pick list.
- [ ] X-010 Append all comment URLs to `pr_context.md` Cross-Ticket Amendments section (AC-005).
