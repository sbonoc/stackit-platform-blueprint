# Architecture

## Context
- Work item: 2026-04-26-issue-198-199-upgrade-coverage-gaps
- Owner: Platform Engineering
- Date: 2026-04-26

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: Three independent gaps in the blueprint upgrade pipeline cause consumer-repo regressions to go undetected. (1) `VALIDATION_TARGETS` in `upgrade_consumer_validate.py` omits `blueprint-template-smoke`, so init-path regressions are never caught locally. (2) `VALIDATION_TARGETS` also omits `infra-argocd-topology-validate`, so broken kustomize manifests (e.g. from Stage 2 prune deleting consumer-renamed files, as observed in #203) only surface at the CI `blueprint-quality` job. (3) `ownership_path_classes` in `contract.yaml` has no declaration for `apps/catalog*` paths, so every source-tree coverage audit emits false-positive "uncovered file" warnings — or if the strict gate is enabled, blocks plan generation entirely.
- Scope boundaries: Python schema/validation logic (`contract_schema.py`, `upgrade_consumer.py`, `upgrade_consumer_validate.py`, `validate_contract.py`) and two YAML contract files (`blueprint/contract.yaml`, bootstrap template counterpart). No runtime, API, or infra changes.
- Out of scope: Option A schema loosening, disk-presence checks for feature-gated paths, consumer-repo migration docs.

## Bounded Contexts and Responsibilities
- Context A — Contract schema (`contract_schema.py`): owns the Python dataclasses that represent `blueprint/contract.yaml`. Adds `feature_gated: list[str]` to `RepositoryOwnershipPathClasses` and a `feature_gated_paths` property on `RepositoryContract`.
- Context B — Source-tree coverage audit (`upgrade_consumer.py`): owns the `audit_source_tree_coverage` function that determines which blueprint source files are accounted for by the contract. Adds `feature_gated` as an additional coverage set parameter.
- Context C — Upgrade validation (`upgrade_consumer_validate.py`): owns `VALIDATION_TARGETS`, the tuple of Make targets run in the consumer repo after upgrade. Adds `"blueprint-template-smoke"` and `"infra-argocd-topology-validate"`.
- Context D — Contract validation (`validate_contract.py`): owns the static checks run against `blueprint/contract.yaml`. Reads and validates `feature_gated`; no disk-presence check, no equality constraint vs `optional_modules`.
- Context E — Contract data (`blueprint/contract.yaml` + bootstrap template): declares `feature_gated: [apps/catalog, apps/catalog/manifest.yaml, apps/catalog/versions.lock]` under `ownership_path_classes`.

## High-Level Component Design
- Domain layer: `RepositoryOwnershipPathClasses` dataclass — pure data, no side effects. Adding a field is a non-breaking schema extension.
- Application layer: `audit_source_tree_coverage` — adds `feature_gated` to the union of coverage roots; defaults to `set()` for backward compatibility. `validate_plan_uncovered_source_files` error message updated to reference `feature_gated`.
- Infrastructure adapters: none — no new I/O, no new subprocesses.
- Presentation/API/workflow boundaries: `validate_contract.py` reads the new YAML field via the existing loader; no CLI signature changes.

## Integration and Dependency Edges
- Upstream dependencies: `contract.yaml` schema loader in `contract_schema.py` — must parse the new `feature_gated` list.
- Downstream dependencies: `upgrade_consumer.py` call to `audit_source_tree_coverage` — must pass `feature_gated` paths extracted from the loaded contract.
- Data/API/event contracts touched: none — internal Python function signatures only.

## Non-Functional Architecture Notes
- Security: No authn/authz, no secret handling, no privilege changes. Pure data-validation logic.
- Observability: `validate_plan_uncovered_source_files` error message updated to list `feature_gated` alongside existing categories. No new metrics or log lines required — the existing uncovered-file warning path already emits to stderr.
- Reliability and rollback: All changes are in Python source files and YAML. Rollback = `git revert` of the PR. No migrations, no state changes.
- Monitoring/alerting: none — this is offline validation tooling, not a runtime service.

## Risks and Tradeoffs
- Risk 1: `feature_gated` parameter default (`set()`) means existing call sites silently continue to exclude those paths from coverage. Mitigation: the blueprint-repo call site in `upgrade_consumer.py` is updated in the same PR to pass the contract-declared `feature_gated_paths`.
- Risk 2: `infra-argocd-topology-validate` requires kustomize; if not installed in a consumer environment the target falls back to kustomization-file-only validation. Mitigation: the script handles this gracefully with a logged warning — no hard failure if kustomize is absent.
- Tradeoff 1: Adding a new ownership class name requires developers to learn one more concept. Accepted because `feature_gated` is semantically distinct from `conditional_scaffold` (flag-gated with no seed template vs optional-module scaffolding with a disk-presence check) and maps cleanly to the existing `app_catalog_scaffold_contract` concept.
- Tradeoff 2: Adding `infra-argocd-topology-validate` to VALIDATION_TARGETS increases validate runtime by ~5–15 seconds (kustomize build). Accepted — this is a post-upgrade gate, not an inner-loop step, and the cost is far lower than a failed CI job.
- Out-of-scope exclusion: The root cause of #203 (Stage 2 prune deleting consumer-renamed seeded files) and #204 (3-way merge duplicate Terraform blocks) are explicitly excluded; early detection via FR-005 is the mitigating measure for #203's symptoms.
