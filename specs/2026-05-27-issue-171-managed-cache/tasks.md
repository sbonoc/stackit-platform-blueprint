# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm Q-1 (STACKIT Redis TF resource name) is resolved before starting Slice 3

## Slice 1 — Module contract + shell lib skeleton
- [ ] T-101 Write failing test assertions (contract file, enable flag, outputs, shell functions)
- [ ] T-102 Create `blueprint/modules/managed-cache/module.contract.yaml`
- [ ] T-103 Register module in `blueprint/contract.yaml` under `optional_modules`
- [ ] T-104 Create `scripts/lib/infra/managed_cache.sh` with stubbed functions
- [ ] T-105 Gate: `make infra-contract-test-fast` green

## Slice 2 — Make targets
- [ ] T-201 Write failing test assertions (make targets, bin script existence)
- [ ] T-202 Add make targets to `make/blueprint.generated.mk` and Makefile template
- [ ] T-203 Create stub `scripts/bin/infra/managed_cache_{plan,apply,smoke,destroy}.sh`
- [ ] T-204 Gate: `make infra-contract-test-fast` green

## Slice 3 — TF module (blocked on Q-1)
- [ ] T-301 Resolve Q-1: verify STACKIT Redis TF resource name from provider schema
- [ ] T-302 Write failing test assertions (TF files, resource declarations, foundation wiring)
- [ ] T-303 Create TF module files (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`)
- [ ] T-304 Add `managed_cache_enabled` variable to foundation `variables.tf`
- [ ] T-305 Wire module call and outputs in foundation TF workspace
- [ ] T-306 Gate: `make infra-validate` + `make infra-contract-test-fast` green

## Slice 4 — Local lane Helm values
- [ ] T-401 Write failing test assertions (Helm values file existence and chart config)
- [ ] T-402 Create `infra/local/helm/managed-cache/values.yaml`
- [ ] T-403 Gate: `make infra-contract-test-fast` green

## Slice 5 — Shell lib + apply script — full implementation
- [ ] T-501 Write failing test assertions (URI scheme, lane branching, state file sans password)
- [ ] T-502 Implement `managed_cache.sh` with `is_stackit_profile` lane branching
- [ ] T-503 Implement `managed_cache_apply.sh` with `write_state_file` (no password)
- [ ] T-504 Implement `managed_cache_plan.sh` and `managed_cache_destroy.sh`
- [ ] T-505 Gate: `make infra-contract-test-fast` green

## Slice 6 — Smoke script + bootstrap templates + docs
- [ ] T-601 Implement `managed_cache_smoke.sh`
- [ ] T-602 Create bootstrap template `scripts/templates/infra/bootstrap/infra/local/helm/managed-cache/values.yaml`
- [ ] T-603 Add `ensure_infra_template_file` call in `bootstrap.sh`
- [ ] T-604 Create `docs/platform/modules/managed-cache/README.md`
- [ ] T-605 Gate: `make quality-hooks-fast` green (all 11 checks)

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: infra-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: infra-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: module does not add new port-forward targets

## Publish
- [ ] T-901 Run `make quality-hooks-fast` — all checks pass
- [ ] T-902 Run `python3 -m pytest tests/infra/modules/managed-cache/ -x -q` — ≥ 10 assertions pass
- [ ] T-903 Complete `pr_context.md`, `hardening_review.md`, `traceability.md`, `evidence_manifest.json`
- [ ] T-904 Mark PR ready for review
