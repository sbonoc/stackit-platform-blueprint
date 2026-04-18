# Architecture

## Context
- Work item: `2026-04-18-docs-ownership-boundary-generated-consumer`
- Owner: `@sbonoc`
- Date: `2026-04-18`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2` (Python docs/quality tooling)
- Frontend stack profile: `none (not in scope)`
- Test automation profile: `unittest + repo-mode fixture tests`
- Agent execution model: `single-agent deterministic execution`

## Problem Statement
- Generated-consumer repositories currently inherit docs sync behavior that mirrors `docs/platform/**` back into `scripts/templates/blueprint/bootstrap/docs/platform/**`.
- This reverse mirroring duplicates consumer-owned docs into template paths and creates avoidable drift/failures in docs quality gates.
- Scope boundaries:
  - `scripts/lib/docs/sync_platform_seed_docs.py`
  - `scripts/lib/docs/sync_runtime_identity_contract_summary.py`
  - `scripts/lib/docs/sync_module_contract_summaries.py`
  - docs sync tests under `tests/blueprint/` and `tests/docs/`
  - SDD/ADR/governance artifacts for this work item
- Out of scope:
  - redefining `docs/blueprint/**` strict template sync behavior
  - changing consumer-facing doc content beyond ownership mechanics
  - introducing new make targets or new runtime services

## Bounded Contexts and Responsibilities
- Platform Docs Seed Sync Context:
  - in `template-source`, keep strict source-to-template synchronization for contract-declared seed files
  - in `generated-consumer`, enforce one-way ownership and clean template orphans
- Generated Summary Sync Context:
  - runtime identity and module summary generators update/check template mirrors only in `template-source`
  - generated-consumer checks remain source-doc focused and must not block on template drift

## High-Level Component Design
- Domain layer:
  - ownership policy keyed by `repo_mode` and `docs_contract.platform_docs.required_seed_files`
  - deterministic orphan classification for template files outside required seed set
- Application layer:
  - repo-mode-aware docs sync/check orchestration inside each docs generator
  - non-destructive orphan handling (`move-to-source-when-missing`, otherwise remove template copy)
- Infrastructure adapters:
  - contract loader (`load_blueprint_contract`)
  - filesystem adapter for docs/template file reconciliation
- Presentation/API/workflow boundaries:
  - existing CLI contracts (`--check`, `--repo-root`) remain stable
  - stderr diagnostics and change summaries communicate cleanup/remediation paths

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml` (`repo_mode`, `docs_contract.platform_docs`)
  - module contracts in `blueprint/modules/*/module.contract.yaml`
  - runtime identity contract in `blueprint/runtime_identity_contract.yaml`
- Downstream dependencies:
  - `make quality-docs-check-changed`
  - `make quality-docs-sync-all`
  - `make blueprint-bootstrap` during upgrade flows
- Data/API/event contracts touched:
  - docs sync/check behavior contract for generated-consumer mode
  - template-folder cleanup behavior during bootstrap/upgrade

## Non-Functional Architecture Notes
- Security:
  - all file operations remain repository-root scoped and contract-derived
- Observability:
  - cleanup/remediation actions are emitted through deterministic script output and change summaries
- Reliability and rollback:
  - cleanup is idempotent; repeated runs converge to the same template/source state
  - rollback is revert of docs sync scripts + tests + SDD artifacts
- Monitoring/alerting:
  - existing quality gates (`quality-docs-check-changed`, `quality-hooks-fast`) remain the detection boundary

## Risks and Tradeoffs
- Risk 1: changing sync semantics can miss a hidden reverse-mirroring path and keep duplication active.
  - Mitigation: implement and test all three docs sync generators that touch template platform docs.
- Tradeoff 1: generated-consumer mode intentionally stops strict source-template equality checks for `docs/platform/**`.
  - Rationale: ownership correctness and non-duplication take precedence over mirror symmetry in consumer repos.
