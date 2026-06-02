# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 2
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: none
- authorized-by: none

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-013 (managed services) and SDD-C-014 (local-first runtime) do not apply — this work item ships no runtime stack changes. SDD-C-015 (app onboarding Make-target contract) does not apply — no app-delivery workflow is created or modified. SDD-C-018 (upstream defect escalation) does not apply — no blueprint defect workaround. SDD-C-022 (HTTP smoke gate) does not apply — no HTTP route changes. SDD-C-023 (filter/payload positive-path assertion) does not apply — no filter/payload-transform logic. SDD-C-024 (finding-to-test translation) remains applicable in principle but is expected to be inert for a pure governance-doc ticket; any pre-PR finding MUST still be translated into a failing automated test first.

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
- Has user-facing flow: false
  <!-- Pure governance-doc and skill-runbook authoring; no UI signals present in scope. -->
- E2E gate classification: N/A
  <!-- No user-facing flow → gate does not apply. -->

## Objective
- Business outcome: Establish the AI persona roster (6 implementers + 4 reviewers) and the 10 new SDD/factory skill runbooks that power the STACKIT autonomous software factory's SDD execution, with extensibility/inheritance conventions consumers inherit identically via the existing blueprint `contract.yaml` mechanism.
- Success metric: Exactly 10 persona files exist under `.agents/personas/` and 10 new skill directories exist under `.agents/skills/`, each with complete content, validated by `make quality-sdd-check` and the new persona/skill content checks; the Contract C8 enumeration in `docs/blueprint/autonomous-factory/design-contracts.md` lists each item with stability tier `stable` and extensibility tier `extensible`.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 The work item MUST author exactly 10 persona files under `.agents/personas/<name>.md` partitioned as 6 implementer personas (`po-analyst.md`, `architect.md`, `tech-lead.md`, `implementer.md`, `devsecops-qa.md`, `doc-keeper.md`) and 4 reviewer personas (`security-reviewer.md`, `architecture-reviewer.md`, `contract-reviewer.md`, `test-coverage-reviewer.md`).
- FR-002 The work item MUST author exactly 10 new skill directories under `.agents/skills/<skill-name>/`, each containing a `SKILL.md` runbook: `blueprint-ticket-triage-size`, `blueprint-ticket-decompose-light`, `blueprint-agent-secret-scan`, `blueprint-agent-handoff`, `blueprint-spec-revision-handoff`, `blueprint-spec-review-prep`, `blueprint-human-review-prep`, `blueprint-sdd-step08-agent-pr-review`, `blueprint-pr-review-respond`, `blueprint-agent-stop-cleanup`.
- FR-003 Every newly authored `SKILL.md` MUST carry a `## Required Output Schema` section containing EXACTLY ONE fenced ```yaml jsonschema``` code block defining the structured artifact the skill returns (per `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md`). The schema MUST be self-contained valid JSON Schema (draft-07 or later) authored inside the YAML block.
- FR-004 `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) MUST enumerate each of the 10 persona files (by full path `.agents/personas/<name>.md`) and each of the 10 new skill directories (by full path `.agents/skills/<skill-name>/`) as separate rows with stability tier `stable` and extensibility tier `extensible`, owning ticket `#333` (this child).
- FR-005 Every new persona file and every new `SKILL.md` MUST carry the default extensibility tier `extensible`; the 4 reviewer personas MUST be explicitly marked `extensible` so consumer instances can shadow them under the namespaced consumer subdirectory convention defined in `docs/blueprint/autonomous-factory/design-contracts.md` § Consumer-extension discovery convention (`.agents/personas/consumer/<basename>.md`, `.agents/skills/consumer/<skill-name>/`). No item authored by this work item appears in the design-contracts sealed list.
- FR-006 Every new persona file and every new `SKILL.md` MUST carry `blueprint-version: <semver>` in YAML front-matter so the extended `/blueprint-consumer-upgrade` skill from epic #342 can detect drift. The semver value MUST be the current blueprint release version at authoring time.
- FR-007 Persona and skill files MUST document that consumer-authored extensions under `.agents/personas/consumer/` and `.agents/skills/consumer/` are permitted to carry `upstream-candidate: true` in YAML front-matter to signal upstream-contribution intent (per the upstream-candidate convention defined in `docs/blueprint/autonomous-factory/design-contracts.md`); absence of the flag means strictly-local. The convention is mentioned once in the persona template documentation and the new-skill template documentation; per-file repetition is not required.
- FR-008 No persona or skill file authored by this work item MUST contain placeholder tokens. Specifically, the strings `TBD`, `TODO`, `FIXME`, `<...>`-style angle-bracket placeholders, and the SDD clarification marker token defined in `AGENTS.md § Clarification Marker Policy` MUST NOT appear in any new persona `.md` or new `SKILL.md`.
- FR-009 The `devsecops-qa.md` persona's `## Definition of Done (DoD)` section MUST mandate, as separate bullet items: (a) exclusion of production PII from any artifact, (b) non-root container constraints for any runtime workload the persona introduces, (c) `hardening_review.md` produced via `make quality-hardening-review` and clean (zero outstanding findings) before handoff to `blueprint-sdd-step07-pr-packager`.
- FR-010 The `tech-lead.md` persona's `## Definition of Done (DoD)` section MUST mandate: (a) `blueprint-ticket-triage-size` runs first on every ticket, (b) `blueprint-ticket-decompose-light` MUST be invoked whenever triage classifies the ticket as large-decomposable, (c) every sub-ticket grounds in the parent spec and cites its boundary type, (d) sub-ticket fan-out MUST NOT exceed the maximum defined in the Phase 0 ADR on light decomposition policy (`docs/blueprint/architecture/decisions/ADR-issue-337-light-decomposition-policy.md`).
- FR-011 Every reference to a skill in any persona's `## Skills Invoked` section MUST resolve to EXACTLY ONE OF the following: an already-shipped skill under `.agents/skills/`, or one of the 10 new skill directories created by this work item. References that do not resolve MUST fail validation.
- FR-012 No persona file MUST claim authority for any of the four human canonical sign-off roles (Product, Architecture, Security, Operations) or for the bounded-context human merge gate. Concretely: the `# Persona:` heading, `## Role Objective`, `## Activation Triggers`, and `## Definition of Done (DoD)` sections of every persona MUST NOT contain any of the four canonical sign-off phrases (`SPEC_PRODUCT_READY: approved`, `ARCHITECTURE_SIGNOFF: approved`, `SECURITY_SIGNOFF: approved`, `OPERATIONS_SIGNOFF: approved`) or any plain-language statement asserting that the persona grants such a sign-off.
- FR-013 The `## Review Dimensions` sections of the four reviewer personas MUST be non-overlapping: each named review-dimension item MUST appear in EXACTLY ONE reviewer persona file. Duplicate items across reviewer personas MUST fail validation.
- FR-014 The `architecture-reviewer.md` persona MUST contain a `## Cross-Context Impact Reporting` section providing a structured template ready to drop into the PR body for the human merge reviewer. The template MUST include fields for: bounded contexts touched, downstream consumers impacted, contract-surface deltas, and rollback risk.
- FR-015 `blueprint-ticket-triage-size`'s `SKILL.md` MUST document that the skill: (a) classifies the ticket into `small | medium | large-decomposable | escalate` per the Phase 0 threshold ADR, (b) always emits the bounded-context candidates it identified as part of its `## Required Output Schema` output, (c) when the classification is `large-decomposable`, names `blueprint-ticket-decompose-light` as the explicit persona-orchestrated next step. The runtime persistence of the triage output for the #338 data feed is owned by Child B (orchestrator); this work item only authors the documented contract.
- FR-016 No newly authored `SKILL.md` MUST contain a directive that triggers another skill (no `Skill(` invocation, no `/blueprint-…` slash-command directive inside a step block, no `Invoke skill:` directive). Skill composition is a persona-layer responsibility, per `ADR-issue-337-persona-skill-contract.md` clause 3. Skills are permitted to reference other skills *by name* in prose (for example, "the persona will subsequently invoke X"), but MUST NOT directive-invoke them.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 No new persona or skill file MUST contain credentials, API tokens, private keys, or PII. The `blueprint-agent-secret-scan` skill ships as the runtime enforcement layer that future persona executions invoke; for this authoring work, the static check is performed by `git-secrets`/`detect-secrets` style scanning over the new files (covered by an automated test, see AC-006).
- NFR-OBS-001 Every persona file MUST declare, within its `## SDD Cycle Stakes` section, which Contract C7 lifecycle `phase` enum value(s) its actions emit events for. The 10 new skill `SKILL.md` files MUST each indicate (in their `## Required Output Schema` block or an adjacent section) which `phase` enum value the orchestrator emits when the skill completes. This produces a complete persona→phase and skill→phase mapping auditable from static text alone.
- NFR-REL-001 The persona/skill invocation graph MUST be reproducible: for the same input ticket and same persona, the documented skill invocation order in `## Skills Invoked` MUST be deterministic. Persona files MUST NOT contain language that implies non-deterministic, random, or model-choice-dependent skill selection. Rollback is trivial — these are content-only files; revert the commit.
- NFR-OPS-001 Every persona file MUST declare its `## Activation Triggers` (the event or condition that causes a runtime to instantiate this persona) and MUST reference `blueprint-agent-stop-cleanup` in its handoff section so that the persona's runtime state can be cleaned up under the `agent-stop` label (per #336 contract).
- NFR-A11Y-001 N/A — this work item ships no UI; it ships persona and skill markdown files under `.agents/` consumed by the autonomous factory orchestrator and by Claude Code locally.

## Normative Option Decision
- Option A: Author all 10 personas + 10 skills in this single child A PR (governance-only).
- Option B: Split persona authoring (one PR) from skill authoring (a second PR).
- Selected option: OPTION_A
- Rationale: Personas and skills are tightly coupled by FR-011 (every `## Skills Invoked` reference MUST resolve). Splitting would force EXACTLY ONE OF: staging a "phantom skills" PR first, or breaking FR-011 mid-split. Both halves are pure markdown with zero runtime; reviewer cognitive load is the only cost and is manageable because each file follows a fixed template. Confirmed by user during decomposition step (2026-06-02).

## Contract Changes (Normative)
- Config/Env contract: no change.
- API contract: no change.
- OpenAPI / Pact contract path: none
- Event contract: this work item DOCUMENTS persona→C7 phase and skill→C7 phase mapping (NFR-OBS-001); no change to the C7 schema itself (which is sealed under the design-contracts.md sealed list).
- Make/CLI contract: no new Make targets. This work item MUST NOT add slash-command rows to `CLAUDE.md`'s Skills table for any of the 10 new skills; the 9 non-step08 skills are persona-invoked only, and the slash-command entry for `blueprint-sdd-step08-agent-pr-review` is deferred to the follow-up tracked as OQ-1 below.
- Docs contract: `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) gains 20 new rows (10 personas + 10 skills) per FR-004.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [Exactly 10 persona files exist with correct roster split] — verified by T-101, which MUST assert that the set of files matching `.agents/personas/*.md` equals exactly the 10 named files in FR-001 (6 implementer + 4 reviewer), no more and no fewer.
- AC-002 [Exactly 10 new skill directories exist with SKILL.md present] — verified by T-101, which MUST assert each of the 10 named skill directories from FR-002 contains a `SKILL.md` file.
- AC-003 [Every new SKILL.md has `## Required Output Schema` with one fenced yaml jsonschema block] — verified by T-102, which MUST assert each new SKILL.md contains EXACTLY ONE `## Required Output Schema` heading followed by EXACTLY ONE fenced ```yaml jsonschema``` block whose body parses as valid JSON Schema.
- AC-004 [Contract C8 enumerates 10 personas + 10 skills with `stable` + `extensible` tiers] — verified by T-102, which MUST assert each of the 20 paths from FR-001 + FR-002 appears as a row in `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) with stability tier `stable` and extensibility tier `extensible`.
- AC-005 [Every persona + every new SKILL.md carries `blueprint-version` front-matter] — verified by T-102, which MUST assert YAML front-matter parses on each of the 20 files and contains a `blueprint-version` key whose value matches the semver pattern `^\d+\.\d+\.\d+(-[\w.]+)?$`.
- AC-006 [No placeholders or secrets in any new persona/skill file] — verified by T-103, which MUST assert no occurrence of `TBD`, `TODO`, `FIXME`, the SDD clarification marker token (as defined in `AGENTS.md § Clarification Marker Policy`), or unquoted `<...>`-style angle-bracket placeholders in any of the 20 new files; AND that a baseline secret-pattern scan (covering AWS access keys, private-key headers, bearer tokens) finds zero matches.
- AC-007 [DevSecOps/QA persona DoD enforces the three mandated items] — verified by T-104, which MUST assert the three FR-009 phrases (PII exclusion, non-root container constraint, `hardening_review.md` clean before step07 handoff) each appear as separate bullet items under the `## Definition of Done (DoD)` heading of `.agents/personas/devsecops-qa.md`.
- AC-008 [Tech Lead DoD mandates triage-first + light-decompose conditional + boundary citation + max fan-out] — verified by T-104, which MUST assert the four FR-010 phrases appear as separate bullet items under the `## Definition of Done (DoD)` heading of `.agents/personas/tech-lead.md`.
- AC-009 [Every `## Skills Invoked` reference resolves to an existing skill] — verified by T-105, which MUST assert every `.agents/skills/<name>` path token under any `## Skills Invoked` section of any persona file resolves to a directory that exists in the repo after the change.
- AC-010 [No persona claims human sign-off role] — verified by T-105, which MUST assert no persona file contains the four canonical sign-off phrases from FR-012 nor any plain-language equivalent ("grants Product sign-off", "approves architecture sign-off", "approves security sign-off", "approves operations sign-off").
- AC-011 [Reviewer dimensions non-overlapping] — verified by T-106, which MUST assert the union of bulleted items under `## Review Dimensions` across the four reviewer personas contains zero duplicates after case-folding and whitespace-normalization.
- AC-012 [Architecture-reviewer Cross-Context Impact Reporting template present with required fields] — verified by T-106, which MUST assert `architecture-reviewer.md` contains a `## Cross-Context Impact Reporting` section with subheadings or bullets for: bounded contexts touched, downstream consumers impacted, contract-surface deltas, rollback risk.
- AC-013 [No skill directive-invokes another skill] — verified by T-107, which MUST assert no new SKILL.md contains any of: a `Skill(` token, a `/blueprint-` token on a line that starts with `Invoke`, `Run`, `Call`, or `Execute`, or an `Invoke skill:` directive. Prose mentions of skill names elsewhere remain permitted.

## Informative Notes (Non-Normative)
- Context: Phase 0 (#337 + #339) is now merged and pinned the persona/skill contract, light-decomposition policy, triage-size threshold, reviewer-rotation policy, C7 emission mechanism, and the Contract C8 consumer-shipped surface enumeration. Phase 1 ticket #333 was split at intake (2026-06-02) into Child A (this work item — governance docs only) and Child B (orchestrator service). Child B remains blocked by #335 + #336 spec-complete; this child can ship independently.
- Tradeoffs: Static markdown content with no runtime means tests are file-existence + grep + YAML/JSON parsing, which is brittle to template drift in the long run. Mitigation: tests are anchored on the explicit FR phrases above so drift produces a clear test failure pointing back to the spec.
- Clarifications: none

### Open Questions (Tracked)

| ID | Question | Recommended resolution | Owner |
|---|---|---|---|
| OQ-1 | Should `CLAUDE.md`'s Skills slash-command table gain a row for the new `blueprint-sdd-step08-agent-pr-review` skill? | Defer to a follow-up chore. The step08 skill is invoked by the runtime orchestrator (Child B) on PR open, not by a human; no slash-command access is required. The remaining 9 new skills are persona-invoked only. | Software Engineer |
| OQ-2 | Should the existing 7 SDD step skills (`step01`–`step07`) and `blueprint-sdd-traceability-keeper` retroactively gain `## Required Output Schema` sections for parity with the new skills? | Defer to a separate ticket (recommend a chore under Epic #332). The orchestrator-side validator (Child B) is not yet implemented, so adding schemas to the existing skills today produces unused content. When Child B lands, retrofit in one pass and apply uniformly. | Software Engineer |

## Explicit Exclusions
- Orchestrator service implementation (Python Deployment, Helm chart) — owned by Child B (`#361`).
- OpenHands API client — depends on #335.
- RabbitMQ publisher and C7 phase-boundary emission to the durable bus — owned by Child B.
- Reviewer-rotation picker that reads the most recent `phase: implement` C7 event — owned by Child B.
- jsonschema runtime validator — owned by Child B; this work item only authors the schemas.
- Retroactive `## Required Output Schema` additions to existing 7 SDD step skills — see OQ-2.
- Slash-command table updates in `CLAUDE.md` for the 10 new skills — see OQ-1.

## Potential Deferred Proposals
- Add `## Required Output Schema` to existing 7 SDD step skills (`step01`–`step07`) + `traceability-keeper`, once Child B's validator is in place. Owner: Software Engineer. Trigger: Child B (`#361`) merges.
- Add `blueprint-sdd-step08-agent-pr-review` to CLAUDE.md Skills table once the orchestrator (`#361`) is operational and human invocation paths are defined. Owner: Software Engineer. Trigger: Child B merges.
