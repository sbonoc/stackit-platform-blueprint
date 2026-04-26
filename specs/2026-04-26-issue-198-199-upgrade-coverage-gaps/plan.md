# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: satisfied — two dataclass fields, one tuple extension, one custom yaml.Dumper subclass; no new module boundaries or abstractions introduced.
- Anti-abstraction gate: satisfied — all additions use direct PyYAML primitives (`yaml.Dumper` subclass) and plain dataclass fields; no wrapper layers.
- Integration-first testing gate: satisfied — contract validation covered by `make infra-validate`; schema parsing covered by unit tests that exercise the real YAML loader against real contract YAML structure.
- Positive-path filter/transform test gate: satisfied — `test_feature_gated_paths_covered` asserts that a file under a `feature_gated` root is NOT flagged as uncovered (positive-path assertion on filter inclusion).
- Finding-to-test translation gate: satisfied — all four findings from issues #198, #199, #205 are translated into failing tests first (TDD red → green); no manual-only smoke findings remain.

## Delivery Slices

### Slice 1 — Add `blueprint-template-smoke` and `infra-argocd-topology-validate` to `VALIDATION_TARGETS` (red → green)
**Scope**: `tests/blueprint/test_upgrade_consumer.py`, `scripts/lib/blueprint/upgrade_consumer_validate.py`
**Depends on**: none (independent)
**Owner**: Software Engineer
**Delivers**: FR-001, FR-005 → AC-001, AC-006

1. Add two failing unit tests in a new `TestValidationTargets` class:
   - `test_blueprint_template_smoke_in_validation_targets` — asserts `"blueprint-template-smoke" in validate_module.VALIDATION_TARGETS`
   - `test_infra_argocd_topology_validate_in_validation_targets` — asserts `"infra-argocd-topology-validate" in validate_module.VALIDATION_TARGETS`
2. Add `"blueprint-template-smoke"` and `"infra-argocd-topology-validate"` to the `VALIDATION_TARGETS` tuple in `upgrade_consumer_validate.py` — both tests turn green.
3. Run `make quality-hooks-fast` to confirm no regressions.

**Validation gate**: both unit tests green; `make quality-hooks-fast` passes.

### Slice 2 — Add `feature_gated` ownership class (red → green)
**Scope**: `tests/blueprint/test_upgrade_consumer.py`, `scripts/lib/blueprint/contract_schema.py`, `scripts/lib/blueprint/upgrade_consumer.py`
**Depends on**: none (independent of Slice 1; must precede Slices 3 and 4)
**Owner**: Software Engineer
**Delivers**: FR-002, FR-003 → AC-002, AC-005, AC-007

1. Add a failing unit test in `TestAuditSourceTreeCoverage` that calls `audit_source_tree_coverage` with `feature_gated={"apps/catalog"}` and asserts `apps/catalog/manifest.yaml` is NOT in the returned uncovered list.
2. Add `feature_gated: list[str] = field(default_factory=list)` to `RepositoryOwnershipPathClasses` in `contract_schema.py`; add `feature_gated_paths` property to `RepositoryContract`.
3. Parse `feature_gated` from the YAML in the schema loader (parallel to how `conditional_scaffold` is parsed).
4. Add `feature_gated: set[str] = frozenset()` parameter to `audit_source_tree_coverage`; include it in `all_coverage_roots`.
5. Update the call site in `upgrade_consumer.py` to pass `set(contract.repository.feature_gated_paths)`.
6. Update `validate_plan_uncovered_source_files` error message to reference `feature_gated`.
7. Run tests — the new test turns green; pre-existing tests remain green.

**Validation gate**: new `TestAuditSourceTreeCoverage` test green; all pre-existing `TestAuditSourceTreeCoverage` tests green.

### Slice 3 — Wire `feature_gated` into contract validation (red → green)
**Scope**: `tests/blueprint/test_validate_contract.py` (or existing contract test file), `scripts/bin/blueprint/validate_contract.py`
**Depends on**: Slice 2 (reads `feature_gated_paths` from the schema object introduced there)
**Owner**: Software Engineer
**Delivers**: FR-002 (validation path) → AC-003

1. Add a test that constructs a minimal contract dict with `feature_gated: [apps/catalog]` and asserts no validation errors are returned for the ownership section.
2. In `validate_contract.py`, read `feature_gated_paths` from the loaded contract; confirm no disk-presence check and no equality constraint against `optional_modules`.
3. Run tests — green.

**Validation gate**: new contract-validation test green.

### Slice 4 — Populate `feature_gated` in contract YAML + mirror (green validation)
**Scope**: `blueprint/contract.yaml`, `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml`
**Depends on**: Slices 2 and 3 (schema and validator must be in place before `make infra-validate` can pass)
**Owner**: Software Engineer
**Delivers**: FR-004 → AC-004

1. Add `feature_gated:` list under `ownership_path_classes` in `blueprint/contract.yaml` with the three `apps/catalog` paths.
2. Mirror the identical addition to the bootstrap template counterpart.
3. Run `make infra-validate` — confirms AC-004.

**Validation gate**: `make infra-validate` passes.

### Slice 5 — Fix `yaml.dump` indentation in `resolve_contract_upgrade.py` (red → green)
**Scope**: `tests/blueprint/test_upgrade_pipeline.py`, `scripts/lib/blueprint/resolve_contract_upgrade.py`
**Depends on**: none (independent — different module, no shared state with Slices 1–4)
**Owner**: Software Engineer
**Delivers**: FR-006 → AC-008

1. Add a failing unit test `test_resolve_contract_yaml_dump_uses_indented_style` in the existing `TestResolveContractConflict` class (or equivalent) that:
   - Calls `resolve_contract_conflict` with a fixture containing a `required_files` entry longer than 80 characters.
   - Reads the written `blueprint/contract.yaml` as raw text and asserts no line matches the indentless-sequence pattern (`^- ` at column 0 after a mapping key) and no scalar is wrapped (no continuation-indent lines).
   - Asserts the written YAML is parseable by `load_blueprint_contract` without error.
2. Add `_IndentedDumper` class before the write call (overrides `increase_indent` with `indentless=False`).
3. Replace the bare `yaml.dump(...)` call with `yaml.dump(..., Dumper=_IndentedDumper, width=4096)`.
4. Run tests — the new test turns green; all pre-existing `TestResolveContractConflict` tests remain green.

**Validation gate**: new `test_resolve_contract_yaml_dump_uses_indented_style` green; all pre-existing `TestResolveContractConflict` tests green.

### Slice 6 — Quality gate + final evidence
**Scope**: all
**Depends on**: Slices 1–5 (all implementation slices complete)
**Owner**: Software Engineer

1. Run `make quality-hooks-fast` and `make infra-validate` — both pass.
2. Confirm `make quality-sdd-check` passes.
3. Capture test output as evidence in `traceability.md`.

**Validation gate**: `make quality-hooks-fast` and `make infra-validate` both pass; evidence attached.

## Change Strategy
- Migration/rollout sequence: Slices 1 and 5 are independent and can be executed in any order or in parallel. Slices 2→3→4 are sequentially dependent (schema before validator before YAML). Slice 6 (quality gate) is last. Natural ordering: 1, 2, 3, 4, 5, 6.
- Backward compatibility policy: `audit_source_tree_coverage` new `feature_gated` parameter defaults to `frozenset()` — all existing call sites continue to work unchanged. `RepositoryOwnershipPathClasses.feature_gated` uses `field(default_factory=list)` — existing YAML files without the key parse without error.
- Rollback plan: `git revert` of the PR. No database migrations, no infra state, no consumer-repo changes required.

## Validation Strategy (Shift-Left)
- Unit checks: new `TestValidationTargets.test_blueprint_template_smoke_in_validation_targets`; new `TestAuditSourceTreeCoverage.test_feature_gated_paths_covered`; new contract-validation test for `feature_gated` field parsing; new `test_resolve_contract_yaml_dump_uses_indented_style`. All in `tests/blueprint/`.
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
- Risk 3: `_IndentedDumper` changes output format for existing consumers of the resolved contract → mitigation: all pre-existing `TestResolveContractConflict` tests assert on parsed data (not raw YAML text), so they remain valid; the raw-text assertion in the new test is the only format-sensitive assertion.
