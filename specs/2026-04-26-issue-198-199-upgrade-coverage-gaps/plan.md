# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Keep initial implementation scope minimal and explicit.
  - Avoid speculative future-proof abstractions.
- Anti-abstraction gate:
  - Prefer direct framework primitives over wrapper layers unless justified.
  - Keep model representations singular unless boundary separation is required.
- Integration-first testing gate:
  - Define contract and boundary tests before implementation details.
  - Ensure realistic environment coverage for integration points.
- Positive-path filter/transform test gate:
  - For any filter or payload-transform logic, at least one unit test MUST assert that a matching fixture value returns a record.
  - Positive-path assertions MUST verify relevant output fields remain intact after filtering/transform.
  - Empty-result-only assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from smoke/`curl`/deterministic manual checks MUST be translated into a failing automated test first.
  - The implementation fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices

### Slice 1 — Add `blueprint-template-smoke` to `VALIDATION_TARGETS` (red → green)
**Scope**: `tests/blueprint/test_upgrade_consumer.py`, `scripts/lib/blueprint/upgrade_consumer_validate.py`

1. Add a failing unit test in `TestUpgradeConsumerValidate` (or a new `TestValidationTargets` class) that asserts `"blueprint-template-smoke" in validate_module.VALIDATION_TARGETS`.
2. Add `"blueprint-template-smoke"` to the `VALIDATION_TARGETS` tuple in `upgrade_consumer_validate.py` — the test turns green.
3. Run `make quality-hooks-fast` to confirm no regressions.

### Slice 2 — Add `feature_gated` ownership class (red → green)
**Scope**: `tests/blueprint/test_upgrade_consumer.py`, `scripts/lib/blueprint/contract_schema.py`, `scripts/lib/blueprint/upgrade_consumer.py`

1. Add a failing unit test in `TestAuditSourceTreeCoverage` that calls `audit_source_tree_coverage` with `feature_gated={"apps/catalog"}` and asserts `apps/catalog/manifest.yaml` is NOT in the returned uncovered list.
2. Add `feature_gated: list[str] = field(default_factory=list)` to `RepositoryOwnershipPathClasses` in `contract_schema.py`; add `feature_gated_paths` property to `RepositoryContract`.
3. Parse `feature_gated` from the YAML in the schema loader (parallel to how `conditional_scaffold` is parsed).
4. Add `feature_gated: set[str] = frozenset()` parameter to `audit_source_tree_coverage`; include it in `all_coverage_roots`.
5. Update the call site in `upgrade_consumer.py` to pass `set(contract.repository.feature_gated_paths)`.
6. Update `validate_plan_uncovered_source_files` error message to reference `feature_gated`.
7. Run tests — the new test turns green; pre-existing tests remain green.

### Slice 3 — Wire `feature_gated` into contract validation (red → green)
**Scope**: `tests/blueprint/test_validate_contract.py` (or existing contract test file), `scripts/bin/blueprint/validate_contract.py`

1. Add a test that constructs a minimal contract dict with `feature_gated: [apps/catalog]` and asserts no validation errors are returned for the ownership section.
2. In `validate_contract.py`, read `feature_gated_paths` from the loaded contract; confirm no disk-presence check and no equality constraint against `optional_modules`.
3. Run tests — green.

### Slice 4 — Populate `feature_gated` in contract YAML + mirror (green validation)
**Scope**: `blueprint/contract.yaml`, `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`

1. Add `feature_gated:` list under `ownership_path_classes` in `blueprint/contract.yaml` with the three `apps/catalog` paths.
2. Mirror the identical addition to the bootstrap template counterpart.
3. Run `make infra-validate` — confirms AC-004.

### Slice 5 — Quality gate + final evidence
**Scope**: all

1. Run `make quality-hooks-fast` and `make infra-validate` — both pass.
2. Confirm `make quality-sdd-check` passes (SPEC_READY gate deferred to sign-off round).
3. Capture test output as evidence in `traceability.md`.

## Change Strategy
- Migration/rollout sequence: Slices 1–5 are independent of each other within the same PR; natural ordering minimises broken-intermediate-state risk (tests first, then implementation, then YAML).
- Backward compatibility policy: `audit_source_tree_coverage` new `feature_gated` parameter defaults to `frozenset()` — all existing call sites continue to work unchanged. `RepositoryOwnershipPathClasses.feature_gated` uses `field(default_factory=list)` — existing YAML files without the key parse without error.
- Rollback plan: `git revert` of the PR. No database migrations, no infra state, no consumer-repo changes required.

## Validation Strategy (Shift-Left)
- Unit checks: new `TestValidationTargets.test_blueprint_template_smoke_in_validation_targets`; new `TestAuditSourceTreeCoverage.test_feature_gated_paths_covered`; new contract-validation test for `feature_gated` field parsing. All in `tests/blueprint/`.
- Contract checks: `make infra-validate` (covers `validate_contract.py` against `blueprint/contract.yaml`).
- Integration checks: `make quality-hooks-fast` — runs the full fast-lane hook suite against the modified files.
- E2E checks: none required — no runtime paths changed.

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
- Notes: Python/YAML-only changes to upgrade pipeline validation tooling; no app onboarding surface modified.

## Documentation Plan (Document Phase)
- Blueprint docs updates: none required — the change is internal to validation tooling.
- Consumer docs updates: none required — `feature_gated` is a blueprint-internal concept.
- Mermaid diagrams updated: none required.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — no HTTP routes or filter logic changed.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: `validate_plan_uncovered_source_files` error string updated — no new log lines or metrics.
- Alerts/ownership: none.
- Runbook updates: none required.

## Risks and Mitigations
- Risk 1: Stale YAML loader silently ignores unknown keys → mitigation: confirm `feature_gated` list is actually parsed by adding an explicit assertion in a test that reads the real `blueprint/contract.yaml` and checks `len(contract.repository.feature_gated_paths) > 0`.
- Risk 2: Bootstrap template drift → mitigation: Slice 4 explicitly mirrors `blueprint/contract.yaml` to the template counterpart, and `make infra-validate` enforces the check.
