# Architecture

## Context
- Work item: `2026-04-18-upgrade-validation-required-file-reconciliation`
- Owner: `@sbonoc`
- Date: `2026-04-18`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2` (Python CLI tooling in `scripts/lib/blueprint/**`)
- Frontend stack profile: `none (not in scope)`
- Test automation profile: `unittest + json-schema checks`
- Agent execution model: `single-agent deterministic execution`

## Problem Statement
- Generated-consumer upgrade validation previously trusted implicit required-file assumptions.
- Missing required files or partial generated-reference drift could pass preflight/validate and fail later in CI or manual review.
- Scope boundaries:
  - `scripts/lib/blueprint/upgrade_consumer_validate.py`
  - `scripts/lib/blueprint/upgrade_preflight.py`
  - `scripts/lib/blueprint/upgrade_report_metrics.py`
  - `scripts/bin/blueprint/upgrade_consumer_validate.sh`
  - `scripts/lib/blueprint/schemas/upgrade_validate.schema.json`
  - tests under `tests/blueprint/`
- Out of scope:
  - auto-committing regenerated files
  - changing ownership boundaries in `blueprint/contract.yaml`
  - introducing new Make targets

## Bounded Contexts and Responsibilities
- Upgrade Validate Context:
  - execute required validation targets
  - enforce repo-mode-aware required-file reconciliation
  - enforce coupled generated-reference contract checks
  - emit machine-readable status artifacts and summary counts
- Upgrade Preflight Context:
  - classify plan/apply/manual actions
  - surface `required_surface_reconciliation` and `required_surfaces_at_risk`
  - keep output deterministic for generated-consumer and template-source repo modes

## High-Level Component Design
- Domain layer:
  - required-file gating policy derived from active `repo_mode` and `source_only_paths`
  - remediation action taxonomy (`render`, `sync`, `restore`, `manual-review`)
- Application layer:
  - validate flow orchestration with `status=failure` on missing required files and coupled-doc drift
  - preflight aggregation enriched with required-surface risk detection
- Infrastructure adapters:
  - blueprint contract loader (`load_blueprint_contract`)
  - JSON artifact writers under `artifacts/blueprint/**`
  - Make target command execution in validate bundle
- Presentation/API/workflow boundaries:
  - `upgrade_validate.json` schema-expanded payload
  - new `artifacts/blueprint/upgrade/required_files_status.json`
  - preflight `required_surface_reconciliation` section
  - wrapper-emitted metrics sourced from report summaries

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml`
  - runtime edge catalog (`runtime_dependency_edges.py`)
- Downstream dependencies:
  - upgrade wrappers (`upgrade_consumer_validate.sh`)
  - CI/quality lanes consuming validate/preflight artifacts
- Data/API/event contracts touched:
  - `scripts/lib/blueprint/schemas/upgrade_validate.schema.json`
  - `artifacts/blueprint/upgrade_validate.json`
  - `artifacts/blueprint/upgrade/required_files_status.json`
  - `artifacts/blueprint/upgrade_preflight.json`

## Non-Functional Architecture Notes
- Security:
  - all report paths remain repo-scoped with strict path resolution
  - no new network operations or secret surfaces
- Observability:
  - summary counts and wrapper metrics now include required-file and coupled-doc signals
- Reliability and rollback:
  - deterministic sorted reports for reproducible CI diffs
  - rollback is revert of modified scripts/schemas/tests only
- Monitoring/alerting:
  - wrapper metrics expose new counters for missing required files and generated-reference failures

## Risks and Tradeoffs
- Risk: contract-driven required-file checks could cause false positives in minimal fixtures.
  - Mitigation: fixture-aware contract minimization and explicit repo-mode gating tests.
- Tradeoff: helper logic is duplicated in validate and preflight to keep dependencies local and avoid new shared module churn in this slice.
