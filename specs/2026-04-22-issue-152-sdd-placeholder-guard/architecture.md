# Architecture

## Context
- Work item: 2026-04-22-issue-152-sdd-placeholder-guard
- Owner: bonos
- Date: 2026-04-22

## Stack and Execution Model
- Backend stack profile: none (no application code)
- Frontend stack profile: none
- Test automation profile: pytest unit tests in `tests/infra/test_tooling_contracts.py`; fast-lane via `make infra-contract-test-fast`
- Agent execution model: SDD blueprint track; quality-hooks-fast + quality-hardening-review gates

## Problem Statement
- What needs to change and why: `check_sdd_assets.py` does not validate required fields in `context_pack.md` or `architecture.md`; both can ship with scaffold placeholder values and pass `make quality-hardening-review`. Discovered in PR #151.
- Scope boundaries: extend `check_sdd_assets.py` to read a required-field list from `blueprint/contract.yaml` and assert each field is non-empty when `SPEC_READY=true`. No changes to scaffold templates.
- Out of scope: validation of `spec.md`, `plan.md`, `tasks.md`, `traceability.md`, or `hardening_review.md`.

## Bounded Contexts and Responsibilities
- Context A — SDD quality gate: `check_sdd_assets.py` is the authoritative validator for SDD work-item artifacts, run by `make quality-hardening-review`.
- Context B — SDD contract configuration: `blueprint/contract.yaml` is the source of truth for SDD governance rules; required-field lists are declared there to keep the validator contract-driven.

## High-Level Component Design
- Domain layer: none
- Application layer: none
- Infrastructure adapters: `check_sdd_assets.py` reads `work_item_document_required_fields` from the contract's `readiness_gate` section; for each declared document, it checks that every required field has a non-empty value using the existing `_parse_bullet_kv` helper.
- Presentation/API/workflow boundaries: `make quality-hardening-review` → `check_sdd_assets.py`; violations surface as named file+field error messages.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` `readiness_gate.work_item_document_required_fields` config; existing `_parse_bullet_kv` helper.
- Downstream dependencies: all SDD work items going forward must have required fields populated before `SPEC_READY=true`.
- Data/API/event contracts touched: `blueprint/contract.yaml` schema (additive new key under `readiness_gate`).

## Non-Functional Architecture Notes
- Security: none; read-only validation.
- Observability: violation messages name document path and field, giving operators a precise remediation target.
- Reliability and rollback: check is gated on `spec_ready=True`; in-progress specs are unaffected. Rollback: remove the new config key from `blueprint/contract.yaml`.
- Monitoring/alerting: none.

## Risks and Tradeoffs
- Risk 1: retroactively catches existing SPEC_READY=true work items with empty fields — fixed by filling in the `context_pack.md` for `issue-104-106-107` (the only remaining gap after the #108/#109 PR).
- Tradeoff 1: gating on `spec_ready=True` means in-progress specs can still have placeholders — acceptable since the guard's purpose is to prevent shipping, not planning.
