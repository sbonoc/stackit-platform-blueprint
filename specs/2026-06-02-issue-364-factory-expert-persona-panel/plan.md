# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep the expert roster at 7 unless a distinct push-back trigger genuinely justifies an 8th.
  - Persona files MUST stay short and posture-only — no procedural step lists, no schemas, no DoD checklists.
  - The SDD-step × expert matrix lives in EXACTLY ONE file (design-contracts § C3); ADR cross-references rather than duplicates.
- Anti-abstraction gate:
  - The dispatch contract is plain JSON Schema embedded in the ADR — no DSL, no codegen, no framework layer.
  - Persona slugs are kebab-case strings used as directory names — no enum class, no registry singleton.
- Integration-first testing gate:
  - Verification is structural (grep + file-existence + ADR-text substring assertions). The "contract test" is `make quality-sdd-check` plus the AC-001 through AC-007 assertions in `tests/` or as shell snippets in `pr_context.md`.
  - Boundary tests for the dispatch contract (panel shape, convergence modes, empty-findings sentinel) are owned by #361 and ship there; this ticket records the contract, not the test harness.
- Positive-path filter/transform test gate:
  - N/A — this work item ships no filter or payload-transform logic. No runtime data flows through new code.
- Finding-to-test translation gate:
  - If `make quality-sdd-check` or hooks surface a deterministic failure that is not satisfied by a structural assertion in AC-006, capture it as a one-shot script in `evidence_manifest.json` and reference from `pr_context.md`. No runtime code is added by this ticket, so the translation surface is limited to docs/schema/text checks.

## Delivery Slices

The slices are sequenced to keep each commit reviewable in isolation. Each slice produces a working repo state; only the final slice (slice 6) opens the cross-ticket amendment fan-out.

1. **Slice 1 — Spec + ADR scaffold (THIS step01 intake)**: populate spec.md, architecture.md, plan.md, tasks.md, traceability.md, graph.json with the contract enumerated in this plan; draft `ADR-issue-364-expert-persona-model.md` with `Status: proposed`. No persona files yet, no skill edits, no cross-ticket comments. Output: Draft PR opened, awaiting Product sign-off (SPEC_PRODUCT_READY gate).
2. **Slice 2 — Persona file authoring** (step03/step04 of SDD): create 8 `.agents/personas/<slug>/PERSONA.md` files, each with the 6 required first-person sections. The `data-privacy` persona MUST carry the distinguishing posture (data minimization, lawful basis, retention, subject rights) that AC-001 checks. No skill edits in this slice. Verify AC-001 passes locally with the grep assertions.
3. **Slice 3 — Skill runbook persona-coupling strip + `blueprint-agent-pr-review` panel-input reshape**: edit the 10 skill files cherry-picked from PR #362 to remove stage-persona language; reshape `blueprint-agent-pr-review` to take panel input and produce a per-expert verdict array. Verify AC-004 passes (zero grep hits for "X persona" phrasing).
4. **Slice 4 — Design-contracts § C3 reshape + AGENTS.md persona section update + ADR amendment lines on the four superseded/amended ADRs**: single-source the SDD-step × expert matrix in design-contracts; retitle the AGENTS.md persona section; add `Amended by ADR-issue-364-expert-persona-model.md` lines to the three #337 ADRs; set `Status: superseded by ADR-issue-364-expert-persona-model.md` on ADR-issue-360. Resync bootstrap template mirror. Verify AC-002 and AC-003.
5. **Slice 5 — Memory file updates** (`MEMORY.md` index + `project_autonomous_factory.md` + `project_factory_design_contracts.md` + `project_factory_c7_emission_mechanism.md`): reflect the post-#364 model in the auto-memory store. Verify AC-007 substring presence.
6. **Slice 6 — Cross-ticket amendments fan-out** (step06 document-sync of SDD): post one comment per ticket per FR-008. Close #360 and PR #362 with cherry-pick references. Capture all comment URLs in `pr_context.md` "Cross-Ticket Amendments" section. Verify AC-005.
7. **Slice 7 — Quality gates + hardening + PR ready** (step07): `make quality-sdd-check` + `make quality-hooks-fast` + `make quality-hooks-slow`; hardening review entries; flip PR Ready-for-Review. Verify AC-006.

## Change Strategy
- Migration/rollout sequence: All slices land on this branch; the merge of this PR is the cutover. No phased rollout — the personas/skills/docs surface is internal to the factory and consumed by future bot runs that boot fresh per ticket. Consumer repos that have inherited the C8 surface will receive the change via `/blueprint-consumer-upgrade` per #342 (which itself learns about the new artifact category from this ticket's amendment comment).
- Backward compatibility policy: C7 schema change is additive (optional field) so existing emitters/consumers remain valid. ADR supersession is metadata-only; the superseded ADR-issue-360 remains in the repo with an updated `Status` line for historical reference. Skill runbook edits remove stage-persona language; any caller that hard-coded a stage-persona name will need to switch to the orchestrator dispatch (delivered in #361) — captured as #361's responsibility, not a regression here.
- Rollback plan: `git revert` the merge commit. The additive C7 field is tolerated by existing consumers. Persona files and skill edits revert cleanly. Cross-ticket comments are not auto-reverted but carry the PR/issue number as their identifier — manual deletion or follow-up comment is possible. The ADR-issue-360 `Status` line revert is a one-line change.

## Validation Strategy (Shift-Left)
- Unit checks: N/A — no runtime code.
- Contract checks: ADR contains a JSON Schema for the verdict object; structural assertion validates schema syntax (`uv run python3 -c "import json, jsonschema; jsonschema.Draft7Validator.check_schema(...)"`).
- Integration checks: N/A — no integration code.
- E2E checks: N/A — no UI / user journey.
- Structural checks (replacing the test gates above for this ticket):
  - Persona file shape: shell + grep assertions per AC-001.
  - ADR cross-references: shell + grep assertions per AC-002.
  - Matrix single-source: shell + grep assertions per AC-003.
  - Skill runbook clean: shell + grep assertions per AC-004.
  - Cross-ticket comment URLs: `gh api` HTTP-200 check per AC-005.
  - Quality gates: `make quality-sdd-check`, `make quality-hooks-fast`, `make quality-hooks-slow` per AC-006.
  - Memory store presence (skip-if-absent): file-existence + grep per AC-007.

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
- Notes: This work item ships specs, ADRs, persona files, skill runbook edits, and docs. No make targets added or changed.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C3 reshape (single-source the SDD-step × expert matrix).
  - `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` (new ADR).
  - `docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md` (Status flip).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` (Amended-by line).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` (Amended-by line + expert_verdicts[] additive field clause).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` (Amended-by line + per-expert model assignment clause).
  - `AGENTS.md` persona section retitle + rewrite.
  - `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` (mirror resync via `sync_blueprint_template_docs.py`).
- Consumer docs updates: None at this layer — the C8 surface receives this via `/blueprint-consumer-upgrade` per #342's per-artifact versioning expansion (amended into #342 via comment from step06).
- Mermaid diagrams updated:
  - ADR-issue-364 includes a `flowchart TD` of the three-layer model (SDD step → skill → expert panel).
  - ADR-issue-364 includes a `sequenceDiagram` showing parallel-then-merge convergence with empty-findings-sentinel responses.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - N/A — this work item touches no HTTP route handlers, query/filter logic, or API endpoints. Documented in `pr_context.md` under Validation Evidence as "No HTTP surface changes — local-smoke gate not applicable."
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes
  - include Cross-Ticket Amendments section listing all comment URLs (AC-005)

## Operational Readiness
- Logging/metrics/traces: No new runtime — the `expert_verdicts[]` field becomes a queryable C7 outcome.details key for post-merge audits ("Show me every block verdict by Boundary Hawk in last 30 days"). Documented in ADR-issue-337-c7-emission-mechanism.md amendment.
- Alerts/ownership: No alerts added. Existing C7-derived alerts remain in scope.
- Runbook updates: None required. Future #361 orchestrator runbook will cover panel-dispatch operability.

## Risks and Mitigations
- Risk 1 -> mitigation: 8-expert roster is at the ceiling on day one — any 9th expert MUST demonstrate distinct push-back triggers the existing 8 do not cover, OR MUST replace an underperforming existing expert; below-distinction proposals MUST be rejected. The ADR pins this discipline.
- Risk 2 -> mitigation: Convergence dedup quality degrades when N experts emit semantically-duplicate findings → priority-order verdict aggregation (`block > revise > pass`) is the minimum; finding-text dedup is a #361 follow-up problem, not blocking here.
- Risk 3 -> mitigation: Per-expert model assignment raises token cost → heterogeneity ADR amendment encourages cheaper models for high-volume low-stakes experts (Documentation Discipline → Haiku) and stronger models for high-stakes experts (Security Paranoid → Opus); cost-tracking captured in #361's observability surface.
- Risk 4 -> mitigation: Cross-ticket amendment fan-out forgets a ticket → `pr_context.md` checklist enumerates all required URLs (AC-005); merge gate fails if any URL is missing or returns non-200.
- Risk 5 -> mitigation: PR #362 stays open and confuses readers about which is the source of truth → step06 closes PR #362 explicitly with a top-comment naming this PR; AC-005 verifies the close-with-reference link.
