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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260418-generated-consumer-platform-docs-ownership-boundary.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
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
- Business outcome: generated-consumer repositories MUST keep `docs/platform/**` consumer-owned after seeding and MUST NOT reintroduce reverse mirroring into template docs.
- Success metric: generated-consumer docs checks pass after consumer doc edits without requiring template mirror updates, and upgrade/bootstrap cleanup removes template-orphan consumer docs deterministically.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST enforce repo-mode-aware platform docs sync behavior: `template-source` mode MUST keep strict synchronization from `docs/platform/**` to template seed docs only for contract-declared required seed files.
- FR-002 MUST enforce one-way ownership in `generated-consumer` mode: platform docs sync/check MUST NOT require template mirror equality for consumer-edited `docs/platform/**`.
- FR-003 MUST clean generated-consumer template orphans under `scripts/templates/blueprint/bootstrap/docs/platform/**` that are outside `required_seed_files`, with non-destructive handling (`move to docs/platform when missing`, otherwise remove template copy).
- FR-004 MUST apply the same repo-mode ownership policy to generated summary scripts (`sync_runtime_identity_contract_summary.py`, `sync_module_contract_summaries.py`) so consumer-mode checks do not fail on template drift.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST keep all docs cleanup/sync operations repository-root scoped and contract-derived.
- NFR-OBS-001 MUST emit deterministic script diagnostics that identify orphan template paths and the applied cleanup action.
- NFR-REL-001 MUST keep generated-consumer cleanup idempotent so repeated runs converge without destructive data loss.
- NFR-OPS-001 MUST provide deterministic remediation guidance in `--check` mode with a single canonical sync command.

## Normative Option Decision
- Option A: keep bidirectional docs/platform-template synchronization in both repo modes.
- Option B: enforce repo-mode-aware one-way ownership with generated-consumer template-orphan cleanup.
- Selected option: OPTION_B
- Rationale: Option B preserves bootstrap seeding behavior while eliminating consumer-doc duplication and noisy template drift failures.

## Contract Changes (Normative)
- Config/Env contract: no new environment variables are introduced.
- API contract: no API/event surface changes.
- Event contract: no event surface changes.
- Make/CLI contract: existing docs sync CLI flags (`--repo-root`, `--check`) remain stable.
- Docs contract: `docs_contract.platform_docs.required_seed_files` becomes the deterministic allowlist for template-source sync and generated-consumer template-orphan cleanup.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST be objectively testable: in generated-consumer mode, editing `docs/platform/**` no longer requires template mirror updates for docs checks to pass.
- AC-002 MUST be objectively testable: in generated-consumer mode, template-orphan docs files outside `required_seed_files` are detected in `--check` and cleaned in sync mode.
- AC-003 MUST be objectively testable: runtime-identity and module-summary generators skip template synchronization/checks in generated-consumer mode while keeping source-doc validation.
- AC-004 MUST be objectively testable: template-source mode continues strict platform seed synchronization and existing checks remain green.

## Informative Notes (Non-Normative)
- Context: this work item implements the next P0 backlog item and includes upgrade-time cleanup behavior explicitly requested by the user.
- Tradeoffs: template-source strict sync remains for blueprint maintenance while generated-consumer mode intentionally relaxes template equality checks for consumer-owned docs.
- Clarifications: none.

## Explicit Exclusions
- No change to `docs/blueprint/**` strict template synchronization policy.
- No change to module runtime behavior outside docs generation/sync surfaces.
