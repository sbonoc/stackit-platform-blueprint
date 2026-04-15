# SDD Policy Mapping

This file maps repository governance guardrails to Spec-Driven Development (SDD) artifacts.

## Lifecycle Deliverables

| Phase | Required Output | Canonical File |
|---|---|---|
| Discover | Problem statement, scope, constraints, clarified business requirements, clarified non-functional requirements | `spec.md` |
| High-Level Architecture | Bounded contexts, dependency direction, integration boundaries, stack-specific architecture shape | `architecture.md` |
| Specify | Normative requirements, selected option, acceptance criteria, contract impacts | `spec.md` |
| Plan | Sequenced slices, rollout/rollback strategy, shift-left validation strategy | `plan.md`, `tasks.md` |
| Implement | Code/docs/contracts aligned with approved spec | Implementation diff |
| Verify | Validation evidence + requirement traceability | `traceability.md` |
| Verify | Graph-based dependency/evidence drift checks | `graph.yaml`, `traceability.md` |
| Document | Blueprint + consumer documentation updates and diagram sync | `docs/blueprint/**`, `docs/platform/**` |
| Operate | Monitoring/alerting/runbook ownership and diagnostics | `traceability.md` |
| Publish | Reviewer-ready PR packaging context and hardening report | `pr_context.md`, `hardening_review.md`, PR template |

## Readiness Gate Mapping

Before implementation, every work item must satisfy the blocking gate in `spec.md`:

- `SPEC_READY=true`
- `Open questions count: 0`
- `Unresolved alternatives count: 0`
- `Unresolved TODO markers count: 0`
- `Pending assumptions count: 0`
- `Open clarification markers count: 0`
- Approved sign-offs for `Product`, `Architecture`, `Security`, `Operations`

If required inputs are missing, mark the spec with `BLOCKED_MISSING_INPUTS` and keep `SPEC_READY=false`.

## Assumption Policy

- Code assistants MUST NOT invent missing requirements during `Discover`, `High-Level Architecture`, `Specify`, or `Plan`.
- Missing requirements MUST be resolved explicitly or blocked with `BLOCKED_MISSING_INPUTS`.
- Specs can remain draft while open questions exist, but implementation MUST NOT start.
- Use `[NEEDS CLARIFICATION: ...]` markers for unresolved requirements and clear them before implementation.

## Control Catalog Mapping

- `.spec-kit/control-catalog.yaml` is the machine-readable source for `SDD-C-###` control statements.
- `.spec-kit/control-catalog.md` is generated from `.spec-kit/control-catalog.yaml` for human-readable review.
- Each work-item `spec.md` MUST include an `Applicable Guardrail Controls` section listing the exact control IDs that govern the work item.
- Each work-item `spec.md` MUST include an `Implementation Stack Profile` section with backend/frontend/test profiles, explicit agent execution model, managed-service decision fields, and local-first runtime baseline fields.
- Each work-item `plan.md` and `tasks.md` MUST include the app onboarding minimum make-target contract (including `infra-port-forward-start`, `infra-port-forward-stop`, and `infra-port-forward-cleanup`).
- Each work-item `spec.md` MUST include blueprint-defect escalation fields (`Upstream issue URL`, `Temporary workaround path`, `Replacement trigger`, `Workaround review date`) when consumer work includes blueprint-caused defects/workarounds.

## Managed-Service-First Mapping

- For runtime capabilities in `stackit-*` profiles, default posture is `Managed service preference: stackit-managed-first`.
- If using an alternative (`Managed service preference: explicit-consumer-exception`), the work item MUST include:
  - explicit `Managed service exception rationale` in `spec.md`
  - approved ADR reference
  - corresponding entry in `AGENTS.decisions.md`

## Local-First Runtime Baseline Mapping

- For local-first execution, `spec.md` MUST declare:
  - `Runtime profile: local-first-docker-desktop-kubernetes`
  - `Local Kubernetes context policy: docker-desktop-preferred`
  - `Local provisioning stack: crossplane-plus-helm`
  - `Runtime identity baseline: eso-plus-argocd-plus-keycloak`
  - `Local-first exception rationale: none`
- If `Runtime profile` is not local-first, the work item MUST include an explicit approved exception rationale in spec + ADR + decisions log.

## Normative Language Policy

Normative sections define implementation behavior and use only deterministic verbs:

- Allowed: `MUST`, `MUST NOT`, `SHALL`, `EXACTLY ONE OF`
- Forbidden ambiguity terms in normative sections:
  - `should`
  - `may`
  - `could`
  - `might`
  - `either`
  - `and/or`
  - `as needed`
  - `approximately`
  - `etc.`

Informative sections can explain context/tradeoffs, but they do not override normative requirements.

## Non-Functional Guardrail Mapping

| Guardrail | Capture In | Evidence |
|---|---|---|
| Security and privacy | `spec.md` NFR section | Authn/authz, secret handling, least-privilege controls |
| Observability | `spec.md`, `architecture.md` | Structured logs, metrics, traces, diagnostics fields |
| Monitoring and alerting | `spec.md`, `traceability.md` | Alert rules, thresholds, routing and ownership |
| Reliability and resilience | `architecture.md`, `plan.md` | Failure modes, rollback strategy, blast-radius controls |
| Operability and runbooks | `plan.md`, `traceability.md` | Deterministic runbook commands and diagnostics artifacts |

## Architecture and Code Policy Mapping

| Policy | Capture In | Evidence |
|---|---|---|
| SOLID + Clean Code | `architecture.md`, `plan.md` | Cohesive modules and explicit dependencies |
| Clean Architecture | `architecture.md` | Dependency direction and layer boundaries |
| DDD | `architecture.md`, `spec.md` | Ubiquitous language, bounded contexts, domain ownership |

## Test Automation Policy Mapping

| Policy | Capture In | Evidence |
|---|---|---|
| Shift-left strategy | `plan.md` | Lowest valid test layer first |
| Test pyramid | `plan.md`, `traceability.md` | Unit > 60%, Integration <= 30%, E2E <= 10% |
| Requirement-to-test mapping | `traceability.md` | Every requirement ID mapped to automated evidence |

## Graph and Evidence Mapping

- `graph.yaml` is the machine-readable requirement/acceptance dependency map for each work item.
- `traceability.md` MUST stay in sync with `graph.yaml` for all requirement and acceptance IDs.
- `evidence_manifest.json` stores deterministic file checksum evidence for work-item artifacts.
- `context_pack.md` captures normalized context handoff metadata for implementation/review/operations.

## Hardening and Publish Mapping

- `hardening_review.md` is mandatory before publish and must record repository-wide findings fixed, observability/diagnostics deltas, architecture/code-quality compliance, and non-implemented proposals.
- `pr_context.md` is mandatory before PR publication and must summarize requirement/contract coverage, key reviewer files, validation evidence, risk/rollback, and deferred proposals.
- PR templates (`.github/pull_request_template.md` and consumer init template) must include matching reviewer-context headings.

## Skill and Assistant Mapping

- Codex skills are optional accelerators that map lifecycle phases to deterministic runbooks.
- Multi-assistant execution remains contract-driven; all assistants must follow:
  - `AGENTS.md`
  - `blueprint/contract.yaml`
  - `.spec-kit/**`
  - canonical Make validation commands

## ADR Mapping

Finalized architecture decisions are recorded as ADRs:

- Blueprint track: `docs/blueprint/architecture/decisions/`
- Consumer track: `docs/platform/architecture/decisions/`

When `SPEC_READY=true`, `spec.md` must include:

- `ADR path` pointing to a valid ADR file
- `ADR status` in an accepted lifecycle state

## ADR Content Expectations

Each ADR should include:

- Business objective and requirement summary
- Options considered, selected option rationale, rejected-option rationale
- Affected capabilities and architecture components
- Mermaid architecture diagram
- Mermaid Gantt timeline for high-level work packages
- External dependencies
