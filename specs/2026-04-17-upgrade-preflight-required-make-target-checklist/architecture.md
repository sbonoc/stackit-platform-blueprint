# Architecture

## Context
- Work item: 2026-04-17-upgrade-preflight-required-make-target-checklist
- Owner: sbonoc
- Date: 2026-04-17

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: preflight diagnostics currently miss some contract-required consumer-owned Make target gaps when targets are not yet referenced by known invoker paths, which causes late validation failures.
- Scope boundaries: upgrade planning manual-action detection, targeted tests, and consumer upgrade documentation.
- Out of scope: upgrade apply conflict engine, template ownership boundaries, and Make contract schema redesign.

## Bounded Contexts and Responsibilities
- Upgrade planning context (`scripts/lib/blueprint/upgrade_consumer.py`): detect missing required consumer-owned Make targets and generate deterministic manual-action records.
- Contract context (`blueprint/contract.yaml`): canonical source for required Make targets and platform make ownership paths.
- Validation context (`tests/blueprint/test_upgrade_consumer.py`): enforce red->green regression coverage for missing required-target detection and existing placeholder safeguards.
- Consumer documentation context (`docs/platform/consumer/**`): explain preflight checklist expectations and remediation location.

## High-Level Component Design
- Domain layer: required target coverage rules for consumer-owned Make surfaces.
- Application layer: `upgrade_consumer` planning composes manual actions with dependency source, reason, and follow-up commands.
- Infrastructure adapters: parser over `make/platform.mk` and `make/platform/*.mk`; source invoker-path scanning for dependency context.
- Presentation/API/workflow boundaries: `upgrade_plan.json`, `upgrade_apply.json`, `upgrade_preflight.json`, and `upgrade_summary.md` surface actionable findings.

## Integration and Dependency Edges
- Upstream dependencies:
  - `blueprint/contract.yaml` (`spec.make_contract.required_targets`, ownership paths)
  - source blueprint repository checkout used by upgrade planner
- Downstream dependencies:
  - `make blueprint-upgrade-consumer-preflight`
  - `make blueprint-upgrade-consumer-validate`
  - `make blueprint-upgrade-readiness-doctor`
- Data/API/event contracts touched:
  - `required_manual_actions[*].dependency_of`
  - `required_manual_actions[*].reason`
  - `required_manual_actions[*].required_follow_up_commands`

## Non-Functional Architecture Notes
- Security: no new mutable actions or credential scopes; detection remains file-content only.
- Observability: manual-action reasons become more deterministic, including expected target definition locations.
- Reliability and rollback: behavior is isolated to planning diagnostics; rollback is revert of planner/test/docs changes.
- Monitoring/alerting: existing upgrade report summary counts continue to reflect required manual actions.

## Risks and Tradeoffs
- Risk 1: legacy repositories with heavily diverged `make/platform.mk` may report many missing required targets at once.
- Tradeoff 1: broader early visibility is preferred over late validation failures and iterative trial-and-error.
