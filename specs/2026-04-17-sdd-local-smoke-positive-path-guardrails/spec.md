# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260417-sdd-local-smoke-positive-path-guardrails.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-022, SDD-C-023, SDD-C-024
- Control exception rationale: none

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
- Business outcome: enforce SDD guardrails that block weak filter/transform test evidence and require local positive-path smoke evidence for HTTP/filter scope.
- Success metric: future work-item plans/tasks and governance docs consistently include positive-path and local-smoke gates, validated by repository quality checks.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001: Blueprint and consumer `plan.md` templates MUST define a positive-path filter/payload-transform test gate that requires matching fixture/request assertions and preserved output fields.
- FR-002: Blueprint and consumer `plan.md` templates MUST define a local smoke publish gate for HTTP route/filter/new-endpoint scope, including positive-path `curl` evidence capture in `pr_context.md` as `Endpoint | Method | Auth | Result`.
- FR-003: Blueprint and consumer `tasks.md` templates MUST include an explicit test task that verifies positive-path filter/payload-transform coverage and evidence capture in `pr_context.md`.
- FR-004: Governance and interoperability surfaces (`AGENTS.md`, consumer-init `AGENTS.md.tmpl`, `docs/blueprint/governance/spec_driven_development.md`, `docs/blueprint/governance/assistant_compatibility.md`, `CLAUDE.md`) MUST state these guardrails as assistant-agnostic policy.
- FR-005: The SDD control catalog MUST include stable control IDs for local smoke and positive-path gates and keep rendered markdown synchronized with the source catalog.
- FR-006: SDD templates and governance policy MUST require translation of any reproducible pre-PR smoke/`curl`/deterministic-check finding into a failing automated test first and a green result after the fix, or documented deterministic exception rationale in publish artifacts.

### Non-Functional Requirements (Normative)
- NFR-SEC-001: Guardrail wording MUST block empty-result-only assertions as sufficient evidence for filter/payload-transform behavior.
- NFR-OBS-001: Publish evidence expectations MUST be explicit and deterministic (`Endpoint | Method | Auth | Result`) for local smoke assertions.
- NFR-REL-001: Canonical templates and mirrors MUST remain synchronized via repository sync tooling in the same change.
- NFR-OPS-001: Validation guidance MUST remain executable through canonical repository commands without adding new manual-only runbooks.

## Normative Option Decision
- Option A: enforce guardrails in templates, governance docs, and control catalog with regression coverage.
- Option B: keep guidance in issue text and rely on reviewer memory.
- Selected option: OPTION_A
- Rationale: Option A provides deterministic, reusable enforcement for all assistants and reduces regression risk.

## Contract Changes (Normative)
- Config/Env contract: no change.
- API contract: no change.
- Event contract: no change.
- Make/CLI contract: no new targets; existing `quality-sdd-*`, docs sync, and validation targets enforce updated artifacts.
- Docs contract: governance docs and template mirrors include local-smoke and positive-path guardrails.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001: `.spec-kit/templates/{blueprint,consumer}/plan.md` include the positive-path gate and local smoke gate markers.
- AC-002: `.spec-kit/templates/{blueprint,consumer}/tasks.md` include explicit positive-path verification task wording with `pr_context.md` evidence capture.
- AC-003: `.spec-kit/control-catalog.yaml` defines `SDD-C-022` and `SDD-C-023`, and `.spec-kit/control-catalog.md` renders both controls.
- AC-004: Governance/interoperability docs and consumer-init governance template include normative statements for the new gates.
- AC-005: Sync and validation commands pass after changes (`quality-sdd-check`, docs template sync check, infra-validate, targeted unit tests).
- AC-006: Plan/tasks templates and control catalog include explicit finding-to-test translation requirements (`failing test first`, `green after fix`, deterministic exception documentation path).

## Informative Notes (Non-Normative)
- Context: issue #138 reported a real defect pattern where empty-result-only tests hid a filter regression until local smoke execution.
- Tradeoffs: additional checklist and evidence steps increase authoring time but provide earlier defect detection.
- Clarifications:
  - user requested implementation by following the full SDD lifecycle in this work item.

## Explicit Exclusions
- Excluded item 1: no runtime application logic changes.
- Excluded item 2: no CI lane restructuring in this work item.
