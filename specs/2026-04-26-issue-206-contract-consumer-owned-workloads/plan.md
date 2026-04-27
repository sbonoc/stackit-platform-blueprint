# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: Two list edits in one YAML file. No code changes required.
- Anti-abstraction gate: Uses existing `source_only_paths` mechanism without introducing new abstractions.
- Integration-first testing gate: Existing `test_upgrade_consumer.py` coverage for `source_only` classification applies. One new contract-level assertion for AC-001/AC-002 needed.
- Positive-path filter/transform test gate: AC-004 and AC-005 are positive-path assertions for the classification behavior and MUST be covered by unit tests before implementation completes.
- Finding-to-test translation gate: The consumer finding (contract re-patching after each upgrade) is structural — no deterministic automated assertion currently exists for "file must NOT be in required_files". A new contract content test must be added to translate this into a regression guard.

## Delivery Slices

### Slice 1 — Contract YAML modification
1. In `blueprint/contract.yaml`, remove the four manifest paths from `required_files`:
   - `infra/gitops/platform/base/apps/backend-api-deployment.yaml`
   - `infra/gitops/platform/base/apps/backend-api-service.yaml`
   - `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml`
   - `infra/gitops/platform/base/apps/touchpoints-web-service.yaml`
2. In `blueprint/contract.yaml`, add the four manifest paths to `source_only_paths`.
3. In `blueprint/contract.yaml`, remove the same four paths from `app_runtime_gitops_contract.required_paths_when_enabled`.

### Slice 2 — Test coverage
1. Add regression guard to `tests/blueprint/test_contract_stackit_runtime.py` or equivalent:
   - `test_seed_manifest_paths_not_in_required_files` — asserts the 4 paths are NOT in `required_files`
   - `test_seed_manifest_paths_in_source_only_paths` — asserts the 4 paths ARE in `source_only_paths`
   - `test_app_runtime_required_paths_contains_only_directory_and_kustomization` — asserts `app_runtime_gitops_contract.required_paths_when_enabled` contains no hardcoded manifest names
2. Verify AC-004 and AC-005 via a new targeted upgrade planner test (IMPL T-104):
   - Fixture path: `tests/fixtures/upgrade_consumer_renamed_manifests/` (create new)
   - Fixture contains consumer-renamed manifests (e.g. `my-api-deployment.yaml`, `my-api-service.yaml`) — names NOT in `source_only_paths` in the source blueprint
   - AC-004 assertion: upgrade plan with `allow_delete=True` against this fixture MUST show zero `OPERATION_DELETE` entries for the four blueprint seed paths and zero `OPERATION_CREATE` entries attempting to recreate them
   - AC-005 assertion: upgrade plan against a fixture with the original seed manifest names MUST classify those four paths as `source-only / skip` — no `OPERATION_UPDATE` or `OPERATION_DELETE`
3. Add fresh-init seeding regression guard (IMPL T-106):
   - Run `blueprint-init-repo` (or equivalent init fixture) and assert the 4 seed manifest files (`backend-api-deployment.yaml`, `backend-api-service.yaml`, `touchpoints-web-deployment.yaml`, `touchpoints-web-service.yaml`) are still created in `infra/gitops/platform/base/apps/` even though they no longer appear in `required_paths_when_enabled`
   - Guards against the init validation gap introduced by FR-003: seeding via `ensure_infra_template_file` must not rely on `required_paths_when_enabled` for file creation

### Slice 3 — Documentation
1. Write ADR: `docs/blueprint/architecture/decisions/ADR-2026-04-26-issue-206-contract-consumer-owned-workloads.md`.
2. No consumer-facing docs updates required (the change eliminates required consumer action — no new consumer steps).

### Slice 4 — Quality validation and publish
1. `make quality-hooks-fast`
2. `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-206-contract-consumer-owned-workloads`
3. `make quality-hardening-review`
4. `make test-unit-all`
5. Populate `pr_context.md` and `hardening_review.md`.
6. Commit and create PR.

## Change Strategy
- Migration/rollout sequence: Single commit on feature branch; merge to main via PR. Consumer repos receive the fix when they run `blueprint-upgrade` against the new blueprint tag.
- Backward compatibility policy: Fully backward-compatible. Consumers with the original seed manifest names: files are classified `source-only/skip` (unchanged). Consumers with renamed manifests: no more mandatory re-patching.
- Rollback plan: Revert the three list modifications in `blueprint/contract.yaml`. No data migration. No consumer action needed unless they have already upgraded (in which case they can add the 4 paths back manually).

## Validation Strategy (Shift-Left)
- Unit checks: Contract content regression guards (AC-001, AC-002, AC-003); upgrade planner classification tests for source_only paths (AC-004, AC-005).
- Contract checks: `make quality-sdd-check` — validates spec, plan, tasks, traceability artifacts.
- Integration checks: `make test-unit-all` — existing source-only classification tests pass.
- E2E checks: Not applicable.

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
- Notes: Contract YAML modification only. No app bootstrap, smoke, or test lane targets are affected.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR only.
- Consumer docs updates: none.
- Mermaid diagrams updated: architecture.md diagram in this spec.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): Not applicable.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: No changes.
- Alerts/ownership: No changes.
- Runbook updates: none.

## Risks and Mitigations
- Risk 1 → mitigation: Template-source CI may flag the 4 seed paths as uncovered if `source_only_paths` is not checked by `audit_source_tree_coverage`. Mitigation: verify `audit_source_tree_coverage` includes `source_only` in its coverage roots — it does (line 395 in `upgrade_consumer.py`).
- Risk 2 → mitigation: Consumers who intentionally keep the 4 paths in `required_files` as a preflight guard (to ensure seed files exist) lose this guard. Mitigation: the smoke assertion (issue #208) dynamically reads from `kustomization.yaml` and validates all declared manifests exist and have correct Deployment/Service kinds — a stronger runtime guard than the static path existence check.
