# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: roster locked at 8 experts; persona files stay short and posture-only; matrix lives in exactly one file.
  - The expert roster is locked at **8** (product-pragmatist, boundary-hawk, security-paranoid, data-privacy, test-quality-sceptic, operability-sre, documentation-discipline, performance-cost-aware). The ceiling is occupied on day one. A 9th expert MUST demonstrate distinct push-back triggers none of the 8 cover, or MUST replace an underperforming existing expert after 30 days of no distinct findings.
  - Persona files MUST stay short and posture-only — no procedural step lists, no schemas, no DoD checklists. Each `## Push-back Triggers` section MUST list ≥6 distinct trigger phrases (one per list item); the count of phrases semantically overlapping with any other persona's triggers MUST NOT exceed 1 per persona.
  - The SDD-step × expert matrix lives in EXACTLY ONE file (design-contracts § C3); ADR cross-references rather than duplicates.
- Anti-abstraction gate: dispatch contract is plain JSON Schema in the ADR; persona slugs are kebab-case directory names — no DSL, codegen, enum class, or registry singleton.
  - The dispatch contract is plain JSON Schema embedded in the ADR — no DSL, no codegen, no framework layer.
  - Persona slugs are kebab-case strings used as directory names — no enum class, no registry singleton.
- Integration-first testing gate: structural assertions only (grep + file-existence + ADR-text substrings); the dispatch boundary harness is owned by #361.
  - Verification is structural (grep + file-existence + ADR-text substring assertions). The "contract test" is `make quality-sdd-check` plus the AC-001 through AC-007 assertions in `tests/` or as shell snippets in `pr_context.md`.
  - Boundary tests for the dispatch contract (panel shape, convergence modes, empty-findings sentinel) are owned by #361 and ship there; this ticket records the contract, not the test harness.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic ships here.
  - N/A — this work item ships no filter or payload-transform logic. No runtime data flows through new code.
- Finding-to-test translation gate: capture any deterministic failure as a one-shot script in `evidence_manifest.json` and reference from `pr_context.md`.
  - If `make quality-sdd-check` or hooks surface a deterministic failure that is not satisfied by a structural assertion in AC-006, capture it as a one-shot script in `evidence_manifest.json` and reference from `pr_context.md`. No runtime code is added by this ticket, so the translation surface is limited to docs/schema/text checks.

## Delivery Slices

The slices are sequenced to keep each commit reviewable in isolation. Each slice produces a working repo state; only the final slice (slice 6) opens the cross-ticket amendment fan-out.

1. **Slice 1 — Spec + ADR scaffold (THIS step01 intake)**: populate spec.md, architecture.md, plan.md, tasks.md, traceability.md, graph.json with the contract enumerated in this plan; draft `ADR-issue-364-expert-persona-model.md` with `Status: proposed`. No persona files yet, no skill edits, no cross-ticket comments. Output: Draft PR opened, awaiting Product sign-off (SPEC_PRODUCT_READY gate).
2. **Slice 2 — Persona file authoring + old-file deletion** (lands at step05): create 8 `.agents/personas/<slug>/PERSONA.md` files, each with the 6 required sections (`## Worldview`, `## Default Heuristics`, `## Push-back Triggers`, `## What I Notice That Others Miss`, `## Quality Bar`, `## Communication Style`). Quality bars per FR-001: (a) ≥6 distinct trigger phrases in `## Push-back Triggers`; (b) at most 1 phrase semantically overlapping with any other persona; (c) `## Worldview` is self-contained — no references to `AGENTS.md § Role and Philosophy`; (d) no persona body prose references another expert's slug (compositional independence). The `data-privacy` persona MUST carry the distinguishing posture (data minimization, lawful basis, retention, subject rights) distinct from `security-paranoid`. Trigger phrases MUST be written with sufficient domain specificity that the #361 orchestrator substring-match algorithm (ADR § 4.2) routes correctly without ambiguity. **In the same commit**, delete the 10 old flat persona files from PR #362 (`.agents/personas/po-analyst.md`, `architect.md`, `tech-lead.md`, `implementer.md`, `devsecops-qa.md`, `doc-keeper.md`, `security-reviewer.md`, `architecture-reviewer.md`, `contract-reviewer.md`, `test-coverage-reviewer.md`) per FR-011; preserve `.agents/personas/consumer/`. Verify AC-001, AC-012, AC-013 pass locally.
3. **Slice 3 — Skill runbook persona-coupling strip + step08 panel-input reshape**: cherry-pick the 10 net-new SKILL.md files from PR #362 onto this branch (`git cherry-pick <sha>` per runbook where possible), then immediately strip persona-coupling language per FR-006(a)/(b). Reshape `blueprint-sdd-step08-agent-pr-review/SKILL.md` to accept `expert_slugs[]` input and produce a per-expert verdict array in `## Required Output Schema` per FR-006(c). Maintain the **Cherry-Pick Ledger** in `pr_context.md` (sub-section "Cherry-Pick Ledger"): one row per runbook of the form `| <runbook path> | <PR #362 commit-sha or "(new on this branch)"> | <stripping-edit commit-sha on this branch> |`. Verify AC-004 (zero stage-persona slug matches), AC-011 (step08 schema shape), AC-014 (all 8 SDD-step SKILL.md files have Required Output Schema + panel ≥ 2 carries expert_verdicts/expert_slug).
4. **Slice 4 — Design-contracts reshape + AGENTS.md + ADR amendments + mirror resync**: (a) reshape design-contracts § C3 with the SDD-step × expert matrix and remove old `Activation Triggers`/`Skills Invoked` prose (FR-002); (b) replace § C8 Category (c) persona-list rows with the 8 expert-slug rows (FR-009); (c) update § C7 `persona` field prose to skill-basename wording (FR-010); (d) update `AGENTS.md § Role and Philosophy` to carry the `operator-default` scope qualifier in the heading and a `Persona precedence` paragraph in the body (FR-012 / AC-015); (e) add `Amended by ADR-issue-364-expert-persona-model.md` lines to `ADR-issue-337-persona-skill-contract.md`, `ADR-issue-337-c7-emission-mechanism.md`, `ADR-issue-337-reviewer-model-heterogeneity.md`; (f) set `Status: superseded` on `ADR-issue-360-factory-personas-skills-roster.md`; (g) run `uv run python3 scripts/lib/docs/sync_blueprint_template_docs.py` to resync bootstrap template mirror. Verify AC-002, AC-003, AC-008, AC-009, AC-010, AC-015.
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
  - C8 § (c) persona-list replacement: grep predicates per AC-008.
  - C7 persona-field semantics: absence/presence grep per AC-009.
  - Bootstrap mirror in sync: `sync_blueprint_template_docs.py --check` or `diff -u` per AC-010.
  - Step08 schema reshape: grep on `## Required Output Schema` block per AC-011.
  - PERSONA.md compositional independence: no-other-slug grep per AC-012.
  - Old flat persona files deleted: `git ls-files` predicate per AC-013.
  - All SDD-step SKILL.md schema sanity: loop grep per AC-014.
  - AGENTS.md operator-default scoping: heading + body grep per AC-015.

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
- Blueprint docs updates: design-contracts § C3/C7/C8 reshape + new ADR-issue-364 + #337 amendments + AGENTS.md scoping + bootstrap template mirror.
  - `docs/blueprint/autonomous-factory/design-contracts.md` § C3 reshape (single-source the SDD-step × expert matrix).
  - `docs/blueprint/architecture/decisions/ADR-issue-364-expert-persona-model.md` (new ADR).
  - `docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md` (Status flip).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-persona-skill-contract.md` (Amended-by line).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` (Amended-by line + expert_verdicts[] additive field clause).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-reviewer-model-heterogeneity.md` (Amended-by line + per-expert model assignment clause).
  - `AGENTS.md` persona section retitle + rewrite.
  - `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` (mirror resync via `sync_blueprint_template_docs.py`).
- Consumer docs updates: None at this layer — the C8 surface receives this via `/blueprint-consumer-upgrade` per #342's per-artifact versioning expansion (amended into #342 via comment from step06).
- Mermaid diagrams updated: ADR-issue-364 carries the flowchart and sequenceDiagram for the three-layer model and parallel-then-merge convergence.
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
- Logging/metrics/traces: No new runtime — the `expert_verdicts[]` field becomes a queryable C7 outcome_details key for post-merge audits ("Show me every block verdict by Boundary Hawk in last 30 days"). Documented in ADR-issue-337-c7-emission-mechanism.md amendment.
- Alerts/ownership: No alerts added. Existing C7-derived alerts remain in scope.
- Runbook updates: None required. Future #361 orchestrator runbook will cover panel-dispatch operability.

## Risks and Mitigations
- Risk 1 -> mitigation: 8-expert roster is at the ceiling on day one — any 9th expert MUST demonstrate distinct push-back triggers the existing 8 do not cover, OR MUST replace an underperforming existing expert; below-distinction proposals MUST be rejected. The ADR pins this discipline.
- Risk 2 -> mitigation: Convergence dedup quality degrades when N experts emit semantically-duplicate findings → priority-order verdict aggregation (`block > revise > pass`) is the minimum; finding-text dedup is a #361 follow-up problem, not blocking here.
- Risk 3 -> mitigation: Per-expert model assignment raises token cost → final tier baseline is 5 Opus (product-pragmatist, boundary-hawk, security-paranoid, data-privacy, + documentation-discipline at Sonnet as baseline) and 3 Sonnet (test-quality-sceptic, operability-sre, performance-cost-aware); documentation-discipline overrides to Haiku at step01/step03/step08 (structural-presence only); the `model_per_expert` field in the dispatch table (ADR §4.1) allows #335 to tune further; cost-tracking captured in #361's observability surface.
- Risk 4 -> mitigation: Cross-ticket amendment fan-out forgets a ticket → `pr_context.md` checklist enumerates all required URLs (AC-005); merge gate fails if any URL is missing or returns non-200.
- Risk 5 -> mitigation: PR #362 stays open and confuses readers about which is the source of truth → step06 closes PR #362 explicitly with a top-comment naming this PR; AC-005 verifies the close-with-reference link.
