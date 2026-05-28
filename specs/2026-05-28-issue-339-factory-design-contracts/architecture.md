# Architecture

## Context
- Work item: 2026-05-28-issue-339-factory-design-contracts
- Owner: bonos
- Date: 2026-05-28

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2 (not exercised — documentation-only work item)
- Frontend stack profile: vue_router_pinia_onyx (not exercised — documentation-only work item)
- Test automation profile: pytest_vitest_playwright_pact (not exercised — validation is `make docs-build` and `make docs-smoke`)
- Agent execution model: specialized-subagents-isolated-worktrees (this intake run is single-agent; no worktree partitioning required for a single-file deliverable)

## Problem Statement
- What needs to change and why: the four Phase 1 autonomous-factory tickets (#333 personas, #334 Confidential K8s, #335 OpenHands+LiteLLM, #336 webhooks) and the Phase 0 sibling #337 all depend on the same cross-ticket conventions (branch naming, spec directory layout for decomposed work, persona↔microagent mapping, integration AC format, factory bot identity + SoD detection, CODEOWNERS team slugs, metrics dashboard target + event schema). Without one pinned source, each ticket invents its own values for the same shared concepts and Phase 1 ships with inconsistent assumptions discovered only at integration time. The two failure modes already foreseeable are: (1) #335 and #336 disagreeing on branch and spec paths; (2) #333 persona DoDs referencing a bot identity #334 has not provisioned; (3) #337 populating CODEOWNERS with team names #336 does not know to allowlist.
- Scope boundaries: this work item produces exactly two new artifacts — the design-contracts document at `docs/blueprint/autonomous-factory/design-contracts.md` and one summary ADR at `docs/blueprint/architecture/decisions/ADR-issue-339-factory-design-contracts.md`. The contracts pinned are the seven listed in the spec (C1–C7).
- Out of scope: implementation of any contract (CODEOWNERS population, bot provisioning, event emission, persona file creation, etc.); enumeration of concrete bounded contexts beyond a placeholder structure; #337's own ten ADRs; any change to existing `docs/blueprint/contracts/` or `docs/blueprint/governance/` documents.

## Bounded Contexts and Responsibilities
- Context A — Factory Governance (this work item): owns cross-ticket interface conventions for the autonomous software factory. Surface: the design-contracts document and its summary ADR. Editorial authority: Architecture, with Security and Operations co-signing.
- Context B — Phase 1 implementers (downstream consumers): #333, #334, #335, #336 own implementation of the contracts. They MUST NOT redefine values pinned in Context A; they MAY surface deltas via PR comments that update Context A.
- Context C — Phase 0 sibling #337: depends on Context A for CODEOWNERS team slugs (Contract C6), bot identity SoD rule (Contract C5), and event schema (Contract C7). #337's own ADRs are not Context A's responsibility; the dependency is unidirectional.

## High-Level Component Design
- Domain layer: governance content — the seven contract sections C1–C7. Each section is self-contained and addressable by section anchor.
- Application layer: none (documentation-only).
- Infrastructure adapters: none.
- Presentation/API/workflow boundaries: the deliverable surfaces through the existing `docs/blueprint/` rendering pipeline (`make docs-build` / `make docs-smoke`). The ADR surfaces through the same pipeline at the conventional ADR path.

## Integration and Dependency Edges
- Upstream dependencies: Epic #332 (provides the initiative framing); `AGENTS.md § Sign-off Phrases` (provides canonical sign-off vocabulary used in FR-012); `AGENTS.md § SDD Artifact Contract` (provides the spec directory layout convention reused in Contract C2).
- Downstream dependencies: #333 (Contracts C2, C3, C4), #334 (Contract C5), #335 (Contracts C1, C3, C5, C7), #336 (Contracts C1, C2, C4, C5, C6, C7), #337 (Contracts C5, C6, C7), #338 (Contracts C2, C4).
- Data/API/event contracts touched: introduces the factory lifecycle-event schema definition (Contract C7) — definition only; emission and consumption are owned by #336, #335, and #337 respectively.

## Non-Functional Architecture Notes
- Security: Contract C5 specifies the deterministic factory-bot identity rule used by multi-author SoD detection. The rule MUST use exact-string equality on the GitHub login; substring or regex heuristics MUST NOT be used (NFR-SEC-001). No secrets or credentials live in this document.
- Observability: Contract C7 defines the minimum lifecycle-event field set. The schema must be expressed in a form downstream consumers can adopt without re-specification (NFR-OBS-001). Eight fields are required: `ticket_id`, `parent_ticket_id`, `phase`, `persona`, `model`, `timestamp`, `outcome`, `rerun_round`.
- Reliability and rollback: rollback for this work item is reverting the design-contracts.md change in isolation. No runtime code depends on the document's contents at runtime; downstream tickets adopt values during their own implementation. `Referenced by:` lines per contract section make blast radius explicit (NFR-REL-001).
- Monitoring/alerting: no runtime monitoring introduced. Documentation drift is caught by `make docs-build` and `make docs-smoke` (NFR-OPS-001) at the next PR that touches related docs.

## Risks and Tradeoffs
- Risk 1 — Open Decisions backlog: three contracts (C5 bot handle, C6 team slugs + bounded contexts, C7 dashboard platform) carry deferred values resolved during #334 / #337. If those tickets close before resolving them, downstream dependents will adopt placeholders. Mitigation: each open decision names the deferring ticket and is gated as a non-closure condition on that ticket; AC-004 enforces this in the document; spec sign-off acknowledges the deferral path.
- Risk 2 — Document churn during Phase 1: as #333–#337 implement the contracts they may surface deltas requiring spec amendments. Mitigation: each contract section is independently editable; `Referenced by:` lines localize the impact; amendments follow the same SDD/sign-off flow as the original document.
- Tradeoff 1 — single-file vs many-ADRs: chose single-file (per OPTION_A in spec.md). Pro: one place to read, easier cross-references, fewer sign-off cycles. Con: any contract amendment touches the same file (cosmetic blast-radius). Mitigation accepted: per-section `Referenced by:` lines make true blast-radius visible at review.
- Tradeoff 2 — strict normative language in a governance doc: governance prose typically uses softer wording. We constrain ourselves to `MUST/MUST NOT/SHALL/EXACTLY ONE OF` per `AGENTS.md § Normative Language Policy`. Pro: removes interpretive drift across implementer agents. Con: prose reads as terse; informative context lives in dedicated non-normative sections of the deliverable.
