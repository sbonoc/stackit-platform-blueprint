# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: implementation is additive — two new shell functions, three new Terraform files plus one foundation outputs addition, one state file extension, smoke hardening, tests, docs. No new abstractions.
- Anti-abstraction gate: reuse existing framework functions (`stackit_foundation_output_value_or_default`, `render_optional_module_values_file`, `write_state_file`); no new wrappers; Terraform follows the exact foundation resource pattern.
- Integration-first testing gate: write all tests RED in Slice 1 before any implementation; confirm RED state; then implement GREEN in Slices 2–3.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic.
- Finding-to-test translation gate: not applicable — no reproducible pre-PR smoke failures; existing scripts are structurally sound.

## Delivery Slices

### Slice 1 — Tests RED (no dependencies)
Write all test files with assertions that will fail against the current scaffold. Confirm RED state before implementing.

**Files:**
- `tests/infra/modules/rabbitmq/test_rabbitmq_module.py` — unit assertions: Terraform `main.tf` declares both resources (AC-001); `variables.tf` binds all inputs (AC-002); `outputs.tf` exposes all contract keys (AC-003); foundation `outputs.tf` exposes `rabbitmq_management_url` (AC-013); `rabbitmq_vhost()` returns `/` (AC-005); `rabbitmq_management_url()` non-empty on local profile (AC-006); `rabbitmq_apply.sh` `write_state_file` call includes `vhost` and `management_url` (AC-007); smoke passes with valid 7-key state (AC-008); smoke fails on bad URI prefix (AC-009); smoke fails on empty `host` (AC-010); smoke fails on empty `vhost` (AC-011); smoke fails on empty `management_url` (AC-014).
- `tests/infra/modules/rabbitmq/test_contract.py` — contract assertions: `module.contract.yaml` `outputs.produced` includes `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` (AC-004); runtime state fixture has all seven declared output keys (AC-012).
- `scripts/lib/quality/test_pyramid_contract.json` — register both new test files under `unit` scope.

**Validation:** `pytest tests/infra/modules/rabbitmq/ -v` — all assertions FAIL (RED); `make quality-hooks-fast` passes (lint/syntax only).

**Owner:** bonos

---

### Slice 2 — STACKIT Terraform Module + Foundation Outputs (no upstream deps)
Can be developed in parallel with Slice 1; must complete before Slice 3.

**Files:**
- `infra/cloud/stackit/terraform/modules/rabbitmq/main.tf` — complete with `stackit_rabbitmq_instance` (with `lifecycle { create_before_destroy = true }`) and `stackit_rabbitmq_credential` resources.
- `infra/cloud/stackit/terraform/modules/rabbitmq/variables.tf` — all contract inputs: `stackit_project_id`, `stackit_region`, `rabbitmq_instance_name`, `rabbitmq_version`, `rabbitmq_plan_name`.
- `infra/cloud/stackit/terraform/modules/rabbitmq/outputs.tf` — all contract outputs: `rabbitmq_host`, `rabbitmq_port`, `rabbitmq_username`, `rabbitmq_password`, `rabbitmq_uri`, `rabbitmq_management_url` (from credential resource `management` attribute).
- `infra/cloud/stackit/terraform/modules/rabbitmq/versions.tf` — `stackitcloud/stackit` provider version pin matching foundation (currently `= 0.88.0`).
- `infra/cloud/stackit/terraform/foundation/outputs.tf` — add `rabbitmq_management_url` output reading `stackit_rabbitmq_credential.foundation[0].management`.

**Validation:** `pytest tests/infra/modules/rabbitmq/test_rabbitmq_module.py -k terraform or foundation -v` — AC-001, AC-002, AC-003, AC-013 turn GREEN.

**Owner:** bonos

---

### Slice 3 — Contract + Shell Layer (depends on Slice 1 for test baseline)
Implement the contract YAML update, new shell functions, state file extension, and smoke hardening.

**Files:**
- `blueprint/modules/rabbitmq/module.contract.yaml` — add `RABBITMQ_VHOST` and `RABBITMQ_MANAGEMENT_URL` to `outputs.produced`.
- `scripts/lib/infra/rabbitmq.sh` — add `rabbitmq_vhost()` (returns `/` on both lanes) and `rabbitmq_management_url()` (reads `stackit_foundation_output_value_or_default "rabbitmq_management_url" ""` on STACKIT lane; constructs `http://<host>:15672` on local lane).
- `scripts/bin/infra/rabbitmq_apply.sh` — add `"vhost=$(rabbitmq_vhost)"` and `"management_url=$(rabbitmq_management_url)"` to the `write_state_file` call.
- `scripts/bin/infra/rabbitmq_smoke.sh` — add non-empty validation for `host`, `port`, `vhost`, and `management_url` in addition to the existing URI prefix check.

**Validation:** `pytest tests/infra/modules/rabbitmq/ -v` — all assertions GREEN; `pytest tests/infra/test_contract.py -k rabbitmq -v` passes; `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` passes.

**Owner:** bonos

---

### Slice 4 — Docs (depends on Slices 2 and 3)
Complete module documentation. No implementation changes.

**Files:**
- `docs/platform/modules/rabbitmq/README.md` — both-lanes usage, credentials section (existing Secret pattern), vhost section (constant `/`, why), management URL section (how to access on each lane), smoke section, destroy section, env-var reference table.

**Validation:** `make docs-build` and `make docs-smoke` pass.

**Owner:** bonos

---

## Dependency Map

```
Slice 1 (tests RED)
  └── Slice 3 (shell layer) ← test baseline needed
Slice 2 (Terraform)         ← independent, can run in parallel with Slice 1
  └── Slice 3 (shell layer) ← foundation output must exist before rabbitmq_management_url() STACKIT path is testable
Slice 3 (shell layer)
  └── Slice 4 (docs)
```

## Change Strategy
- Migration/rollout sequence: Slice 1 (RED) → Slice 2 + Slice 1 in parallel → Slice 3 (GREEN all) → Slice 4 (docs).
- Backward compatibility policy: fully backward compatible — two new keys added to state file; no existing keys renamed or removed; no make-target changes.
- Rollback plan: revert shell function additions and state file write changes; remove new Terraform files; the Helm chart and Secret pattern are unchanged.

## Validation Strategy (Shift-Left)

| Slice | Command | Assertions |
|---|---|---|
| Slice 1 | `pytest tests/infra/modules/rabbitmq/ -v` | All RED (confirms test quality) |
| Slice 2 | `pytest tests/infra/modules/rabbitmq/test_rabbitmq_module.py -k "terraform or foundation" -v` | AC-001, AC-002, AC-003, AC-013 GREEN |
| Slice 3 | `pytest tests/infra/modules/rabbitmq/ -v` + `pytest tests/infra/test_contract.py -k rabbitmq -v` | All ≥ 20 assertions GREEN |
| Slice 3 | `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` | 0 violations |
| Slice 4 | `make docs-build && make docs-smoke` | Docs build clean |
| Pre-PR | `pytest tests/infra/modules/rabbitmq/ -v` + `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` | Full gate |

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
  - include requirement/contract coverage (all 14 ACs mapped)
  - include key reviewer files (`scripts/lib/infra/rabbitmq.sh`, `scripts/bin/infra/rabbitmq_{apply,smoke}.sh`, `infra/cloud/stackit/terraform/modules/rabbitmq/`, `blueprint/modules/rabbitmq/module.contract.yaml`)
  - include validation evidence (pytest output showing ≥ 20 assertions passing, all GREEN)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: all four scripts already use `start_script_metric_trap`; new state file keys are emitted to the runtime env artifact; no additional instrumentation required.
- Alerts/ownership: no alert changes; management URL added to state file enables operator access to the RabbitMQ management UI.
- Runbook updates: `docs/platform/modules/rabbitmq/README.md` updated with management URL access instructions.

## Risks and Mitigations
- Risk 1: Foundation Terraform output `rabbitmq_management_url` missing at apply time → `stackit_foundation_output_value_or_default` returns empty string → smoke check on `management_url` fails explicitly → no silent incorrect state. Mitigation: the smoke failure message is actionable; fix is to re-run foundation apply after Slice 2 ships.
- Risk 2: Bitnami RabbitMQ chart may expose management plugin on a different port in some versions → local-lane `rabbitmq_management_url()` constructs URL from port 15672 → if chart changes, URL may be stale. Mitigation: port 15672 is a stable default; a version upgrade work item would cover this.
