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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-issue-152-sdd-placeholder-guard.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-005, SDD-C-012
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
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
- Business outcome: `make quality-hardening-review` reliably catches unfilled scaffold placeholder fields in SDD work-item documents before they ship in a PR.
- Success metric: a work-item directory with untouched scaffold values in `context_pack.md` or `architecture.md` MUST cause `make quality-hardening-review` to exit non-zero with a message naming the file and the empty field.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `check_sdd_assets.py` MUST detect when any required field in `context_pack.md` has an empty value and emit a Violation naming the file and the field.
- FR-002 `check_sdd_assets.py` MUST detect when any required field in `architecture.md` has an empty value and emit a Violation naming the file and the field.
- FR-003 The required fields MUST be declared in `blueprint/contract.yaml` under the SDD contract so they can be extended without modifying the validator.

### Non-Functional Requirements (Normative)
- NFR-OPS-001 Violation messages MUST name the document path and the specific empty field so operators know exactly what to fill in.
- NFR-REL-001 The check MUST NOT fire on documents that are intentionally sparse (e.g. "none" is a valid value; only a blank or absent value after the colon is a violation).

## Normative Option Decision
- Option A: required-field allowlist declared in `blueprint/contract.yaml`; validator reads the list and asserts each field has a non-empty value.
- Option B: heuristic line-scan for scaffold placeholder patterns (e.g. lines ending with bare `:`).
- Selected option: OPTION_A
- Rationale: Option A is precise, extensible, and does not produce false positives on intentionally sparse documents. The contract is already the canonical source of SDD governance configuration.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- Event contract: none
- Make/CLI contract: `make quality-hardening-review` now fails when required fields are empty in `context_pack.md` or `architecture.md`
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `make quality-hardening-review` MUST exit non-zero when `context_pack.md` has any required field with an empty value.
- AC-002 `make quality-hardening-review` MUST exit non-zero when `architecture.md` has any required field with an empty value.
- AC-003 `make quality-hardening-review` MUST pass when all required fields are populated with non-empty values (including "none").
- AC-004 The violation message MUST include the document path and the name of the empty field.
- AC-005 `make infra-contract-test-fast` MUST remain green after the change.

## Informative Notes (Non-Normative)
- Context: Discovered in PR #151 where `architecture.md` and `context_pack.md` shipped as pure scaffold output. `check_sdd_assets.py` checked `context_pack.md` only for non-emptiness and "Context Snapshot" section presence — the scaffold template satisfies both. `architecture.md` was not checked at all.
- Tradeoffs: Option A (contract-declared field list) is slightly more ceremony than a heuristic scan, but the heuristic approach risks false positives on documents that legitimately have short values or "none" entries.
- Clarifications: "none" is an acceptable field value and MUST NOT trigger a violation.

## Explicit Exclusions
- No changes to how `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, or `hardening_review.md` are validated.
- No changes to the scaffold templates themselves.
