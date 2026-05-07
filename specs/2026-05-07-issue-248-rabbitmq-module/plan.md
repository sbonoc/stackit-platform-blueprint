# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Implementation is additive: two new shell functions, two new Terraform files, one state file extension, smoke hardenening, tests, docs. No new abstractions.
- Anti-abstraction gate:
  - Shell functions follow the existing pattern in `rabbitmq.sh`. Terraform follows the exact foundation resource pattern. No wrapper layers.
- Integration-first testing gate:
  - Contract tests assert `module.contract.yaml` outputs match state file keys. Unit tests assert each function returns the expected value. No integration environment required.
- Positive-path filter/transform test gate:
  - Not applicable — no filter or payload-transform logic in scope.
- Finding-to-test translation gate:
  - No reproducible pre-PR failures exist. All new test cases are green-path assertions for new functionality.

## Delivery Slices

1. **Slice 1 — STACKIT Terraform module**: implement `variables.tf`, `outputs.tf`, and complete `main.tf` with `stackit_rabbitmq_instance` + `stackit_rabbitmq_credential` resources. Update `infra/cloud/stackit/terraform/foundation/outputs.tf` to expose `rabbitmq_management_url`.
2. **Slice 2 — Contract and shell layer**: update `module.contract.yaml` with two new outputs; add `rabbitmq_vhost()` and `rabbitmq_management_url()` to `rabbitmq.sh`; extend `rabbitmq_apply.sh` state file write; harden `rabbitmq_smoke.sh` validations.
3. **Slice 3 — Tests**: write `tests/infra/modules/rabbitmq/` test suite (≥ 20 assertions) covering all ACs.
4. **Slice 4 — Docs**: write `docs/platform/modules/rabbitmq/README.md` with both-lanes usage, credentials, vhost, management URL, smoke, and destroy sections.

## Change Strategy
- Migration/rollout sequence: all changes are additive to the module; no existing outputs are renamed or removed; existing consumers are unaffected.
- Backward compatibility policy: fully backward compatible — two new keys added to state file, no existing keys changed.
- Rollback plan: revert shell function additions and state file write changes; remove new Terraform files; the Helm chart and Secret pattern are unchanged.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/infra/modules/rabbitmq/ -v` — covers Terraform module structure, shell function outputs, state file keys, smoke pass/fail scenarios.
- Contract checks: `pytest tests/infra/test_contract.py -k rabbitmq` — confirms `module.contract.yaml` outputs match state file keys.
- Integration checks: none required at this tier; module is validated against the local lane Helm chart via existing `make infra-rabbitmq-apply`.
- E2E checks: none in scope for this work item.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: This work item affects only infra module wrappers; no app onboarding make targets are added or changed.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/rabbitmq/README.md` — complete from scaffold to production-grade docs.
- Consumer docs updates: none — module contract additive change only.
- Mermaid diagrams updated: none required for docs; architecture diagram in `architecture.md` is spec-only.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP route handlers in scope.
- Publish checklist:
  - include requirement/contract coverage (all 13 ACs mapped)
  - include key reviewer files (`scripts/lib/infra/rabbitmq.sh`, `scripts/bin/infra/rabbitmq_{apply,smoke}.sh`, `infra/cloud/stackit/terraform/modules/rabbitmq/`, `blueprint/modules/rabbitmq/module.contract.yaml`)
  - include validation evidence (pytest output showing ≥ 20 assertions passing)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: all four scripts already use `start_script_metric_trap`; new state file keys are emitted to the runtime env artifact; no additional instrumentation required.
- Alerts/ownership: no alert changes; management URL added to state file enables operator access to the RabbitMQ management UI.
- Runbook updates: `docs/platform/modules/rabbitmq/README.md` updated with management URL access instructions.

## Risks and Mitigations
- Risk 1: Foundation Terraform output `rabbitmq_management_url` missing at apply time → `stackit_foundation_output_value_or_default` returns empty string → smoke check on `management_url` fails explicitly → no silent incorrect state. Mitigation: the smoke failure message is actionable; fix is to re-run foundation apply with updated outputs file.
- Risk 2: Bitnami RabbitMQ chart may expose management plugin on a different port in some versions → local-lane `rabbitmq_management_url()` constructs URL from port 15672 → if chart changes, URL may be stale. Mitigation: out of scope for this work item; port is a stable default; a version upgrade work item would cover this.
