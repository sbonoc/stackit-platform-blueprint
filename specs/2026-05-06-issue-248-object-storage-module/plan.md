# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Implement only what the contract declares — no speculative multi-bucket logic; no ESO wiring.
- Anti-abstraction gate: Follow existing rabbitmq/opensearch patterns directly; do not introduce a new abstraction layer for credential reconciliation.
- Integration-first testing gate: Write contract test (`test_contract.py`) and module unit tests (`test_object_storage_module.py`) in RED before any implementation changes.
- Positive-path filter/transform test gate: Not applicable — no filter or payload-transform logic in scope.
- Finding-to-test translation gate: Not applicable — no pre-PR reproducible failures known at intake time.

## Delivery Slices

### Slice 1 — Tests RED (TDD baseline)
Write failing tests before touching implementation. All tests MUST be red at commit boundary.

**Files written:**
- `tests/infra/modules/object-storage/test_contract.py` — 4 assertions (5 if Q-1 → Option A): runtime state fixture has `endpoint`, `bucket`, `access_key`, `secret_key` keys; dashboard_url absent (not in contract)
- `tests/infra/modules/object-storage/test_object_storage_module.py` — assertions covering:
  - Plan/apply/smoke/destroy script presence and sourcing
  - Values seed uses `auth.existingSecret`, NOT `auth.rootPassword`/`auth.rootUser`
  - Values seed contains `{{OBJECT_STORAGE_CREDENTIAL_SECRET_NAME}}` placeholder, NOT `{{OBJECT_STORAGE_ACCESS_KEY}}`/`{{OBJECT_STORAGE_SECRET_KEY}}`
  - `object_storage.sh` defines `object_storage_reconcile_runtime_secret`, `object_storage_delete_runtime_secret`, `object_storage_credential_secret_name`
  - `object_storage_render_values_file()` does NOT pass `OBJECT_STORAGE_ACCESS_KEY=` or `OBJECT_STORAGE_SECRET_KEY=` to render
  - Apply script calls `object_storage_reconcile_runtime_secret` before `run_helm_upgrade_install`
  - Destroy script calls `object_storage_delete_runtime_secret` after `run_helm_uninstall`
  - Terraform module declares `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential`
  - `versions.sh` defines `OBJECT_STORAGE_HELM_CHART_VERSION_PIN`, `OBJECT_STORAGE_LOCAL_IMAGE_TAG`, client image tag

**Commit:** `test(issue-248-object-storage-module): RED — contract + module unit tests`

### Slice 2 — Terraform standalone module
Implement the standalone STACKIT Terraform module.

**Files changed:**
- `infra/cloud/stackit/terraform/modules/object-storage/main.tf` — implement `stackit_objectstorage_bucket`, `stackit_objectstorage_credentials_group`, `stackit_objectstorage_credential` (mirror foundation inline resources)
- `infra/cloud/stackit/terraform/modules/object-storage/variables.tf` — `stackit_project_id`, `stackit_region`, `bucket_name`, `credentials_group_name`, `expiration_timestamp`
- `infra/cloud/stackit/terraform/modules/object-storage/outputs.tf` — `bucket_name`, `endpoint_url`, `access_key`, `secret_access_key`, `region`
- `infra/cloud/stackit/terraform/modules/object-storage/versions.tf` — `required_version >= 1.13.0`; `required_providers { stackit }`

Tests turned green: Terraform module resource assertions.

**Commit:** `feat(issue-248-object-storage-module): implement STACKIT standalone Terraform module`

### Slice 3 — Execution class fix + Secret-backed credentials for local lane
Fix the `module_execution.sh` class from `provider_backed` to `fallback_runtime` for the local lane (consistency with rabbitmq/opensearch), and migrate from plaintext credentials in values render to Secret-backed pattern.

**Files changed:**
- `scripts/lib/infra/module_execution.sh`:
  - `object-storage:plan | object-storage:apply` local branch: change `optional_module_execution_set "provider_backed"` → `optional_module_execution_set "fallback_runtime"`
  - `object-storage:destroy` local branch: same change
- `scripts/lib/infra/object_storage.sh`:
  - Add `object_storage_credential_secret_name()` → `printf '%s-auth' "$OBJECT_STORAGE_HELM_RELEASE"`
  - Add `object_storage_reconcile_runtime_secret()` — calls `apply_optional_module_secret_from_literals` with `root-user=$OBJECT_STORAGE_ACCESS_KEY` and `root-password=$OBJECT_STORAGE_SECRET_KEY`
  - Add `object_storage_delete_runtime_secret()` — calls `delete_optional_module_secret` with Secret name
  - Update `object_storage_render_values_file()`: remove `OBJECT_STORAGE_ACCESS_KEY=` and `OBJECT_STORAGE_SECRET_KEY=`; add `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME=$(object_storage_credential_secret_name)`
- `infra/local/helm/object-storage/values.yaml` (materialized seed):
  - Replace `auth.rootUser`/`auth.rootPassword` with `auth.existingSecret: "{{OBJECT_STORAGE_CREDENTIAL_SECRET_NAME}}"` (remove `rootUser`/`rootPassword` keys entirely)
- `scripts/templates/infra/bootstrap/infra/local/helm/object-storage/values.yaml` (seed template):
  - Same change as above
- `scripts/bin/infra/object_storage_apply.sh`:
  - In `helm)` case: call `object_storage_reconcile_runtime_secret` before `object_storage_render_values_file`
- `scripts/bin/infra/object_storage_destroy.sh`:
  - In `helm)` case: call `object_storage_delete_runtime_secret` after `run_helm_uninstall`
- `scripts/bin/infra/bootstrap.sh`:
  - In `object-storage)` case: replace `OBJECT_STORAGE_ACCESS_KEY=$OBJECT_STORAGE_ACCESS_KEY` and `OBJECT_STORAGE_SECRET_KEY=$OBJECT_STORAGE_SECRET_KEY` with `OBJECT_STORAGE_CREDENTIAL_SECRET_NAME=$(object_storage_credential_secret_name)`
- `tests/infra/test_tooling_contracts.py`:
  - Add `test_optional_module_execution_resolves_local_fallback_modes_for_object_storage` asserting `class=fallback_runtime`, `driver=helm`
  - Add `test_optional_module_execution_resolves_stackit_provider_backed_object_storage_modes` asserting `class=provider_backed`, `driver=foundation_contract`

Tests turned green: class=fallback_runtime assertion for local lane; Secret-backed credential assertions (existingSecret in values, no plaintext, reconcile/delete functions present).

**Commit:** `fix(issue-248-object-storage-module): fallback_runtime class + Secret-backed MinIO credentials for local lane`

### Slice 4 — Contract + smoke + docs
Update contract YAML, smoke script (add region check if Q-1 → Option A), complete README.

**Files changed (pending Q-1 resolution):**
- `blueprint/modules/object-storage/module.contract.yaml`: add `OBJECT_STORAGE_REGION` to `outputs.produced` (if Q-1 → Option A)
- `scripts/bin/infra/object_storage_apply.sh`: add `region=$OBJECT_STORAGE_REGION` to `write_state_file` call
- `scripts/bin/infra/object_storage_smoke.sh`: add `region` check (grep for `^region=`)
- `docs/platform/modules/object-storage/README.md`: complete env-var reference table, smoke output schema, credentials section, version migration notes, destroy instructions
- `scripts/templates/blueprint/bootstrap/docs/platform/modules/object-storage/README.md`: sync via `sync_platform_seed_docs.py`

Tests turned green: contract test for `region` key (if Q-1 → Option A).

**Commit:** `feat(issue-248-object-storage-module): contract + region output + complete README`

### Slice 5 — Quality gates green
Run all gates and fix any violations.

- `pytest tests/infra/modules/object-storage/ -v` — all green
- `pytest tests/infra/test_tooling_contracts.py -k object` — green
- `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` — all green
- `make quality-docs-check-changed` — green
- `make infra-validate` — green

**Commit:** any fixes found

## Change Strategy
- Migration/rollout sequence: Slices are independent but MUST follow order: RED tests → Terraform module → Secret credentials → Contract/docs → Quality gates.
- Backward compatibility policy: Make target names unchanged. Runtime state schema additive only (adding `region` key). Values seed change is breaking only for consumers who check for `auth.rootUser`/`auth.rootPassword` in rendered values — these are internal blueprint artifacts not consumer-contractual.
- Rollback plan: Local — `OBJECT_STORAGE_ENABLED=true make infra-object-storage-destroy` (runs Helm uninstall + Secret delete); STACKIT — `OBJECT_STORAGE_ENABLED=true make infra-object-storage-destroy` (foundation reconcile destroy); code — revert `object_storage.sh` credential functions, revert values seed to plaintext.

## Validation Strategy (Shift-Left)
- Unit checks: `pytest tests/infra/modules/object-storage/` — all assertions per test classes above.
- Contract checks: `pytest tests/infra/test_tooling_contracts.py -k object_storage` — module execution resolver returns `helm` for local.
- Integration checks: `make infra-validate` — Terraform validate on standalone module.
- E2E checks: not required for this work item (no live cluster provisioning in CI).

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap` — N/A (infra-only, not app scope)
  - `apps-smoke` — N/A (infra-only, not app scope)
  - `backend-test-unit` — N/A (infra-only, not app scope)
  - `backend-test-integration` — N/A (infra-only, not app scope)
  - `backend-test-contracts` — N/A (infra-only, not app scope)
  - `backend-test-e2e` — N/A (infra-only, not app scope)
  - `touchpoints-test-unit` — N/A (infra-only, not app scope)
  - `touchpoints-test-integration` — N/A (infra-only, not app scope)
  - `touchpoints-test-contracts` — N/A (infra-only, not app scope)
  - `touchpoints-test-e2e` — N/A (infra-only, not app scope)
  - `test-unit-all` — N/A (infra-only, not app scope)
  - `test-integration-all` — N/A (infra-only, not app scope)
  - `test-contracts-all` — N/A (infra-only, not app scope)
  - `test-e2e-all-local` — N/A (infra-only, not app scope)
  - `infra-port-forward-start` — N/A (module does not add new port-forward targets)
  - `infra-port-forward-stop` — N/A (module does not add new port-forward targets)
  - `infra-port-forward-cleanup` — N/A (module does not add new port-forward targets)
- App onboarding impact: no-impact (make targets for app lanes unchanged)
- Notes: The object-storage module's `infra-object-storage-apply` is a prerequisite for consumer apps that set `OBJECT_STORAGE_ENABLED=true`, but the app-level make targets themselves are not modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/object-storage/README.md` (dual-lane usage, env-var reference, credentials, smoke, rollback, version migration)
- Consumer docs updates: none
- Mermaid diagrams updated: `architecture.md` (dual-lane flow, secret pattern)
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-docs-check-changed`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not applicable — no HTTP route handlers or new API endpoints.
- Publish checklist:
  - Requirement and contract coverage per FR/NFR/AC IDs
  - Key reviewer files listed
  - Validation evidence: test counts, quality gate results
  - Risk and rollback instructions

## Operational Readiness
- Logging/metrics/traces: `start_script_metric_trap` per script; state file path logged on apply success; smoke logs pass/fail.
- Alerts/ownership: none additional.
- Runbook updates: `docs/platform/modules/object-storage/README.md`.

## Risks and Mitigations
- Risk 1: Bitnami MinIO chart `auth.existingSecret` key names differ across chart versions → mitigation: verify `root-user`/`root-password` against chart 17.0.21 templates via `helm template` before committing.
- Risk 2: Q-1 unresolved at implementation start → mitigation: implement Slices 1–3 without REGION; defer Slice 4 REGION addition until Q-1 answered.
