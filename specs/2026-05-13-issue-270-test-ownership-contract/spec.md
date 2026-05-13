# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 1
- Unresolved alternatives count: 1
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 1
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-270-test-ownership-contract.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-024
- Control exception rationale:
  - SDD-C-009 (secrets/credentials in hooks): N/A — no secret or credential surface; test file relocation only
  - SDD-C-010 (observability): N/A — no runtime observability surface; blueprint tooling changes only
  - SDD-C-013 (STACKIT managed services): N/A — no runtime capability changes
  - SDD-C-014 (local-first runtime baseline): N/A — no local Kubernetes provisioning scope
  - SDD-C-015 (app onboarding make targets): N/A — no app delivery workflow scope
  - SDD-C-018 (blueprint upstream defect escalation): N/A — this work item IS the upstream blueprint fix
  - SDD-C-022 (HTTP route/filter smoke): N/A — no HTTP route or filter logic
  - SDD-C-023 (positive-path filter/transform test): N/A — no filter or payload-transform logic

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none — no frontend components; test file relocation and contract change only
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — no runtime provisioning scope
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: N/A — no local runtime provisioning; blueprint tooling and test taxonomy changes only

## Objective
- Business outcome: Eliminate the class of false-positive test failures caused by the upgrade resolver overwriting consumer `tests/infra/` files that contain blueprint-internal assertions. Blueprint-author tests that assert against blueprint-managed artefacts (`blueprint/modules/`, `scripts/lib/blueprint/`, etc.) are relocated to `tests/blueprint/` (already classified `source_only`), so the upgrade engine never writes them to consumer repos.
- Success metric: (1) All blueprint-author test classes identified by the audit live under `tests/blueprint/` after this change. (2) No file remaining in `required_seed_files` contains test classes that import or assert against `blueprint/modules/` content. (3) Full test suites pass in both template-source and generated-consumer modes. (4) A synthetic consumer with a stale copy of a relocated file receives a clean file deletion (not an overwrite) on upgrade.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001: An audit MUST be conducted of all `tests/infra/test_*.py` files currently listed in `spec.repository.required_seed_files` in `blueprint/contract.yaml`. Each file MUST be classified as: (a) entirely blueprint-author, (b) entirely consumer-runtime, or (c) mixed. The classification MUST be recorded in `architecture.md`.

- FR-002: Each file classified as "entirely blueprint-author" MUST be moved to `tests/blueprint/test_<name>.py` and removed from `required_seed_files`. `tests/blueprint/` is already declared `source_only` in `ownership_path_classes`, so no additional contract change is needed for these files.

- FR-003: Each file classified as "mixed" MUST be split: blueprint-author test classes MUST be extracted to a new or existing file under `tests/blueprint/`, and the remaining consumer-runtime test classes MUST stay in `tests/infra/`. The original `tests/infra/` file MUST be updated in `required_seed_files` to reflect only its consumer-runtime content.

- FR-004: `blueprint/contract.yaml` `spec.repository.required_seed_files` MUST be updated to remove any `tests/infra/` path that is fully relocated, and retain only paths with consumer-runtime content.

- FR-005: A contract assertion MUST be added to `tests/blueprint/test_quality_contracts.py` (or equivalent) verifying that no file listed in `required_seed_files` contains test classes that directly import from or assert against paths beginning with `blueprint/modules/` or `blueprint/modules/`.

- FR-006: All relocated test classes MUST pass in the template-source pytest run after relocation. Any import paths that relied on `tests/infra/`-specific fixtures or conftest MUST be updated to resolve correctly from `tests/blueprint/`.

### Non-Functional Requirements (Normative)

- NFR-REL-001: The relocation MUST be additive from the consumer perspective — no consumer test that currently runs in consumer CI (i.e. test classes remaining in `tests/infra/`) MUST be removed or broken by this change. Consumer repos with stale copies of relocated files will retain those copies until re-init or manual cleanup; they will not receive overwrites on upgrade (the upgrade engine stops writing them).

- NFR-REL-002: The `required_seed_files` list MUST NOT grow as a result of this change. It MUST shrink by the count of fully-relocated files.

- NFR-OPS-001: The change MUST be documented in `docs/blueprint/governance/` so blueprint maintainers understand the `tests/blueprint/` vs `tests/infra/` taxonomy going forward.

- NFR-A11Y-001: N/A — no UI components.

## Acceptance Criteria (Normative)

- AC-001: All test classes that assert against `blueprint/modules/<module>/module.contract.yaml` live under `tests/blueprint/` after this change.

- AC-002: `python3 -m pytest tests/blueprint/ -v` passes with all relocated test classes included and green.

- AC-003: `python3 -m pytest tests/infra/ -v` passes; no test classes that were present in `tests/infra/` before this change and that were consumer-runtime-facing are missing.

- AC-004: The contract assertion from FR-005 is green: no file in `required_seed_files` contains a reference to `blueprint/modules/`.

- AC-005: `make infra-validate` passes; `blueprint/contract.yaml` is valid after `required_seed_files` updates.

- AC-006: `make quality-hooks-fast` passes with zero violations.

## Open Questions

> **[NEEDS CLARIFICATION]** Q-1: Should mixed files be split (Option 1 extended) or should a new `source_only` override per-file be introduced in `contract.yaml` to avoid splitting (Option 2)?
>
> **Options:**
> - **A) Split mixed files** — Extract blueprint-author classes to `tests/blueprint/`, leave consumer-runtime classes in `tests/infra/`. No new contract field. Taxonomy is immediately clear. Requires auditing and splitting each mixed file. (agent recommendation)
> - **B) Per-file source_only override** — Add a list under `ownership_path_classes.source_only` for the specific mixed-file paths, and remove them from `required_seed_files`. Avoids file splitting but leaves blueprint-author classes in `tests/infra/` — taxonomy remains ambiguous for maintainers.
>
> **Agent recommendation:** Option A (split). The split is a one-time cost and produces a permanently clean taxonomy. Option B postpones the problem and leaves blueprint-author test classes in a directory whose name implies consumer-runtime scope. The issue author also marks Option 1 (full relocation) as preferred.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none — this work item IS the upstream blueprint fix for issue #270
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Informative Notes (Non-Normative)
- Context: Issue #270 documents false-positive failures in consumer CI caused by the upgrade resolver 3-way-merging `tests/infra/` blueprint-author test files into consumer repos. Evidence from sbonoc/dhe-marketplace v1.7.0 → v1.10.0 upgrade (PR #62): 19 false-positive test failures. `tests/blueprint/` is already classified `source_only` in `ownership_path_classes` — files there are never written to consumer repos.
- Tradeoffs: Splitting mixed files is a one-time authoring cost; benefit is a permanently unambiguous taxonomy enforced by the FR-005 contract assertion.
- Clarifications: Q-1 (split vs per-file source_only override) is the only open question; all other scope is settled.
