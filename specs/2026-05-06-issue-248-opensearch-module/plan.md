# Implementation Plan

## Implementation Start Gate
- `SPEC_READY: true` — confirmed 2026-05-06. Implementation is unblocked.
- Q-1 resolved: Option A — `infra-opensearch-{plan,apply,smoke,destroy}` with profile-routing.
- Q-2 resolved: Option A — proceed with `stackit_opensearch_credential`; stop condition applies if admin-level assumption fails.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: implement only what the contract requires — no speculative extensions beyond the 8 declared outputs.
- Anti-abstraction gate: use existing script patterns (`opensearch_init_env`, `run_helm_upgrade_install`, `write_state_file`) directly; do not introduce new abstraction layers.
- Integration-first testing gate: write `tests/infra/modules/opensearch/test_contract.py` state-file assertions before implementing the scripts that produce the state file.
- Positive-path filter/transform test gate: no filter/payload-transform logic in scope; N/A.
- Finding-to-test translation gate: any smoke failure found during manual testing MUST become an automated assertion before implementation fix.

## Delivery Slices

Owner: Platform Engineer (Software Engineer). All slices execute on branch `codex/2026-05-06-issue-248-opensearch-module`.

### Dependency Map

```
Slice 1 (Terraform)  ──────────────────────────────────────────┐
Slice 2 (versions.sh) ──┬──────────────────────────────────────┼──► Slice 9 (Docs)
                        ├──► Slice 3 (opensearch.sh) ──┬───────┤         │
                        │                               ├──► Slice 5 ──► Slice 6 ──► Slice 10
                        └──► Slice 4 (Helm chart) ─────┘       │
                                                               Slice 7 (smoke)
                              Slice 8 (contract test) ◄────────┘ (mock fixture, schema from Slice 3)
```

- **Slices 1 and 2** are independent — can start in parallel.
- **Slices 3 and 4** depend on Slice 2 (version pins) — can start in parallel after Slice 2.
- **Slice 5** depends on Slices 3 + 4 (opensearch.sh functions + Helm chart present).
- **Slice 6** depends on Slices 2 + 3 + 5 (versions.sh, opensearch.sh, module_execution routing).
- **Slice 7** depends on Slice 3 (state file schema).
- **Slice 8** (contract test) depends on Slice 3 for state key schema; written as mock fixture test first.
- **Slices 9 and 10** depend on all prior slices.

### Slice 1 — Terraform module (STACKIT lane)
**Dependencies:** none (can start immediately)
**Scope:** `infra/cloud/stackit/terraform/modules/opensearch/main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`

**Red → Green:**
1. Write failing test: `test_terraform_module_has_opensearch_resources` — asserts that `main.tf` declares `stackit_opensearch_instance` and `stackit_opensearch_credential` resource blocks.
2. Implement `main.tf` with `stackit_opensearch_instance` (with `lifecycle { create_before_destroy = true }`) and `stackit_opensearch_credential`; `variables.tf` binding `OPENSEARCH_INSTANCE_NAME`, `OPENSEARCH_VERSION`, `OPENSEARCH_PLAN_NAME`; `outputs.tf` exposing all 8 contract outputs.
3. Test passes.

**Per-slice gate:** `make test-unit-all`

### Slice 2 — versions.sh pins
**Dependencies:** none (can start immediately in parallel with Slice 1)
**Scope:** `scripts/lib/infra/versions.sh`

**Red → Green:**
1. Write failing test: `test_opensearch_version_pins_declared` — asserts that `versions.sh` exports `OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_REGISTRY`, `OPENSEARCH_LOCAL_IMAGE_REPOSITORY`, `OPENSEARCH_LOCAL_IMAGE_TAG`.
2. Add the four variables to `versions.sh`.
3. Test passes.

**Per-slice gate:** `make test-unit-all`

### Slice 3 — opensearch.sh local lane functions
**Dependencies:** Slice 2 (version pins needed for `OPENSEARCH_HELM_CHART_VERSION` default)
**Scope:** `scripts/lib/infra/opensearch.sh`

**Red → Green:**
1. Write failing tests: `test_opensearch_local_host_returns_service_hostname`, `test_opensearch_local_port_returns_9200`, `test_opensearch_local_scheme_returns_http`.
2. Update `opensearch_init_env()` to set `OPENSEARCH_NAMESPACE`, `OPENSEARCH_HELM_RELEASE`, `OPENSEARCH_HELM_CHART`, `OPENSEARCH_HELM_CHART_VERSION`, `OPENSEARCH_USERNAME` (local default), `OPENSEARCH_PASSWORD` (local default); add `opensearch_local_service_host()`, `opensearch_local_port()`, `opensearch_local_scheme()` functions; update `opensearch_host()`, `opensearch_port()`, `opensearch_scheme()`, `opensearch_uri()`, `opensearch_username()`, `opensearch_password()` to branch on `is_local_profile`.
3. Add `opensearch_render_values_file()` analogous to `postgres_render_values_file()`.
4. Tests pass.

**Per-slice gate:** `make test-unit-all`

### Slice 4 — Local Helm chart
**Dependencies:** Slice 2 (image tag and chart version needed in values.yaml) — parallel with Slice 3
**Scope:** `infra/local/helm/opensearch/values.yaml`

**Red → Green:**
1. Write failing test: `test_opensearch_local_helm_values_file_exists_and_parses`.
2. Add `infra/local/helm/opensearch/values.yaml` with `fullnameOverride: "blueprint-opensearch"`, dev-sized resources (≤1 GB RAM), persistence disabled, admin credentials matching `OPENSEARCH_USERNAME`/`OPENSEARCH_PASSWORD` defaults.
3. Test passes.

**Per-slice gate:** `make test-unit-all`

### Slice 5 — module_execution.sh routing update
**Dependencies:** Slices 3 + 4 (opensearch.sh functions + Helm chart file present for rendered values path)
**Scope:** `scripts/lib/infra/module_execution.sh`

**Red → Green:**
1. Write failing test: `test_opensearch_local_profile_routes_to_helm_driver` — asserts `resolve_optional_module_execution "opensearch" "apply"` sets `OPTIONAL_MODULE_EXECUTION_DRIVER=helm` under a local profile.
2. Update `opensearch:plan | opensearch:apply` and `opensearch:destroy` cases to use `helm` driver with `$(rendered_module_helm_values_file "opensearch")` when `is_local_profile`.
3. Test passes.

**Per-slice gate:** `make test-unit-all`

### Slice 6 — opensearch_apply.sh update
**Dependencies:** Slices 2 + 3 + 5 (versions.sh pins, opensearch.sh render helper, module_execution routing)
**Scope:** `scripts/bin/infra/opensearch_apply.sh`

**Red → Green:**
1. Write failing test: `test_opensearch_apply_local_calls_helm_upgrade` (mock test asserting helm driver branch is taken).
2. Add `helm` case to `opensearch_apply.sh`: call `opensearch_render_values_file`, then `run_helm_upgrade_install`; source `scripts/lib/infra/versions.sh` and `scripts/lib/infra/fallback_runtime.sh`.
3. Test passes.

**Per-slice gate:** `make test-unit-all`

### Slice 7 — opensearch_smoke.sh implementation
**Dependencies:** Slice 3 (state file key schema and opensearch_uri() function)
**Scope:** `scripts/bin/infra/opensearch_smoke.sh`

**Red → Green:**
1. Write failing test: `test_opensearch_smoke_fails_when_uri_empty` and `test_opensearch_smoke_passes_with_valid_uri`.
2. Implement `opensearch_smoke.sh`: read `opensearch_runtime` state file; assert `uri` is non-empty and matches expected scheme for profile; assert `dashboard_url` is non-empty.
3. Tests pass.

**Per-slice gate:** `make test-unit-all`

### Slice 8 — Contract tests
**Dependencies:** Slice 3 (state file key schema); written as mock-fixture test to satisfy integration-first gate before Slice 6 produces real state
**Scope:** `tests/infra/modules/opensearch/test_contract.py`

**Red → Green:**
1. Write failing tests asserting all 8 contract outputs are present in a mock `opensearch_runtime` state file.
2. Wire test to read from `artifacts/infra/opensearch_runtime.env` (or mock state fixture).
3. Tests pass.

**Per-slice gate:** `make test-unit-all`

### Slice 9 — Documentation
**Dependencies:** Slices 1–8 (all implementation complete; README documents real paths and values)
**Scope:** `docs/platform/modules/opensearch/README.md`

**Red → Green:**
1. Update README with dual-lane usage examples (local: `OPENSEARCH_ENABLED=true OPENSEARCH_INSTANCE_NAME=... make infra-opensearch-apply`; STACKIT: same target, different profile), env-var reference table, and prerequisite notes.
2. Run `make quality-docs-check-changed` — passes.

**Per-slice gate:** `make quality-hooks-fast`

### Slice 10 — Pre-PR quality sweep
**Dependencies:** Slices 1–9 (all implementation and docs complete)
**Scope:** full quality gate sweep

1. Run `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` and fix all violations.
2. Run `make infra-validate`.
3. Run `make quality-sdd-check`.
4. Record evidence in `pr_context.md`.

## Change Strategy
- Migration/rollout sequence: local lane is additive (was `noop`, now `helm`); STACKIT Terraform module is additive (new standalone module; foundation continues to manage inline). No state migration required.
- Backward compatibility policy: existing `infra-opensearch-apply` make target name is preserved; STACKIT lane behavior is unchanged; local lane changes from `noop` to active `helm` provisioning.
- Rollback plan: local lane — `helm uninstall blueprint-opensearch`; STACKIT lane — set `OPENSEARCH_ENABLED=false` and run `infra-opensearch-destroy`.

## Validation Strategy (Shift-Left)
- Unit checks: `make test-unit-all` after each slice; includes bash function tests via `tests/infra/` Python test suite.
- Contract checks: `tests/infra/modules/opensearch/test_contract.py` — state file output key assertions.
- Integration checks: `infra-opensearch-apply` on docker-desktop local profile; `infra-opensearch-smoke` validates outputs. Real STACKIT apply is maintainer's responsibility.
- E2E checks: none — infra-only work item; no user-facing flows.

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
- Notes: The opensearch module's `infra-opensearch-apply` is a prerequisite for consumer apps that set `OPENSEARCH_ENABLED=true`, but the app-level make targets themselves are not modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/modules/opensearch/README.md` — dual-lane usage, env-var reference, prerequisite notes.
- Consumer docs updates: none in this PR (consumer-side adoption is a separate PR).
- Mermaid diagrams updated: architecture.md contains flowcharts for lane routing and output contract shapes.
- Docs validation commands:
  - `make quality-docs-check-changed`
  - `make quality-docs-check-module-contract-summaries-sync`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): N/A — no HTTP route handler changes.
- Publish checklist:
  - include requirement/contract coverage (FR-001…FR-010, AC-001…AC-010)
  - include key reviewer files
  - include validation evidence (local apply output, smoke pass, test results)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: existing `infra_opensearch_apply` metric trap covers success/failure; no new signals.
- Alerts/ownership: managed by platform team; STACKIT managed instance health monitoring is provider-side.
- Runbook updates: `docs/platform/modules/opensearch/README.md` updated with destroy/rollback instructions.

## Risks and Mitigations
- Risk 1 (admin credential level — Q-2 resolved) → residual risk: assumption that `stackit_opensearch_credential` is admin-level could fail during Slice 1 apply; stop condition protocol applies — post on issue #248 and halt if confirmed non-admin.
- Risk 2 (naming convention — Q-1 resolved) → Option A implemented; comment posted on issue #248 explaining deviation.
- Risk 3 (Bitnami image availability) → mitigation: pin exact image tag in versions.sh and values.yaml; use `bitnamilegacy/opensearch` registry consistent with other modules.
