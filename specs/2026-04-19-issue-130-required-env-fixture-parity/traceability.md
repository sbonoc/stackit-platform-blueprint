# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Canonical required-env fixture hydration | tests/_shared/helpers.py | tests.infra.test_optional_module_required_env_contract.ModuleRequiredEnvFixtureContractTests.test_module_flags_env_populates_required_env_for_all_enabled_modules | specs/2026-04-19-issue-130-required-env-fixture-parity/spec.md | fast-lane contract diagnostics |
| FR-002 | SDD-C-005 | Contract parity detector for required env defaults | tests/infra/test_optional_module_required_env_contract.py | tests.infra.test_optional_module_required_env_contract.ModuleRequiredEnvFixtureContractTests.test_module_flags_env_has_parameter_for_every_optional_module_toggle; tests.infra.test_optional_module_required_env_contract.ModuleRequiredEnvFixtureContractTests.test_required_env_contract_parity_reports_no_missing_defaults | specs/2026-04-19-issue-130-required-env-fixture-parity/plan.md | deterministic missing list in pytest output |
| FR-003 | SDD-C-005 | Fast lane inclusion of parity test | scripts/bin/infra/contract_test_fast.sh | make infra-contract-test-fast | docs/reference/generated/core_targets.generated.md | quality-hooks-fast / infra-contract-test-fast output |
| NFR-SEC-001 | SDD-C-009 | Placeholder-safe deterministic defaults for required env | scripts/lib/blueprint/init_repo_env.py; tests/_shared/helpers.py | tests.blueprint.test_init_repo_env.InitRepoEnvTests.test_enabled_module_required_inputs_split_by_sensitivity | specs/2026-04-19-issue-130-required-env-fixture-parity/spec.md | no live secret requirements in fast lane |
| NFR-OBS-001 | SDD-C-010 | Sorted, deterministic parity diagnostics | tests/infra/test_optional_module_required_env_contract.py | pytest -q tests/infra/test_optional_module_required_env_contract.py | specs/2026-04-19-issue-130-required-env-fixture-parity/hardening_review.md | sorted missing diagnostics |
| NFR-REL-001 | SDD-C-011 | Deterministic contract traversal and union coverage | tests/infra/test_optional_module_required_env_contract.py | pytest -q tests/infra/test_optional_module_required_env_contract.py | specs/2026-04-19-issue-130-required-env-fixture-parity/spec.md | stable pass/fail across runs |
| NFR-OPS-001 | SDD-C-018 | Explicit remediation path in fast lane | scripts/bin/infra/contract_test_fast.sh; tests/infra/test_optional_module_required_env_contract.py | make quality-hooks-fast | specs/2026-04-19-issue-130-required-env-fixture-parity/pr_context.md | command-level remediation (`make infra-contract-test-fast`) |
| AC-001 | SDD-C-012 | Enabled-module required env hydration | tests/_shared/helpers.py | tests.infra.test_optional_module_required_env_contract.ModuleRequiredEnvFixtureContractTests.test_module_flags_env_populates_required_env_for_all_enabled_modules | specs/2026-04-19-issue-130-required-env-fixture-parity/pr_context.md | fixture env payload contains required keys |
| AC-002 | SDD-C-012 | Missing-required-env fail-fast check | tests/infra/test_optional_module_required_env_contract.py | tests.infra.test_optional_module_required_env_contract.ModuleRequiredEnvFixtureContractTests.test_required_env_contract_parity_reports_no_missing_defaults | specs/2026-04-19-issue-130-required-env-fixture-parity/pr_context.md | deterministic parity failure output |
| AC-003 | SDD-C-012 | Fast lane wiring | scripts/bin/infra/contract_test_fast.sh | make infra-contract-test-fast; make quality-hooks-fast | specs/2026-04-19-issue-130-required-env-fixture-parity/pr_context.md | fast lane includes parity test file |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003

## Validation Summary
- Required bundles executed:
  - `pytest -q tests/infra/test_optional_module_required_env_contract.py`
  - `python3 -m unittest tests.blueprint.test_init_repo_env -v`
  - `make infra-contract-test-fast`
  - `make quality-hooks-fast`
  - `make docs-build`
  - `make docs-smoke`
  - `make quality-hardening-review`
  - `make quality-hooks-run`
- Result summary:
  - all commands above passed.
  - targeted optional-module integration spot-check (`pytest -q tests/infra/test_optional_modules.py -k "test_postgres_module_flow or test_workflows_module_flow"`) failed due sandbox-only kubeconfig write permission, not fixture parity logic.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: optionally expose a reusable helper to materialize required-env defaults for tests and init flows from one typed API surface.
