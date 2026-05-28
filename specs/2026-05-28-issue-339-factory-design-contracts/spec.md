# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 3
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 3
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-007 (Clean Architecture dependency direction), SDD-C-008 (test pyramid), SDD-C-013 (STACKIT managed-first), SDD-C-014 (local-first runtime), SDD-C-015 (app onboarding Make targets), SDD-C-018 (blueprint defect escalation), SDD-C-022 (local smoke gate), SDD-C-023 (filter/transform unit assertions), SDD-C-024 (finding-to-test translation) are not declared applicable: this work item produces governance documentation and one ADR — no runtime code, no HTTP routes, no filters, no app onboarding surface, no consumer workaround, no STACKIT runtime resource, and no test pyramid beyond `make docs-build` / `make docs-smoke`.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Pin the cross-ticket interface conventions that Phase 1 factory tickets (#333, #334, #335, #336) and Phase 0 sibling #337 all depend on, in a single signed-off document, so the four Phase 1 tickets do not invent conflicting values for the same shared concepts and Phase 1 ships with consistent interfaces.
- Success metric: Zero contract-disagreement defects discovered during Phase 1 integration between #333, #334, #335, #336, #337 (measured as PR-time changes to any of contracts 1–7 in this document driven by inconsistency rather than evolving requirements).

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The deliverable document at `docs/blueprint/autonomous-factory/design-contracts.md` MUST contain EXACTLY ONE OF the seven named contract sections per ordered identifier C1 through C7.
- FR-002 Each contract section MUST end with a `Referenced by:` line enumerating the GitHub issue numbers of every dependent ticket; the union across the seven sections MUST cover the ticket set {#333, #334, #335, #336, #337, #338} with no orphans.
- FR-003 Every contract section MUST confine `TBD` tokens to an explicit `### Open Decisions` subsection naming the deferring Phase 1 ticket number and the resolve-by deadline; `TBD` outside such a subsection MUST be rejected by review.
- FR-004 Contract C1 (branch naming) MUST pin the format `factory/<issue-number>-<short-slug>` for single-ticket runs and `factory/<parent-issue>-<child-issue>-<short-slug>` for decomposed children.
- FR-005 Contract C2 (spec directory layout for decomposed tickets) MUST pin the parent path `docs/blueprint/specs/<parent-issue>-<slug>/` and the child path `docs/blueprint/specs/<parent-issue>-<slug>/children/<child-issue>-<slug>/` and MUST require each child spec to reference the parent spec path and the boundary type cited by `blueprint-ticket-decompose-light`.
- FR-006 Contract C3 (OpenHands microagent ↔ persona mapping) MUST require microagent name equality with persona file basename and MUST declare the persona's `## Activation Triggers` section authoritative for selection and `## Skills Invoked` section authoritative for execution scope.
- FR-007 Contract C4 (integration acceptance criteria format) MUST require a parent issue body section titled `## Integration Acceptance Criteria` with checkboxes only satisfiable by cross-child behavior, and MUST require parent closure to depend on all children merged AND every checkbox ticked by a human bounded-context reviewer.
- FR-008 Contract C5 (factory bot identity + SoD detection) MUST pin a single GitHub machine user as the authoring identity for every factory commit and review comment, and MUST declare a deterministic string-match rule under which sign-offs by that identity do NOT count toward multi-author Separation of Duties.
- FR-009 Contract C6 (CODEOWNERS team slugs) MUST list canonical GitHub team slugs for the four spec sign-off roles (Product, Architecture, Security, Operations) and MUST list one bounded-context merge-review team slug per bounded context declared in this repo, with the rule that every listed slug MUST resolve to a real GitHub team carrying at least two members before #337 can close.
- FR-010 Contract C7 (metrics dashboard target + event schema) MUST pin the dashboard platform and MUST require factory-emitted lifecycle events to carry, at minimum, the eight fields `ticket_id`, `parent_ticket_id` (nullable), `phase`, `persona`, `model`, `timestamp`, `outcome`, `rerun_round`.
- FR-011 An ADR record at `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` MUST exist and MUST link to the deliverable document by relative path.
- FR-012 The deliverable document MUST carry all four canonical sign-offs from `AGENTS.md § Sign-off Phrases` before being merged to `main`.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The Contract C5 deterministic string-match rule for factory bot identity MUST be specified as exact-string equality on the comment author's GitHub login, and MUST NOT use substring, regex, or display-name heuristics, in order to prevent false positives that would count factory-authored sign-offs toward multi-author SoD.
- NFR-OBS-001 The Contract C7 event schema MUST be expressed in a form that downstream consumers (#336 webhook emitter, #337 instrumentation plan, #335 OpenHands run metadata) can adopt without re-specification; the eight minimum fields MUST be presented as a named schema with explicit JSON-compatible types and nullability per field.
- NFR-REL-001 The `Referenced by:` line in each contract section MUST be updated within the same PR whenever any downstream ticket scope is changed to add or remove a dependency on that contract; rollback is achieved by reverting the design-contracts.md change in isolation since no runtime code depends on its content.
- NFR-OPS-001 The deliverable document and the ADR MUST be discoverable via `make docs-build` and MUST pass `make docs-smoke` with no link or anchor regressions against the existing `docs/blueprint/` tree.
- NFR-A11Y-001 N/A — internal governance documentation. No UI surface is introduced or modified by this work item.

## Normative Option Decision
- Option A: Single `docs/blueprint/autonomous-factory/design-contracts.md` document containing the seven contract sections, recorded by one summary ADR.
- Option B: Seven separate ADRs under `docs/blueprint/architecture/decisions/`, one per contract, with no consolidated document.
- Selected option: OPTION_A
- Rationale: cross-referencing seven tightly coupled conventions is cheaper to maintain in one file than across seven ADRs; matches the existing ADR convention of one decision per record (the meta-decision "centralize these conventions"); avoids seven independent sign-off cycles on closely coupled values; #337 already produces ten ADRs and Phase 0 ceremony must stay proportionate.

## Contract Changes (Normative)
- Config/Env contract: none.
- API contract: none.
- OpenAPI / Pact contract path: none
- Event contract: introduces the lifecycle-event schema definition under Contract C7 (definition only; emission is owned by #336 / #335).
- Make/CLI contract: none.
- Docs contract: introduces `docs/blueprint/autonomous-factory/design-contracts.md` and `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`; the autonomous-factory subdirectory is created by this work item.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `docs/blueprint/autonomous-factory/design-contracts.md` exists with all seven contract sections populated and contains zero `TBD` tokens outside `### Open Decisions` subsections.
- AC-002 Each contract section ends with a `Referenced by:` line whose union across the seven sections covers {#333, #334, #335, #336, #337, #338} with no orphan ticket.
- AC-003 The document carries all four canonical sign-off phrases from `AGENTS.md` recorded in the PR comment thread.
- AC-004 Every open decision present in the document is captured under a `### Open Decisions` subsection naming the deferring Phase 1 ticket number and the resolve-by deadline.
- AC-005 `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` exists with `Status: approved` and links to the deliverable document by relative path.
- AC-006 `make quality-sdd-check` passes against this work item's `specs/2026-05-28-issue-339-factory-design-contracts/` directory.
- AC-007 `make docs-build` and `make docs-smoke` pass with the new deliverable and ADR added.

## Informative Notes (Non-Normative)
- Context: this is the first SDD work item in the autonomous software factory initiative (Epic #332). Manual SDD is used to build the contract layer that the factory itself will later inherit. The strictness applied here is the strictness the factory will inherit.
- Tradeoffs: a single design-contracts file means any change touches every dependent ticket's perceived blast radius. Mitigation: contract sections are self-contained and `Referenced by:` lines make scope explicit per section.
- Clarifications:
  - [NEEDS CLARIFICATION: Q-1 — Factory bot final GitHub handle. The Epic recommends `stackit-factory-bot` as a working name; the final handle is owned by Operations during #334. Resolution path: Operations confirms during #334 Secrets Manager provisioning; this document's Contract C5 carries the value under `### Open Decisions` until then; #334 cannot close while this remains TBD.]
  - [NEEDS CLARIFICATION: Q-2 — CODEOWNERS canonical team slugs and the bounded-context enumeration. The four sign-off team slugs and the per-bounded-context merge teams are not yet decided; the repo references "bounded contexts" as a concept but does not enumerate concrete contexts. Resolution path: Architecture + Operations enumerate and provision the GitHub teams during #337; this document's Contract C6 carries placeholders under `### Open Decisions` until then; #337 cannot close while this remains TBD.]
  - [NEEDS CLARIFICATION: Q-3 — Metrics dashboard platform target. STACKIT-hosted Grafana, internal observability tool, or other. Resolution path: Operations confirms during #337 instrumentation plan sign-off; this document's Contract C7 carries the value under `### Open Decisions` until then; #337 cannot close while this remains TBD.]

## Explicit Exclusions
- Excluded item 1: implementation of any of the seven contracts (e.g., creating CODEOWNERS entries, provisioning the bot identity, emitting events) — all owned by their respective Phase 1 tickets.
- Excluded item 2: enumeration of bounded contexts beyond the placeholder structure — owned by #337 with Architecture input.
- Excluded item 3: ADR drafts for the ten decisions in scope of #337 — those are #337's deliverables, not this work item's.
- Excluded item 4: any change to existing `docs/blueprint/contracts/` or `docs/blueprint/governance/` documents — this work item only creates new files under `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/`.
