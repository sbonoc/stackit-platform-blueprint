# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 4
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 4
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
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-007 (Clean Architecture dependency direction), SDD-C-008 (test pyramid), SDD-C-015 (app onboarding Make targets), SDD-C-018 (blueprint defect escalation), SDD-C-022 (local smoke gate), SDD-C-023 (filter/transform unit assertions), SDD-C-024 (finding-to-test translation) are not declared applicable: this work item produces governance documentation and one ADR — no runtime code, no HTTP routes, no filters, no app onboarding surface, no consumer workaround surface, and no test pyramid beyond `make docs-build` / `make docs-smoke`. SDD-C-013 (STACKIT managed-first) and SDD-C-014 (local-first runtime) are declared applicable because Contract C8 (Consumer Surface) imposes both properties on the consumer-shipped factory-instance surface enumerated by this document, even though their per-implementer realization lands in #334/#335/#336.

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
- Business outcome: Pin the cross-ticket interface conventions that Phase 1 factory tickets (#333, #334, #335, #336) and Phase 0 sibling #337 all depend on, AND pin the consumer-facing surface that the blueprint ships so each consumer repo can instantiate its own per-consumer autonomous factory, in a single signed-off document. Each consumer repo provisions its own factory instance (own Confidential K8s cluster, own OpenHands deployment, own GitHub App, own bot identity, own CODEOWNERS team slugs, own metrics dashboard); the LiteLLM gateway is an existing external service that consumers configure access to rather than deploy. This document distinguishes identical conventions (Contracts C1–C4 — applied identically by the blueprint repo and every consumer repo) from parameterized contracts (C5–C7 — schema is identical; values are per-consumer) and enumerates the consumer-shipped surface that makes inheritance possible (Contract C8).
- Success metric: Zero contract-disagreement defects discovered during Phase 1 integration between #333, #334, #335, #336, #337 (measured as PR-time changes to any of contracts C1–C8 in this document driven by inconsistency rather than evolving requirements) AND every consumer repo that adopts the factory (target: at least the first consumer adopter within six months of merge) can instantiate its factory using only the surface enumerated in Contract C8 without redefining any C1–C7 convention.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The deliverable document at `docs/blueprint/autonomous-factory/design-contracts.md` MUST contain EXACTLY ONE OF the eight named contract sections per ordered identifier C1 through C8.
- FR-002 Each contract section MUST end with a `Referenced by:` line enumerating the GitHub issue numbers of every dependent ticket; the union across the eight sections MUST cover the ticket set {#333, #334, #335, #336, #337, #338} with no orphans.
- FR-003 Every contract section MUST confine `TBD` tokens to an explicit `### Open Decisions` subsection naming the deferring Phase 1 ticket number and the resolve-by deadline; `TBD` outside such a subsection MUST be rejected by review.
- FR-004 Contract C1 (branch naming — identical convention) MUST pin the format `factory/<issue-number>-<short-slug>` for single-ticket runs and `factory/<parent-issue>-<child-issue>-<short-slug>` for decomposed children, and MUST declare the convention identical for the blueprint repo and every consumer repo that inherits the factory.
- FR-005 Contract C2 (spec directory layout for decomposed tickets — identical convention) MUST pin the parent path `docs/blueprint/specs/<parent-issue>-<slug>/` for the blueprint repo and `docs/specs/<parent-issue>-<slug>/` for consumer repos, and the corresponding child path `<parent-path>/children/<child-issue>-<slug>/`, and MUST require each child spec to reference the parent spec path and the boundary type cited by `blueprint-ticket-decompose-light`.
- FR-006 Contract C3 (OpenHands microagent ↔ persona mapping — identical convention) MUST require microagent name equality with persona file basename and MUST declare the persona's `## Activation Triggers` section authoritative for selection and `## Skills Invoked` section authoritative for execution scope, identically for the blueprint repo and every consumer repo.
- FR-007 Contract C4 (integration acceptance criteria format — identical convention) MUST require a parent issue body section titled `## Integration Acceptance Criteria` with checkboxes only satisfiable by cross-child behavior, and MUST require parent closure to depend on all children merged AND every checkbox ticked by a human bounded-context reviewer, identically for the blueprint repo and every consumer repo.
- FR-008 Contract C5 (factory bot identity + SoD detection — parameterized) MUST carry an `### Identical rule` subsection declaring that every factory instance MUST authenticate as a single GitHub machine user and MUST apply a deterministic exact-string-equality match on that user's GitHub login as the multi-author Separation-of-Duties suppression rule; MUST carry a `### Blueprint instance` subsection naming the bot login for the blueprint's own factory; and MUST carry a `### Consumer overlay` subsection that specifies the field name, type, and configuration location (e.g., `contract.yaml` key) where each consumer repo declares its own bot login without inheriting the blueprint's value.
- FR-009 Contract C6 (CODEOWNERS team slugs — parameterized) MUST carry an `### Identical rule` subsection declaring that every factory instance MUST resolve the four canonical sign-off roles (Product, Architecture, Security, Operations) to real GitHub team slugs each carrying at least two members; MUST carry a `### Blueprint instance` subsection listing the blueprint's four team slugs; and MUST carry a `### Consumer overlay` subsection that specifies the field names and configuration location where each consumer repo declares its own four team slugs, without inheriting the blueprint's slugs.
- FR-010 Contract C7 (metrics dashboard + event schema — parameterized) MUST carry an `### Identical rule` subsection pinning the minimum lifecycle-event field set (`ticket_id`, `parent_ticket_id` nullable, `phase`, `persona`, `model`, `timestamp`, `outcome`, `rerun_round`) as a named JSON schema with explicit types and nullability per field; MUST carry a `### Blueprint instance` subsection naming the dashboard platform target for the blueprint's own factory; and MUST carry a `### Consumer overlay` subsection that specifies the configuration location where each consumer repo declares its own dashboard target without inheriting the blueprint's target.
- FR-011 An ADR record at `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` MUST exist and MUST link to the deliverable document by relative path.
- FR-012 The deliverable document MUST carry all four canonical sign-offs from `AGENTS.md § Sign-off Phrases` before being merged to `main`.
- FR-013 Contract C8 (Consumer Surface — blueprint→consumer inheritance) MUST enumerate the complete surface the blueprint ships to enable per-consumer factory instances, partitioned into EXACTLY FOUR named categories: (a) documentation and ADRs under `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/`; (b) Terraform/Helm module wrappers under `scripts/templates/infra/` covering the per-consumer Confidential K8s cluster (#334), OpenHands Agent Server deployment (#335), ESO bindings, and webhook receiver (#336); (c) Make targets and skill runbooks consumers inherit via the blueprint contract (e.g., `factory-bootstrap`, `factory-smoke`, factory-related `.agents/skills/` runbooks); (d) GitHub App manifest and reusable GitHub Actions workflows under `.github/workflows/` consumers install on their own repo.
- FR-014 Contract C8 MUST declare LiteLLM an external service consumers configure access to (not deploy), MUST specify the configuration shape (gateway URL, key reference via ESO, model allowlist) and the field name and location in the consumer repo's `contract.yaml` where consumers declare their access configuration.
- FR-015 Contract C8 MUST require that every enumerated module wrapper, Make target, and skill runbook be inheritable by consumer repos through the existing blueprint `contract.yaml` mechanism (no new inheritance mechanism introduced), and MUST declare each surface item's stability tier (`stable`, `preview`, `internal`) consistent with the blueprint contract conventions.
- FR-016 The `### Consumer overlay` subsections required by FR-008, FR-009, and FR-010 MUST specify a schema (field name, type, configuration location, validation rule) rather than any concrete consumer-specific identity, slug, or target value; concrete consumer values are owned by each consumer repo's own onboarding work and MUST NOT appear in this blueprint-side document.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The Contract C5 deterministic string-match rule for factory bot identity MUST be specified as exact-string equality on the comment author's GitHub login, and MUST NOT use substring, regex, or display-name heuristics, in order to prevent false positives that would count factory-authored sign-offs toward multi-author SoD.
- NFR-OBS-001 The Contract C7 event schema MUST be expressed in a form that downstream consumers (#336 webhook emitter, #337 instrumentation plan, #335 OpenHands run metadata) can adopt without re-specification; the eight minimum fields MUST be presented as a named schema with explicit JSON-compatible types and nullability per field.
- NFR-REL-001 The `Referenced by:` line in each contract section MUST be updated within the same PR whenever any downstream ticket scope is changed to add or remove a dependency on that contract; rollback is achieved by reverting the design-contracts.md change in isolation since no runtime code depends on its content.
- NFR-OPS-001 The deliverable document and the ADR MUST be discoverable via `make docs-build` and MUST pass `make docs-smoke` with no link or anchor regressions against the existing `docs/blueprint/` tree.
- NFR-OPS-002 Contract C8 MUST require every consumer-shipped module wrapper enumerated under FR-013(b) to default to STACKIT-managed runtimes (SDD-C-013) and to local-first execution under the existing `docker-desktop-preferred` Kubernetes context policy (SDD-C-014); concrete per-wrapper realization is owned by #334/#335/#336 but the surface-enumeration schema in C8 MUST carry these properties as preconditions of inclusion.
- NFR-A11Y-001 N/A — internal governance documentation. No UI surface is introduced or modified by this work item.

## Normative Option Decision
- Option A: Single `docs/blueprint/autonomous-factory/design-contracts.md` document containing the seven contract sections, recorded by one summary ADR.
- Option B: Seven separate ADRs under `docs/blueprint/architecture/decisions/`, one per contract, with no consolidated document.
- Selected option: OPTION_A
- Rationale: cross-referencing seven tightly coupled conventions is cheaper to maintain in one file than across seven ADRs; matches the existing ADR convention of one decision per record (the meta-decision "centralize these conventions"); avoids seven independent sign-off cycles on closely coupled values; #337 already produces ten ADRs and Phase 0 ceremony must stay proportionate.

## Contract Changes (Normative)
- Config/Env contract: introduces the `### Consumer overlay` field-name and configuration-location schemas under Contracts C5, C6, C7, and C8 — the schemas describe where consumer repos declare their per-instance values (e.g., bot login, CODEOWNERS slugs, dashboard target, LiteLLM access). Concrete consumer values are out of scope (FR-016).
- API contract: none.
- OpenAPI / Pact contract path: none
- Event contract: introduces the lifecycle-event schema definition under Contract C7 (definition only; emission is owned by #336 / #335 inside every factory instance).
- Make/CLI contract: introduces the enumeration of consumer-inheritable Make targets and skill runbooks under Contract C8 (enumeration only; implementations are owned by #334/#335/#336).
- Docs contract: introduces `docs/blueprint/autonomous-factory/design-contracts.md` and `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`; the autonomous-factory subdirectory is created by this work item. Also enumerates consumer-inheritance scope of `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/` under Contract C8.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `docs/blueprint/autonomous-factory/design-contracts.md` exists with all eight contract sections C1–C8 populated and contains zero `TBD` tokens outside `### Open Decisions` subsections.
- AC-002 Each contract section ends with a `Referenced by:` line whose union across the eight sections covers {#333, #334, #335, #336, #337, #338} with no orphan ticket.
- AC-003 The document carries all four canonical sign-off phrases from `AGENTS.md` recorded in the PR comment thread.
- AC-004 Every open decision present in the document is captured under a `### Open Decisions` subsection naming the deferring Phase 1 ticket number and the resolve-by deadline.
- AC-005 `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md` exists with `Status: approved` and links to the deliverable document by relative path.
- AC-006 `make quality-sdd-check` passes against this work item's `specs/2026-05-28-issue-339-factory-design-contracts/` directory.
- AC-007 `make docs-build` and `make docs-smoke` pass with the new deliverable and ADR added.
- AC-008 Contracts C5, C6, and C7 each contain exactly the three required subsections `### Identical rule`, `### Blueprint instance`, and `### Consumer overlay`; the `### Consumer overlay` subsection in each names a schema (field name, type, configuration location, validation rule) and contains zero consumer-specific identity/slug/target values.
- AC-009 Contract C8 enumerates exactly four named surface categories matching FR-013 (a–d) and declares LiteLLM external per FR-014, with each enumerated surface item tagged `stable`, `preview`, or `internal` per FR-015.

## Informative Notes (Non-Normative)
- Context: this is the first SDD work item in the autonomous software factory initiative (Epic #332). Manual SDD is used to build the contract layer that the factory itself will later inherit. The strictness applied here is the strictness the factory will inherit. The factory is shipped to consumer repos as a capability (per-consumer-instance topology); the blueprint operates its own instance and also publishes the surface (docs, module wrappers, make targets, skill runbooks, GitHub App / workflows) consumers use to instantiate theirs. LiteLLM is a pre-existing external service consumers configure access to rather than deploy.
- Tradeoffs: a single design-contracts file means any change touches every dependent ticket's perceived blast radius. Mitigation: contract sections are self-contained and `Referenced by:` lines make scope explicit per section. Parameterized C5/C6/C7 add subsection structure but keep the identical-rule statement at the top so consumers and the blueprint share the same authoritative semantics.
- Clarifications:
  - [NEEDS CLARIFICATION: Q-1 — Factory bot final GitHub handle for the BLUEPRINT INSTANCE only. The Epic recommends `stackit-factory-bot` as a working name; the final handle is owned by Operations during #334. The Contract C5 `### Consumer overlay` schema is unaffected by Q-1 — consumers declare their own bot login per the schema regardless of the blueprint's choice. Resolution path: Operations confirms the blueprint-instance handle during #334 Secrets Manager provisioning; Contract C5 `### Blueprint instance` subsection carries the value under `### Open Decisions` until then; #334 cannot close while this remains TBD.]
  - [NEEDS CLARIFICATION: Q-2 — CODEOWNERS canonical team slugs for the BLUEPRINT INSTANCE and the blueprint's own bounded-context enumeration. The four sign-off team slugs and per-bounded-context merge teams for the blueprint repo are not yet decided. The Contract C6 `### Consumer overlay` schema is unaffected — consumers declare their own four slugs per the schema. Resolution path: Architecture + Operations enumerate and provision the blueprint's GitHub teams during #337; Contract C6 `### Blueprint instance` subsection carries placeholders under `### Open Decisions` until then; #337 cannot close while this remains TBD.]
  - [NEEDS CLARIFICATION: Q-3 — Metrics dashboard platform target for the BLUEPRINT INSTANCE. STACKIT-hosted Grafana, internal observability tool, or other. The Contract C7 `### Consumer overlay` schema is unaffected — consumers declare their own dashboard target per the schema. Resolution path: Operations confirms during #337 instrumentation plan sign-off; Contract C7 `### Blueprint instance` subsection carries the value under `### Open Decisions` until then; #337 cannot close while this remains TBD.]
  - [NEEDS CLARIFICATION: Q-4 — LiteLLM access configuration field name and location in `contract.yaml`. Whether to introduce a new top-level `factory.litellm` key, reuse an existing config block, or attach to a per-app config section. Resolution path: Architecture confirms during the design-contracts.md authoring step; Contract C8 carries the field-name placeholder under `### Open Decisions` until then. This question does NOT defer to a downstream ticket — it MUST resolve before SPEC_READY flips to true.]

## Explicit Exclusions
- Excluded item 1: implementation of any of the eight contracts (e.g., creating CODEOWNERS entries, provisioning the bot identity, emitting events, authoring the actual module wrappers/make targets/skill runbooks/App manifest enumerated under C8) — all owned by their respective Phase 1 tickets.
- Excluded item 2: enumeration of bounded contexts beyond the placeholder structure — owned by #337 with Architecture input.
- Excluded item 3: ADR drafts for the ten decisions in scope of #337 — those are #337's deliverables, not this work item's.
- Excluded item 4: any change to existing `docs/blueprint/contracts/` or `docs/blueprint/governance/` documents — this work item only creates new files under `docs/blueprint/autonomous-factory/` and `docs/blueprint/architecture/decisions/`.
- Excluded item 5: concrete consumer-specific values (any consumer repo's bot login, CODEOWNERS slugs, dashboard target, LiteLLM access configuration) — owned by each consumer repo's own factory-onboarding work and forbidden by FR-016 from appearing in this document.
- Excluded item 6: introduction of a new consumer-inheritance mechanism beyond the existing blueprint `contract.yaml` — Contract C8 enumerates surface only; the inheritance mechanism is the existing one (FR-015).
