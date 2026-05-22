# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: BLOCKED_MISSING_INPUTS
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001
- Control exception rationale: documentation and tooling fix only — no runtime, infra, or application code changed.

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
- Business outcome: Reduce recurring `quality-sdd-check` failures caused by agents following skill runbooks and templates that disagreed with what the check scripts actually enforced.
- Success metric: Agents can complete SDD intake through PR-ready without hitting check-gate violations that were not signalled by the skill or template they followed.

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 Clarification marker format MUST be `[NEEDS CLARIFICATION: ...]` (colon + descriptive text) in all skill runbooks and templates that reference the canonical form.
- REQ-002 Artifact templates MUST NOT scaffold placeholder lines that immediately trigger `check_spec_pr_ready.py` rejection patterns (`Slice N:` empty, `Risk N -> mitigation:` empty, `Proposal N (not implemented):` empty, `no-impact | impacted (select one)`).
- REQ-003 The bypass track (`SPEC_READY_EXCEPTION`) MUST be documented in the step01 intake skill and the consumer-init seed template so agents see it at the moment they start a work item.
- REQ-004 The bypass track MUST be referenced in the step03 spec-complete skill so agents know sign-offs still apply when the bypass is active.

### Acceptance Criteria
- AC-001 `[NEEDS CLARIFICATION]` (without colon) MUST NOT appear in any skill runbook or consumer-init seed template.
- AC-002 A freshly scaffolded `plan.md` from either template MUST pass `check_spec_pr_ready.py` without any edits to the delivery slice, app-onboarding impact, or risk lines.
- AC-003 A freshly scaffolded `pr_context.md` from either template MUST pass `check_spec_pr_ready.py` on the Deferred Proposals section without any edits.
- AC-004 `blueprint-sdd-step01-intake/SKILL.md` MUST contain a `## Bypass Track` section describing `SPEC_READY_EXCEPTION` values, activation steps, and reduced artifact set.
