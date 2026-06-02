# ADR: Factory Personas + Skills Roster (Child A of #333)

**Status:** approved
**Date:** 2026-06-02
**Approved:** 2026-06-02
**ADR technical decision sign-off:** approved (sbonoc, PR #362)
**Issue:** #360 (Child A of #333)
**Spec:** `specs/2026-06-02-issue-360-factory-personas-skills/`
**Parent ADR:** [`ADR-issue-337-persona-skill-contract.md`](ADR-issue-337-persona-skill-contract.md)
**Extensibility classification:** `extensible` (the persona/skill files themselves are extensible per the design-contracts § Extensibility tier dimension default; the persona/skill *contract* in the parent ADR remains `sealed`).

## Context

Phase 0 pinned the persona/skill contract (`ADR-issue-337-persona-skill-contract.md`): skills are verbs, personas are nouns, personas invoke skills, no AI persona maps 1:1 to a human canonical sign-off role. The contract is set, but the *roster* — which personas exist, which skills they invoke, and which new skills the factory needs — was deferred to Phase 1 ticket #333. At SDD intake on 2026-06-02 #333 was split into Child A (this work item — governance docs only) and Child B (`#361`, the orchestrator service). Child A authors the persona files, the new skill `SKILL.md` runbooks, and the Contract C8 enumeration rows. It does NOT introduce runtime code.

## Decision Drivers

- **One-to-one cohesion with the persona/skill contract.** Every persona authored here must satisfy the four sealed clauses of the parent ADR. The roster is the place those clauses become concrete: ten files, each with an explicit `## Skills Invoked` list that resolves to existing skills or to the 10 new skills authored alongside.
- **Auditable C7 attribution.** Every persona must declare which C7 `phase` enum value(s) its actions emit, so the lifecycle event stream remains traceable from static text alone. (NFR-OBS-001.)
- **Consumer-inheritance parity.** All 20 new files are part of the Contract C8 consumer-shipped surface, default extensibility tier `extensible`, default stability tier `stable`. Consumer instances inherit them identically via the existing blueprint `contract.yaml` mechanism.
- **Drift detection via #342.** Front-matter `blueprint-version: <semver>` lets the extended `/blueprint-consumer-upgrade` skill detect when a consumer's local file lags behind the blueprint version.
- **Two human gates only.** Per the autonomy posture established for Epic #332, the spec sign-off gate and the bounded-context human merge gate are the two human checkpoints. No persona authored here claims either of those gates or the four canonical sign-off roles.
- **Split, not bundle, runtime mechanics out of this child.** The orchestrator that dispatches personas, the jsonschema validator that enforces `## Required Output Schema`, the RabbitMQ publisher that emits C7 events at phase boundaries, and the reviewer-rotation picker are all Child B responsibilities. This ADR authors a static surface; it does not adopt a runtime architecture.

## Decision

The factory persona roster comprises EXACTLY ten personas, partitioned into an implementer half (6) and a reviewer half (4):

**Implementer half (6).**

| File | Role | Owned lifecycle skills |
|---|---|---|
| `.agents/personas/po-analyst.md` | PO / Analyst | `blueprint-sdd-step01-intake`, `blueprint-sdd-step02-resolve-questions`, `blueprint-spec-review-prep` |
| `.agents/personas/architect.md` | Architect | `blueprint-sdd-step03-spec-complete` (cross-bounded-context scope) |
| `.agents/personas/tech-lead.md` | AI Tech Lead | `blueprint-ticket-triage-size` (entry), `blueprint-ticket-decompose-light` (conditional), `blueprint-sdd-step04-plan-slicer`; orchestrates handoffs |
| `.agents/personas/implementer.md` | Implementer | `blueprint-sdd-step05-implement`; `blueprint-pr-review-respond` on reject rounds |
| `.agents/personas/devsecops-qa.md` | DevSecOps / QA | Guardrail across step05 → step06 → step07; owns `hardening_review.md` via `make quality-hardening-review`; owns `blueprint-human-review-prep` |
| `.agents/personas/doc-keeper.md` | Documentation Keeper | `blueprint-sdd-step06-document-sync`; produces spec-vs-changes diff |

**Reviewer half (4) — power the new `agent-pr-review` phase.**

| File | Review dimension (non-overlapping per FR-013) |
|---|---|
| `.agents/personas/security-reviewer.md` | Credentials, PII handling, attack surface, dependency CVEs, container constraints |
| `.agents/personas/architecture-reviewer.md` | Bounded-context discipline, contract adherence, cross-context impact (MUST emit explicit cross-context impact summary for the human merge gate per FR-014) |
| `.agents/personas/contract-reviewer.md` | Public API / schema changes, backward compatibility, consumer impact |
| `.agents/personas/test-coverage-reviewer.md` | Test presence and meaningfulness for changed code paths, positive-path assertions per `AGENTS.md` policy |

The factory skill surface gains EXACTLY ten new skills under `.agents/skills/`:

| Skill | Owning persona | Purpose |
|---|---|---|
| `blueprint-ticket-triage-size` | Tech Lead | First step on every ticket; classifies size; always emits boundary candidates (data feed for `#338`). |
| `blueprint-ticket-decompose-light` | Tech Lead | Conditional on triage = large-decomposable: slice into 2–5 sub-tickets along bounded-context / layer / feature-behaviour boundaries (per Phase 0 light-decomposition ADR). |
| `blueprint-agent-secret-scan` | DevSecOps / QA | Pre-execution scan; fails fast on prod credential or PII patterns. |
| `blueprint-agent-handoff` | All implementer personas | Explicit baton-pass; structured handoff note into PR body. |
| `blueprint-spec-revision-handoff` | Tech Lead | Routes a child ticket back to a fresh po-analyst when a parent-spec grounding gap is detected; other personas MUST NOT invoke this skill. |
| `blueprint-spec-review-prep` | PO / Analyst | Spec-quality artifact for the spec gate reviewers. |
| `blueprint-human-review-prep` | Documentation Keeper | Formats Draft PR for the human merge gate: spec-vs-changes diff + reviewer checklist. |
| `blueprint-sdd-step08-agent-pr-review` | All 4 reviewer personas | Drives the new `agent-pr-review` phase. |
| `blueprint-pr-review-respond` | All 4 reviewer personas | Parses implementation-round review comments and routes fix requests back to the implementer; bounded by Phase 0 reject-rerun cap. |
| `blueprint-agent-stop-cleanup` | All personas | Pairs with the `agent-stop` label; cleans up workspace, journals kill reason, posts comment. |

Every new `SKILL.md` carries a `## Required Output Schema` section with a fenced ```yaml jsonschema``` block per the parent persona/skill contract ADR (clause 3 — skills declare their output contract). Every persona file and every new `SKILL.md` carries `blueprint-version: <semver>` in YAML front-matter per `docs/blueprint/autonomous-factory/design-contracts.md` § Upstream-candidate front-matter convention. All 20 files are enumerated as `stable` + `extensible` rows in `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c).

### Naming-convention reading for clause 4 (resolves OQ-3)

Clause 4 of the parent ADR (`ADR-issue-337-persona-skill-contract.md`) reads: "no AI persona maps 1:1 to a human canonical sign-off role" — meaning no AI persona implies sign-off authority. Two readings were considered for whether persona *names* (`tech-lead`, `devsecops-qa`, `architect`, `po-analyst`, `doc-keeper`) violate that clause:

- **Strict-naming reading (rejected).** Any persona whose name string overlaps with a recognised human role title violates clause 4 and MUST be renamed (for example `tech-lead` → `decomposer`, `architect` → `cross-context-planner`).
- **Work-domain reading (adopted).** Clause 4 is violated only when a persona *takes* a canonical sign-off action — that is, emits one of the four canonical sign-off phrases defined in `AGENTS.md § Sign-off Phrases (Deterministic)` or otherwise asserts sign-off authority in its Definition of Done or Strict Guardrails. Persona names that overlap with human role titles are permitted as long as the persona's responsibilities and guardrails make explicit that the persona MUST NOT sign off and the human canonical sign-off remains with the human reviewer.

The work-domain reading is the one that operates in this ADR and across the 10 persona files. It is consistent with the rejection of Option D below ("`architect-ai-signoff`" being rejected precisely because the suffix `-signoff` encodes sign-off authority — not because the persona name overlapped with the human role "architect"). FR-012 + T-105 enforce the adopted reading mechanically: T-105 scans every persona file's Definition of Done and Strict Guardrails sections and fails if it finds any of the four canonical sign-off phrases or any text that asserts sign-off authority. Name overlap alone does not trigger T-105.

## Options Considered

### Option A — Ten-persona roster (6 implementer + 4 reviewer) with 10 new skills (chosen)

Adopt the roster above.

**Pros:** matches the issue body and the parent persona/skill contract; gives each reviewer a single non-overlapping dimension (FR-013) which keeps attribution clean in the `agent-pr-review` phase; reuses the existing 7 SDD step skills without modification; defers runtime mechanics to Child B; consumer instances inherit the whole surface identically via existing C8 machinery.

**Cons:** 20 files in one PR is a large reviewer surface. Mitigation: every file follows a fixed template anchored on FR-009 / FR-010 / FR-013 / FR-014; the new pytest checks (T-101…T-107) catch most deviations mechanically.

### Option B — Persona roster only; defer new skills to Child B (rejected)

Author the 10 persona files but leave the 10 new skills as stubs, to be authored by Child B alongside the orchestrator.

**Rejected:** breaks FR-011 (`## Skills Invoked` must resolve). Either we ship phantom skill paths (validation fails) or we omit them from persona files (the personas become incomplete, and Child B would have to amend them later). Worse, it couples skill authoring to runtime work in Child B and slows down the `agent-pr-review` phase definition that only needs static content.

### Option C — Split persona PR from skill PR (rejected)

Two children, one for the 10 personas and one for the 10 skills.

**Rejected:** same FR-011 failure mode as Option B during the interim, with no reduction in total review surface. The user confirmed Option A at decomposition step.

### Option D — Author personas for the four human sign-off roles too (rejected at the parent ADR layer)

Add `product-ai`, `architect-ai-signoff`, `security-ai`, `operations-ai` personas that grant the canonical sign-off phrases on the human's behalf.

**Rejected** by `ADR-issue-337-persona-skill-contract.md` clause 4. Re-stated here so the roster is unambiguous: no persona in this roster claims sign-off authority. FR-012 + T-105 enforce this mechanically.

## Consequences

- Child B (`#361`) can dispatch personas and validate skill outputs against the `## Required Output Schema` blocks without further design work on the static surface.
- `#342`'s extended `/blueprint-consumer-upgrade` can detect drift on each of the 20 files via the `blueprint-version` front-matter.
- `#338`'s triage/decomposition data feed has a documented schema (defined in the `## Required Output Schema` of `blueprint-ticket-triage-size` and `blueprint-ticket-decompose-light`) to consume once Child B persists the events.
- The new `agent-pr-review` phase is documented and ready for Child B to wire into the orchestrator state machine.
- Consumer instances that adopt the autonomous factory inherit the entire 20-file surface identically via the existing blueprint `contract.yaml` mechanism (Contract C3 identical convention; C8 enumeration). Consumer shadows under `.agents/personas/consumer/` and `.agents/skills/consumer/` remain permitted per `docs/blueprint/autonomous-factory/design-contracts.md` § Consumer-extension discovery convention, with `upstream-candidate: true` front-matter for contribution-intent signalling per the same document § Upstream-candidate front-matter convention.
- ~~Two follow-up proposals are recorded in `spec.md § Potential Deferred Proposals`~~ Both prior follow-up proposals were resolved in-scope on 2026-06-02 by reviewer comment on PR #362: OQ-1 (B) — CLAUDE.md gains EXACTLY ONE new slash-command row for `/blueprint-sdd-step08-agent-pr-review` (FR-019); OQ-2 (B) — the 8 existing SDD skill `SKILL.md` files (`step01`–`step07` + `traceability-keeper`) gain `## Required Output Schema` sections (FR-020). The remaining 9 new skills stay persona-invoked-only (no slash-command rows).

## References

- Parent ADR: [`ADR-issue-337-persona-skill-contract.md`](ADR-issue-337-persona-skill-contract.md)
- Related ADRs: [`ADR-issue-337-light-decomposition-policy.md`](ADR-issue-337-light-decomposition-policy.md), [`ADR-issue-337-triage-size-threshold.md`](ADR-issue-337-triage-size-threshold.md), [`ADR-issue-337-reviewer-model-heterogeneity.md`](ADR-issue-337-reviewer-model-heterogeneity.md), [`ADR-issue-337-reject-rerun-cap.md`](ADR-issue-337-reject-rerun-cap.md)
- Design contracts: `docs/blueprint/autonomous-factory/design-contracts.md` § C3, § C7, § C8, § Extensibility tier dimension, § Consumer-extension discovery convention, § Upstream-candidate front-matter convention
- Spec: `specs/2026-06-02-issue-360-factory-personas-skills/spec.md`
- Issue: #360 (Child A of #333); sibling Child B: `#361`
- `AGENTS.md § Sign-off Policy` and § Sign-off Phrases (Deterministic)
