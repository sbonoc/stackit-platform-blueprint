# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `_is_consumer_owned_workload()` predicate + `_classify_entries()` guard | `scripts/lib/blueprint/upgrade_consumer.py` | `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` | ADR-2026-04-26-issue-207-apps-prune-exclusion.md | plan output `ownership=consumer-owned-workload` |
| FR-002 | SDD-C-005 | Predicate explicitly excludes `kustomization.yaml` | `scripts/lib/blueprint/upgrade_consumer.py` | `test_kustomization_yaml_in_base_apps_is_not_protected` | spec.md Explicit Exclusions | n/a |
| FR-003 | SDD-C-005 | `reason` field set to distinct string on skip entry | `scripts/lib/blueprint/upgrade_consumer.py` | `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` (asserts reason) | n/a | plan JSON output |
| NFR-SEC-001 | SDD-C-009 | Pure predicate with no I/O | `_is_consumer_owned_workload()` in `upgrade_consumer.py` | `test_is_consumer_owned_workload_returns_true_for_consumer_manifest` | architecture.md Non-Functional Notes | n/a |
| NFR-OBS-001 | SDD-C-010 | Unique `reason` string on skip entries | `upgrade_consumer.py` line in guard | `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` (asserts `in "consumer workload manifest"`) | n/a | plan output |
| NFR-REL-001 | SDD-C-011 | Guard is additive; no existing branch changed | `upgrade_consumer.py` | full test suite passes (make test-unit-all) | n/a | n/a |
| NFR-OPS-001 | SDD-C-010 | `ownership="consumer-owned-workload"` on skip entry | `upgrade_consumer.py` guard | `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` (asserts ownership) | n/a | plan JSON |
| AC-001 | SDD-C-012 | skip/none/consumer-owned-workload entry | `upgrade_consumer.py` | `test_consumer_workload_manifests_not_deleted_when_allow_delete_true` | n/a | n/a |
| AC-002 | SDD-C-012 | kustomization.yaml flows through normal classification → delete | `upgrade_consumer.py` | `test_kustomization_yaml_in_base_apps_is_not_protected` | n/a | n/a |
| AC-003 | SDD-C-012 | Predicate returns False for kustomization.yaml | `_is_consumer_owned_workload()` | `test_is_consumer_owned_workload_returns_false_for_kustomization` | n/a | n/a |
| AC-004 | SDD-C-012 | Predicate returns False for paths outside base/apps/ | `_is_consumer_owned_workload()` | `test_is_consumer_owned_workload_returns_false_for_unrelated_path`, `test_is_consumer_owned_workload_returns_false_for_nested_subdirectory_path` | n/a | n/a |
| AC-005 | SDD-C-012 | Additive fix; no existing tests modified | all of `upgrade_consumer.py` | `make test-unit-all` — all pre-existing tests pass | n/a | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
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
  - AC-004
  - AC-005

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make quality-sdd-check SPEC_SLUG=2026-04-26-issue-207-apps-prune-exclusion`, `make quality-hardening-review`, `make test-unit-all`
- Result summary: all passed; 6 new tests green; no pre-existing test regressions
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Issue #206 — general contract schema mechanism for consumer-owned path declarations; when merged, this bridge guard should be unified with the new schema approach.
