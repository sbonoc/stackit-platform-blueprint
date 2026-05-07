# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: implementation is additive — four new shell functions, three new Terraform files, one Helm values file, one module_execution.sh patch, state file extension, smoke hardening, tests, docs. No new abstractions.
- Anti-abstraction gate: reuse existing framework functions (`stackit_foundation_output_value_or_default`, `render_optional_module_values_file`, `write_state_file`, `run_helm_upgrade_install`, `run_helm_uninstall`); no new wrappers; Terraform follows the exact foundation resource pattern.
- Integration-first testing gate: write all tests RED in Slice 1 before any implementation; confirm RED state; then implement GREEN in Slices 2–3.
- Positive-path filter/transform test gate: not applicable — no filter or payload-transform logic.
- Finding-to-test translation gate: not applicable — no reproducible pre-PR smoke failures; existing scripts are structurally sound.

## Delivery Slices

### Slice 1 — Tests RED (no dependencies)
Write all test files with assertions that will fail against the current scaffold. Confirm RED state before implementing.

**Files:**
- `tests/infra/modules/kms/test_kms_module.py` — unit assertions: Terraform `main.tf` declares both resources (AC-001); `variables.tf` binds all inputs (AC-002); `outputs.tf` exposes all contract keys (AC-003); `kms_endpoint()` returns Vault Transit string on local lane (AC-005); `kms_apply.sh` `write_state_file` includes `endpoint` (AC-006); smoke passes with valid 5-key state (AC-007); smoke fails on empty `key_id` (AC-008); smoke fails on empty `key_ring_id` (AC-009); smoke fails on empty `endpoint` (AC-010); local Helm values has `fullnameOverride: "blueprint-vault"` and dev mode (AC-012); `kms_plan.sh` helm case writes plan state (AC-013); `module_execution.sh` kms local driver is `helm` (AC-014).
- `tests/infra/modules/kms/test_contract.py` — contract assertions: `module.contract.yaml` `outputs.produced` includes `KMS_ENDPOINT` (AC-004); runtime state fixture has all five declared output keys (AC-011).

**Validation:** `pytest tests/infra/modules/kms/ -v` — all assertions FAIL (RED); `make quality-hooks-fast` passes (lint/syntax only).

**Owner:** bonos

---

### Slice 2 — STACKIT Terraform Module (no upstream deps)
Can be developed in parallel with Slice 1; must complete before Slice 3.

**Files:**
- `infra/cloud/stackit/terraform/modules/kms/main.tf` — complete with `stackit_kms_keyring` (with `lifecycle { create_before_destroy = true }`) and `stackit_kms_key` resources; mirrors foundation pattern.
- `infra/cloud/stackit/terraform/modules/kms/variables.tf` — all contract inputs: `stackit_project_id`, `stackit_region`, `kms_key_ring_name`, `kms_key_name`, plus optional inputs (`kms_key_ring_description`, `kms_key_description`, `kms_key_algorithm`, `kms_key_purpose`, `kms_key_protection`, `kms_key_access_scope`, `kms_key_import_only`).
- `infra/cloud/stackit/terraform/modules/kms/outputs.tf` — all contract outputs: `kms_keyring_id`, `kms_keyring_display_name`, `kms_key_id`, `kms_key_display_name`.
- `infra/cloud/stackit/terraform/modules/kms/versions.tf` — `stackitcloud/stackit` provider version pin matching foundation (currently `= 0.88.0`).

**Validation:** `pytest tests/infra/modules/kms/test_kms_module.py -k "terraform" -v` — AC-001, AC-002, AC-003 turn GREEN; `terraform validate` passes.

**Owner:** bonos

---

### Slice 3 — Contract + Shell Layer + Local Helm Chart (depends on Slice 1 baseline)
Implement the contract YAML update, local Helm values, new shell functions, module_execution.sh patch, script updates, and smoke hardening.

**Files:**
- `blueprint/modules/kms/module.contract.yaml` — add `KMS_ENDPOINT` to `outputs.produced`.
- `infra/local/helm/kms/values.yaml` — Vault dev-mode Helm chart values: `fullnameOverride: "blueprint-vault"`, `server.dev.enabled: true`, resource limits ≤ 512 Mi RAM, `injector.enabled: false`.
- `scripts/lib/infra/kms.sh` — add `kms_endpoint()` (STACKIT lane: regional URL; local lane: Vault Transit path), `kms_render_values_file()`, `kms_reconcile_runtime_secret()`, `kms_enable_vault_transit()`.
- `scripts/lib/infra/module_execution.sh` — change `kms:plan|apply` local-profile driver from `noop` to `helm` pointing at rendered Vault values path; change `kms:destroy` local-profile driver from `noop` to `helm`.
- `scripts/bin/infra/kms_apply.sh` — add `helm` case: install Vault chart, call `kms_reconcile_runtime_secret`, call `kms_enable_vault_transit`; add `"endpoint=$(kms_endpoint)"` to `write_state_file`.
- `scripts/bin/infra/kms_plan.sh` — add `helm` case: log dry-run note, write plan state artifact.
- `scripts/bin/infra/kms_destroy.sh` — add `helm` case: call `run_helm_uninstall` and `kms_delete_runtime_secret`.
- `scripts/bin/infra/kms_smoke.sh` — add non-empty validation for `key_ring_id`, `key_id`, and `endpoint`; add `endpoint` to smoke state write.

**Validation:** `pytest tests/infra/modules/kms/ -v` — all ≥ 18 assertions GREEN; `pytest tests/infra/test_contract.py -k kms -v` passes; `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` passes.

**Owner:** bonos

---

### Slice 4 — Docs (depends on Slices 2 and 3)
Complete module documentation. No implementation changes.

**Files:**
- `docs/platform/modules/kms/README.md` — both-lanes usage, Vault Transit section (local lane), STACKIT KMS section (STACKIT lane), endpoint section (`KMS_ENDPOINT` usage), destroy semantics (ephemeral local vs. scheduled-deletion STACKIT), env-var reference table.

**Validation:** `make docs-build` and `make docs-smoke` pass (or document as N/A if no pipeline target).

**Owner:** bonos

---

## Dependency Map

```
Slice 1 (tests RED)
  └── Slice 3 (shell layer) ← test baseline needed
Slice 2 (Terraform)         ← independent, can run in parallel with Slice 1
  └── (Slice 3 needs Terraform files for test assertions)
Slice 3 (shell layer)
  └── Slice 4 (docs)
```

## Change Strategy
- Migration/rollout sequence: Slice 1 (RED) → Slice 2 + Slice 1 in parallel → Slice 3 (GREEN all) → Slice 4 (docs).
- Backward compatibility policy: fully backward compatible — `KMS_ENDPOINT` is a new additive output; no existing keys renamed or removed; local lane previously was a no-op so no consumers depend on the old noop behaviour.
- Rollback plan: revert shell function additions, module_execution.sh patch, and state file write changes; remove new Terraform files and Helm values; the local lane returns to noop behaviour.

## Validation Strategy (Shift-Left)

| Slice | Command | Assertions |
|---|---|---|
| Slice 1 | `pytest tests/infra/modules/kms/ -v` | All RED (confirms test quality) |
| Slice 2 | `pytest tests/infra/modules/kms/test_kms_module.py -k "terraform" -v` | AC-001, AC-002, AC-003 GREEN |
| Slice 2 | `terraform validate` in `infra/cloud/stackit/terraform/modules/kms/` | passes |
| Slice 3 | `pytest tests/infra/modules/kms/ -v` + `pytest tests/infra/test_contract.py -k kms -v` | All ≥ 18 assertions GREEN |
| Slice 3 | `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` | 0 violations |
| Slice 4 | `make docs-build && make docs-smoke` | Docs build clean |
| Pre-PR | `pytest tests/infra/modules/kms/ -v` + `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` | Full gate |

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
- Blueprint docs updates: `docs/platform/modules/kms/README.md` — complete from scaffold to production-grade documentation.
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
  - include key reviewer files (`scripts/lib/infra/kms.sh`, `scripts/lib/infra/module_execution.sh`, `scripts/bin/infra/kms_{plan,apply,smoke,destroy}.sh`, `infra/cloud/stackit/terraform/modules/kms/`, `infra/local/helm/kms/values.yaml`, `blueprint/modules/kms/module.contract.yaml`)
  - include validation evidence (pytest output showing ≥ 18 assertions passing, all GREEN; terraform validate output)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: all four scripts already use `start_script_metric_trap`; new `endpoint` state file key is emitted to the runtime env artifact; no additional instrumentation required.
- Alerts/ownership: no alert changes; `KMS_ENDPOINT` in state file enables operators to verify KMS API connectivity.
- Runbook updates: `docs/platform/modules/kms/README.md` updated with local Vault Transit access instructions and destroy semantics.

## Risks and Mitigations
- Risk 1: Vault Transit engine enablement requires pod readiness before `kms_enable_vault_transit()` runs → if pod not ready, call fails → mitigation: use `k8s_wait` helper or retry loop before Vault API call.
- Risk 2: STACKIT KMS REST API endpoint URL format is inferred from naming conventions → if format differs → `kms_endpoint()` returns incorrect URL on STACKIT lane → mitigation: endpoint URL is isolated in `kms.sh` and trivially patchable; smoke validates non-empty but not reachability against STACKIT on local CI.
