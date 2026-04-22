# PR Context

## Summary
- Work item: Issues #104, #106, #107 — additive-file conflict reclassification and platform helper namespace correction
- Objective: eliminate false conflict signals in generated-consumer upgrade preflight for additive blueprint-required files, and ensure all Python helpers required by distributed platform scripts are present in upgraded generated-consumer repos
- Scope boundaries: `upgrade_consumer.py` classification logic, two helper file relocations from `scripts/lib/platform/` to `scripts/lib/infra/`, two shell-script caller updates, one guard extension in `check_infra_shell_source_graph.py`

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007
- Contract surfaces changed: none (no `contract.yaml`, API, or make-target changes; `scripts/lib/infra/` was already a `blueprint_managed_roots` entry)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` (`_classify_entries` restructure: lines ~516–606)
  - `scripts/lib/infra/runtime_workload_helpers.py` (new location)
  - `scripts/lib/infra/argocd_repo_credentials_json.py` (new location)
  - `scripts/bin/quality/check_infra_shell_source_graph.py` (`_validate_platform_python_refs` addition)
- High-risk files:
  - `scripts/bin/platform/apps/smoke.sh` (line 122: `runtime_workload_helpers.py` path update)
  - `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` (line 49: `argocd_repo_credentials_json.py` path update)

## Validation Evidence
- Required commands executed:
  - `python3 -m pytest tests/blueprint/test_upgrade_consumer.py -q -k "additive"` → 3 passed
  - `python3 -m pytest tests/blueprint/test_upgrade_consumer.py -q` → 30 passed
  - `python3 -m pytest tests/infra/test_tooling_contracts.py::PlatformPythonHelperGuardTests -v` → 3 passed
  - `make infra-contract-test-fast` → 24 passed
  - `make quality-infra-shell-source-graph-check` → nodes=30 edges=34 (pass)
  - `python3 scripts/bin/quality/check_sdd_assets.py` → SDD assets validated (pass)
  - `make infra-validate` → contract validation passed
- Result summary: all tests green; no regressions; guard correctly detects missing platform Python helpers
- Artifact references: `tests/blueprint/test_upgrade_consumer.py` (new `AdditiveFileClassificationTests` class); `tests/infra/test_tooling_contracts.py` (new `PlatformPythonHelperGuardTests` class)

## Risk and Rollback
- Main risks:
  - Risk 1: stale `scripts/lib/platform/apps/runtime_workload_helpers.py` and `scripts/lib/platform/auth/argocd_repo_credentials_json.py` copies may persist in already-upgraded generated-consumer repos. Safe to delete after next upgrade.
  - Risk 2: guard false-positives for commented-out or conditional-existence python3 references. Mitigated: guard strips comment lines before scanning.
- Rollback strategy: classification fix commit and helper relocation are isolated; either can be reverted independently without affecting the other.

## Deferred Proposals
- Full audit of all `scripts/bin/platform/**` Python helper references beyond the two identified in #106/#107 (covered automatically by the guard going forward).
- Resync or postcheck flow changes beyond the classification fix (out of scope; no contract change required).
