# Architecture

## Context
- Work item: `2026-04-18-upgrade-convergence-postcheck-gate`
- Owner: `@sbonoc`
- Date: `2026-04-18`

## Stack and Execution Model
- Backend stack profile: `python_plus_fastapi_pydantic_v2` (upgrade orchestration + validation utilities)
- Frontend stack profile: `none (not in scope)`
- Test automation profile: `unittest + schema/contract assertions`
- Agent execution model: `single-agent deterministic execution`

## Problem Statement
- What needs to change and why:
  - upgrade preflight/apply currently expose `required_manual_actions`, but they do not provide a deterministic ownership-aware reconciliation artifact that summarizes safe-to-take vs manual vs unresolved conflicts.
  - operators need one explicit post-upgrade convergence gate that checks both validation and reconcile state.
  - bundled upgrade skill UX needs an explicit safe-to-continue vs blocked contract tied to machine-readable artifacts.
- Scope boundaries:
  - `scripts/lib/blueprint/upgrade_consumer.py`
  - `scripts/lib/blueprint/upgrade_preflight.py`
  - `scripts/lib/blueprint/upgrade_report_metrics.py`
  - new postcheck wrapper/library and reconcile-report helper under `scripts/bin/blueprint/` + `scripts/lib/blueprint/`
  - `make/blueprint.generated.mk` and template counterpart
  - `blueprint/contract.yaml` and template counterpart
  - docs + bundled skill docs (source + template fallback)
  - tests under `tests/blueprint/`
- Out of scope:
  - auto-resolving consumer-owned merge conflicts
  - changing ownership boundaries in `blueprint/contract.yaml`
  - changing upgrade dirty/delete safety behavior

## Bounded Contexts and Responsibilities
- Upgrade planning/apply context:
  - classify upgrade entries and manual actions
  - emit plan/apply reports + ownership-aware reconcile report
- Upgrade preflight context:
  - aggregate plan/apply + reconcile reports into merge-risk classifications
  - provide deterministic remediation hints before apply
- Upgrade postcheck context:
  - compose validate + merge-marker + reconcile assertions
  - enforce deterministic merge-gate pass/fail contract

## High-Level Component Design
- Domain layer:
  - reconcile buckets (`blueprint_managed_safe_to_take`, `consumer_owned_manual_review`, `generated_references_regenerate`, `conflicts_unresolved`)
  - deterministic blocked/safe decision model
- Application layer:
  - upgrade execution writes reconcile report in same run as plan/apply
  - preflight derives merge-risk classification with bucket hints
  - postcheck enforces convergence gate and emits machine-readable postcheck report
- Infrastructure adapters:
  - contract loader (`load_blueprint_contract`)
  - merge-marker scanner (`find_merge_markers`)
  - make-target execution wrappers for validate/docs hooks
  - JSON artifact writers under `artifacts/blueprint/**`
- Presentation/API/workflow boundaries:
  - new artifact: `artifacts/blueprint/upgrade/upgrade_reconcile_report.json`
  - enriched preflight: `artifacts/blueprint/upgrade_preflight.json`
  - new postcheck artifact: `artifacts/blueprint/upgrade_postcheck.json`
  - new make target: `blueprint-upgrade-consumer-postcheck`

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml` repo-mode and ownership rules
  - existing upgrade plan/apply/validate artifact formats
- Downstream dependencies:
  - Codex/Claude consumer upgrade skill runbooks
  - consumer operator workflows and CI merge gates
- Data/API/event contracts touched:
  - `upgrade_plan.json`
  - `upgrade_apply.json`
  - `upgrade_reconcile_report.json` (new)
  - `upgrade_preflight.json` (enriched)
  - `upgrade_postcheck.json` (new)

## Non-Functional Architecture Notes
- Security:
  - all new path arguments remain repository-scoped and traversal-safe
  - no secret-bearing payload fields added
- Observability:
  - emit per-bucket reconcile counts and postcheck status metrics
  - include deterministic blocked reasons in postcheck payload
- Reliability and rollback:
  - deterministic sorted bucket outputs for stable CI diffs
  - rollback is revert of affected scripts/make/contracts/docs/tests only
- Monitoring/alerting:
  - CI can consume postcheck status metrics and non-zero exit contract

## Risks and Tradeoffs
- Risk 1: reconcile classification drift between preflight and upgrade artifacts.
  - Mitigation: centralize classification helper and test both producers.
- Risk 2: postcheck could duplicate validate behavior and add noisy failures.
  - Mitigation: postcheck composes validate once, then checks only convergence-specific conditions.
- Tradeoff 1: adding a new postcheck target increases command surface.
  - Mitigation: keep wrapper minimal and reference existing validate bundle.
