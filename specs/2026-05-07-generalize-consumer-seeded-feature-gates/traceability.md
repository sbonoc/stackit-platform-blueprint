# Traceability Matrix — Generalize Consumer-Seeded Feature Gates

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | SDD-C-004, SDD-C-007 | `consumer_seeded_feature_gates` YAML schema | `blueprint/contract.yaml` | T-016, T-029 | `architecture.md § Module Structure`, `spec.md § Contract Changes` | `make infra-validate` |
| REQ-002 | SDD-C-007, SDD-C-008 | `resolve_consumer_seeded_feature_gates()` | `scripts/lib/blueprint/init_repo_contract.py` | T-002–T-007, T-023 | `architecture.md § Flow` | `make infra-validate` |
| REQ-003 | SDD-C-007, SDD-C-008 | `seed_consumer_owned_files()` prune step | `scripts/lib/blueprint/init_repo_contract.py` | T-008–T-009, T-023 | `architecture.md § Flow` | `make infra-validate` |
| REQ-004 | SDD-C-004 | `claude_ai_integration` gate entry | `blueprint/contract.yaml` | T-016, T-029 | `spec.md § REQ-004` | `make infra-validate` |
| REQ-005 | SDD-C-004 | Claude paths in `consumer_seeded_paths` + `required_files` | `blueprint/contract.yaml` | T-017–T-020, T-013 | `spec.md § REQ-005` | `make infra-validate` |
| REQ-006 | SDD-C-011 | Claude workflow `.tmpl` files | `scripts/templates/consumer/init/.github/workflows/` | T-027–T-028 | template files themselves | `make blueprint-template-smoke` |
| REQ-007 | SDD-C-007, SDD-C-008 | `_validate_consumer_seeded_feature_gates()` | `scripts/bin/blueprint/validate_contract.py` | T-010–T-013, T-026 | `spec.md § REQ-007` | `make infra-validate` |
| REQ-008 | SDD-C-008 | Wired into top-level validator | `scripts/bin/blueprint/validate_contract.py` | T-025 | — | `make infra-validate` |
| NFR-001 | SDD-C-007 | `app_catalog_scaffold_contract` untouched | `scripts/lib/blueprint/init_repo_contract.py` | T-033 (pre-existing suite) | — | — |
| NFR-002 | SDD-C-007 | upgrade engine `consumer-seeded / skip` classification | `scripts/lib/blueprint/upgrade_consumer.py` | T-003 (paths in consumer_seeded) | — | — |
| NFR-003 | SDD-C-008 | 100% coverage on new code | new test file | T-002–T-013 | — | — |
| NFR-004 | SDD-C-012 | quality bundles pass | make targets | T-031–T-032 | — | `make quality-hooks-run`, `make infra-validate` |
| AC-001 | SDD-C-008 | Disabled gate → no workflow files | `seed_consumer_owned_files` + resolver | T-008 | — | manual init dry-run |
| AC-002 | SDD-C-008 | Enabled gate → workflow files present | `seed_consumer_owned_files` + templates | T-009 | — | manual init dry-run |
| AC-003 | SDD-C-007 | Upgrade engine skips `consumer_seeded` | `upgrade_consumer.py` (unchanged) | T-003 | — | `make blueprint-upgrade-consumer-validate` |
| AC-004 | SDD-C-008 | Validator rejects bad gate entries | `_validate_consumer_seeded_feature_gates` | T-010–T-013 | — | `make infra-validate` |
| AC-005 | SDD-C-007 | Second gate works without code change | `resolve_consumer_seeded_feature_gates` generic loop | T-007 | — | — |
| AC-006 | SDD-C-007 | app_catalog tests unchanged | pre-existing test suite | T-033 | — | — |

## Validation Summary
To be completed in Slice 6 after all quality gates pass.
