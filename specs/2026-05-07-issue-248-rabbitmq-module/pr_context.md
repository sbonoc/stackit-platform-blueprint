# PR Context

## Summary
- Work item: 2026-05-07-issue-248-rabbitmq-module
- Objective: Extend the rabbitmq module with `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` contract outputs: implement the STACKIT Terraform standalone module (`stackit_rabbitmq_instance` + `stackit_rabbitmq_credential`), add `rabbitmq_vhost()` and `rabbitmq_management_url()` shell functions, extend the apply state file and harden the smoke script, and complete module documentation.
- Scope boundaries: `scripts/lib/infra/rabbitmq.sh`, `scripts/bin/infra/rabbitmq_apply.sh`, `scripts/bin/infra/rabbitmq_smoke.sh`, `blueprint/modules/rabbitmq/module.contract.yaml`, `infra/cloud/stackit/terraform/modules/rabbitmq/`, `infra/cloud/stackit/terraform/foundation/outputs.tf`, `docs/platform/modules/rabbitmq/README.md`, `tests/infra/modules/rabbitmq/`. No make target changes; no consumer onboarding changes; no helm values changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
- Acceptance criteria covered: AC-001 through AC-014
- Contract surfaces changed: `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` added to `outputs.produced` in `module.contract.yaml`. Runtime state file gains two new keys (`vhost=/`, `management_url=<url>`); consumers reading existing keys (`host`, `port`, `username`, `password`, `uri`) are unaffected.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/rabbitmq.sh` — two new functions: `rabbitmq_vhost()` (constant `/`) and `rabbitmq_management_url()` (dual-lane)
  - `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` — full Terraform resource implementation
  - `infra/cloud/stackit/terraform/foundation/outputs.tf` — new `rabbitmq_management_url` output from `stackit_rabbitmq_credential.foundation[0].management`
  - `scripts/bin/infra/rabbitmq_smoke.sh` — four additional non-empty guard checks
- High-risk files: `scripts/bin/infra/rabbitmq_apply.sh` (two new keys added to write_state_file call)

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/infra/modules/rabbitmq/ -v` (22/22 PASSED), `make quality-docs-check-changed` (PASS after seed sync), `make infra-validate` (PASS), `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (all checks PASSED)
- Result summary: 22 new tests added, all green. Pyramid ratios within thresholds.
- Artifact references: `specs/2026-05-07-issue-248-rabbitmq-module/traceability.md`

## Risk and Rollback
- Main risks: (1) `management_url` key is new in the state file — existing consumers reading `artifacts/infra/rabbitmq_runtime.env` that do not expect the new key are not affected (new keys are additive); (2) smoke now fails when `host`, `vhost`, or `management_url` is empty — any existing state files missing these keys will cause smoke to fail until re-applied.
- Rollback strategy: Revert the PR branch. No persistent infrastructure changes are required — the Terraform module files are additive and the foundation outputs change is backward-compatible (returns `null` when `rabbitmq_enabled=false`).

## Deferred Proposals
- none
