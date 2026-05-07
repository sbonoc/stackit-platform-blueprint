# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `KMS_ENDPOINT` was absent from `module.contract.yaml` `outputs.produced` and the runtime state file; added as first-class contract output so consumer ESO mappings can reference the lane-appropriate KMS API base URL.
- Finding 2: `kms_smoke.sh` only validated `key_id` presence with a bare `grep -q '^key_id='`; explicit non-empty checks for `key_ring_id`, `key_id`, and `endpoint` added with the `.+` suffix — consistent with the hardening standard established in `postgres_smoke.sh` and `rabbitmq_smoke.sh`.
- Finding 3: The STACKIT standalone Terraform module `main.tf` was a 7-line stub with no provider resources; full `stackit_kms_keyring` + `stackit_kms_key` implementation added with `lifecycle { create_before_destroy = true }` (NFR-REL-001) and a complete `variables.tf` + `outputs.tf`.
- Finding 4: The local lane (`kms:plan`, `kms:apply`, `kms:destroy`) dispatched to a `noop` driver — developers had no KMS-equivalent locally. First-class Vault Transit local lane added via `helm` driver in `module_execution.sh`, with Vault Helm chart provisioning, Transit secrets engine enablement, K8s Secret token delivery (NFR-SEC-001), and a full local state file.
- Finding 5: Runtime state file lacked the `endpoint` key and used `key_ring=` instead of `key_ring_name=`; state file now writes all five contract output keys (`key_ring_id`, `key_id`, `key_ring_name`, `key_name`, `endpoint`) after apply (NFR-OPS-001).

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: No new metric emitters added. `start_script_metric_trap` was already present in all four bin scripts (`kms_plan.sh`, `kms_apply.sh`, `kms_smoke.sh`, `kms_destroy.sh`); no changes required (NFR-OBS-001 satisfied by pre-existing instrumentation).
- Operational diagnostics updates: `kms_smoke.sh` hardened with three `log_fatal` checks (`key_ring_id`, `key_id`, `endpoint`) and smoke state now includes `endpoint=$(kms_endpoint)`, improving failure diagnosis when individual state keys are missing or empty.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Additive changes only. Five new functions in `kms.sh` (`kms_endpoint`, `kms_render_values_file`, `kms_reconcile_runtime_secret`, `kms_enable_vault_transit`, `kms_delete_runtime_secret`) follow the single-responsibility pattern established by all other lane-aware functions in the file. NFR-SEC-001 compliance achieved via `{{KMS_VAULT_ROOT_TOKEN}}` template substitution (not envsubst) in `values.yaml`, with the resolved token delivered exclusively via K8s Secret. No cross-boundary imports; no new abstractions beyond the established `render_optional_module_values_file` + `apply_optional_module_secret_from_literals` pattern.
- Test-automation and pyramid checks: 23 new tests added across `test_kms_module.py` (21 tests across 7 test classes) and `test_contract.py` (2 tests). All classified as `unit` in `test_pyramid_contract.json`. 23/23 tests pass. Pyramid ratios: unit=95.77% (min>60%), integration=3.31% (max≤30%), e2e=0.92% (max≤10%).
- Documentation/diagram/CI/skill consistency checks: `docs/platform/modules/kms/README.md` completed with all required sections (dual-lane table, local Vault Transit prerequisites, STACKIT KMS section, `KMS_ENDPOINT` usage example, destroy semantics, optional inputs table). Bootstrap template mirror synced via `sync_blueprint_template_docs.py`. ADR approved, traceability matrix complete (16 requirements + 14 ACs mapped). Contract metadata regenerated (`contract_metadata.generated.md`).

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI component (NFR-A11Y-001 declared N/A in spec.md)
- [x] SC 2.1.1 (Keyboard): N/A — no UI component
- [x] SC 2.4.7 (Focus Visible): N/A — no UI component
- [x] SC 1.4.1 (Use of Color): N/A — no UI component
- [x] SC 3.3.1 (Error Identification): N/A — no UI component
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no browser-facing surface

## Proposals Only (Not Implemented)
- Proposal 1: `KMS_KEY_ROTATION_PERIOD` — add to `module.contract.yaml` and `stackit_kms_key` when the STACKIT provider exposes a `rotation_period` attribute. Deferred because `stackit_kms_key` v0.88.0 does not expose this attribute; shipping a no-op contract input would mislead consumers. Parked — trigger: on-scope: infra.
- Proposal 2: Vault HA / persistent storage for the local lane — Vault standalone mode with raft storage and a PVC. Deferred because dev-mode ephemeral storage is sufficient for local development; HA adds PVC provisioning and startup complexity disproportionate to local dev needs. Parked — trigger: on-scope: infra.
