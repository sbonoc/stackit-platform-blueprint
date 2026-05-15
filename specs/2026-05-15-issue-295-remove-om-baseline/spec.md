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
- Missing input blocker token: none
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: chore
- authorized-by: sbonoc

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: none
- Control exception rationale: chore — no code, no API, no runtime surface. Backlog and governance doc updates only.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: none
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: governance housekeeping only — no managed service involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: no runtime changes

## Objective
- Business outcome: Close issue #295 cleanly. Verification audit confirms the blueprint template paths cited in the issue contain no OpenMetadata-specific content — the cleanup was already completed prior to this issue being filed. `AGENTS.decisions.md` already records the architectural decision (OM is consumer/product-owned, out of blueprint scope). The only remaining work is updating the backlog and closing the issue so #248 is unblocked.
- Success metric: `AGENTS.backlog.md` no longer lists #295 as an open P1 gate and no longer blocks #248 on #295. GitHub issue #295 is closed with an explanation comment.

## Normative Requirements
- FR-001 `AGENTS.backlog.md` MUST be updated to mark issue #295 resolved and remove the gating of issue #248 on #295.
- FR-002 GitHub issue #295 MUST be closed with a comment explaining that the template cleanup was already in place and `AGENTS.decisions.md` captures the architectural decision.

## Normative Acceptance Criteria
- AC-001 `AGENTS.backlog.md` contains no open entry for issue #295 and no gating of #248 on #295.
- AC-002 GitHub issue #295 state is CLOSED.

## Informative Notes (Non-Normative)
- Audit finding: grep of all blueprint-managed template paths (`scripts/templates/blueprint/bootstrap/`) for `openmetadata`, `OpenMetadata`, `open_metadata` returns zero matches. The 4 files named in the issue (`platform.mk`, `north_star.md`, `tech_stack.md`, `endpoint_exposure_model.md`) contain no OM content.
- Decision already recorded: `AGENTS.decisions.md` line 81 states "OpenMetadata remains consumer/product-owned and is out of blueprint scope unless a future decision records otherwise" — this is exactly the decision #295 asked to document.
- No template changes needed. No consumer upgrade impact. No new OM opt-in module needed (YAGNI — one current consumer; module abstraction deferred until a second consumer adopts OM).
