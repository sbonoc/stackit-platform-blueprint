# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `_classify_entries` baseline-absent branch | `scripts/lib/blueprint/upgrade_consumer.py` | additive-skip + additive-merge-required tests | `AGENTS.decisions.md`, ADR | upgrade plan JSON `action` field |
| FR-002 | SDD-C-005 | source==target → ACTION_SKIP | `scripts/lib/blueprint/upgrade_consumer.py` | additive-skip unit test | ADR | upgrade plan entry |
| FR-003 | SDD-C-005 | source!=target → ACTION_MERGE_REQUIRED | `scripts/lib/blueprint/upgrade_consumer.py` | additive-merge-required unit test | ADR | upgrade plan entry |
| FR-004 | SDD-C-005 | 3-way conflict guard | `scripts/lib/blueprint/upgrade_consumer.py` | regression guard test | ADR | upgrade plan entry |
| FR-005 | SDD-C-005 | helper relocation | `scripts/lib/infra/runtime_workload_helpers.py` | guard test (platform helper exists) | — | `make infra-smoke` |
| FR-006 | SDD-C-005 | helper relocation | `scripts/lib/infra/argocd_repo_credentials_json.py` | guard test (platform helper exists) | — | `make auth-reconcile-argocd-repo-credentials` |
| FR-007 | SDD-C-005 | caller path update | `scripts/bin/platform/apps/smoke.sh` | shell-source-graph check | — | `make infra-smoke` |
| FR-008 | SDD-C-005 | caller path update | `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` | shell-source-graph check | — | `make auth-reconcile-argocd-repo-credentials` |
| FR-009 | SDD-C-005, SDD-C-013 | missing-helper guard | `scripts/bin/quality/check_infra_shell_source_graph.py` | guard trigger test | — | `make quality-infra-shell-source-graph-check` |
| NFR-SEC-001 | SDD-C-009 | no new secret surface | all changed files | test suite clean | — | — |
| NFR-OBS-001 | SDD-C-010 | existing entry schema preserved | `scripts/lib/blueprint/upgrade_consumer.py` | entry field assertions | — | upgrade plan JSON |
| NFR-REL-001 | SDD-C-011 | backward-compatible classification | `scripts/lib/blueprint/upgrade_consumer.py` | regression guard test | — | — |
| NFR-OPS-001 | SDD-C-012 | deterministic guard error output | `scripts/bin/quality/check_infra_shell_source_graph.py` | guard trigger test asserting error message | — | `make quality-infra-shell-source-graph-check` |
| AC-001 | SDD-C-012 | preflight conflict_count excludes additive files | `scripts/lib/blueprint/upgrade_consumer.py` | additive-skip test | — | preflight JSON |
| AC-002 | SDD-C-012 | preflight manual_merge includes diverged additive files | `scripts/lib/blueprint/upgrade_consumer.py` | additive-merge-required test | — | preflight JSON |
| AC-003 | SDD-C-012 | helpers exist in scripts/lib/infra/ after upgrade | `scripts/lib/infra/` | blueprint-managed root distribution | — | upgrade apply output |
| AC-004 | SDD-C-012 | make infra-smoke succeeds | `scripts/bin/platform/apps/smoke.sh` | guard test | — | `make infra-smoke` |
| AC-005 | SDD-C-012 | make auth-reconcile-argocd-repo-credentials succeeds | `scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh` | guard test | — | `make auth-reconcile-argocd-repo-credentials` |
| AC-006 | SDD-C-012, SDD-C-013 | guard fails on missing helper | `scripts/bin/quality/check_infra_shell_source_graph.py` | guard trigger test | — | `make quality-infra-shell-source-graph-check` |
| AC-007 | SDD-C-012 | automated test coverage for all three scenarios | tests/blueprint/ + tests/infra/ | additive-skip, additive-merge-required, guard-trigger tests | — | test run output |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: all green
- Result summary:
  - `python3 -m pytest tests/blueprint/test_upgrade_consumer.py -q -k "additive"` → 3 passed (T-101, T-102, T-103)
  - `python3 -m pytest tests/blueprint/test_upgrade_consumer.py -q` → 30 passed (no regressions)
  - `python3 -m pytest tests/infra/test_tooling_contracts.py::PlatformPythonHelperGuardTests -v` → 3 passed (T-105, T-106, AC-006)
  - `make infra-contract-test-fast` → 24 passed
  - `make quality-infra-shell-source-graph-check` → nodes=30 edges=34 (pass)
  - `make quality-hooks-fast` → pass
  - `make infra-validate` → contract validation passed
  - `make quality-hardening-review` → pass
- Documentation validation:
  - `make quality-hooks-fast` → pass
  - `make infra-validate` → pass

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: notify generated-consumer maintainers that stale `scripts/lib/platform/apps/runtime_workload_helpers.py` and `scripts/lib/platform/auth/argocd_repo_credentials_json.py` copies can be deleted after upgrade to the fixed blueprint version.
