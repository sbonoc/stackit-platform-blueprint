# Traceability Matrix — Generalize Consumer-Seeded Feature Gates

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | SDD-C-004, SDD-C-007 | `consumer_seeded_feature_gates` YAML schema | `blueprint/contract.yaml` | T-016, T-039 | `architecture.md § Module Structure`, `spec.md § Contract Changes` | `make infra-validate` |
| REQ-002 | SDD-C-007, SDD-C-008 | `resolve_consumer_seeded_feature_gates()` | `scripts/lib/blueprint/init_repo_contract.py` | T-002–T-007, T-023, T-040 | `architecture.md § Flow` | `make infra-validate` |
| REQ-003 | SDD-C-007, SDD-C-008 | `seed_consumer_owned_files()` prune step | `scripts/lib/blueprint/init_repo_contract.py` | T-008–T-009, T-023 | `architecture.md § Flow` | `make infra-validate` |
| REQ-004 | SDD-C-004 | `claude_ai_integration` gate entry | `blueprint/contract.yaml` | T-016, T-039 | `spec.md § REQ-004` | `make infra-validate` |
| REQ-005 | SDD-C-004 | Claude paths in `consumer_seeded_paths` + `required_files` | `blueprint/contract.yaml` | T-017–T-020, T-013 | `spec.md § REQ-005` | `make infra-validate` |
| REQ-006 | SDD-C-011 | Claude workflow `.tmpl` files | `scripts/templates/consumer/init/.github/workflows/` | T-037–T-038 | template files themselves | `make blueprint-template-smoke` |
| REQ-007 | SDD-C-007, SDD-C-008 | `_validate_consumer_seeded_feature_gates()` | `scripts/bin/blueprint/validate_contract.py` | T-010–T-013, T-026 | `spec.md § REQ-007` | `make infra-validate` |
| REQ-008 | SDD-C-008 | Wired into top-level validator | `scripts/bin/blueprint/validate_contract.py` | T-025 | — | `make infra-validate` |
| NFR-001 | SDD-C-007 | `app_catalog_scaffold_contract` untouched | `scripts/lib/blueprint/init_repo_contract.py` | T-043 (pre-existing suite) | — | — |
| NFR-002 | SDD-C-007 | upgrade engine `consumer-seeded / skip` classification | `scripts/lib/blueprint/upgrade_consumer.py` | T-017–T-018 (paths added to consumer_seeded list) | — | `make blueprint-upgrade-consumer-validate` |
| NFR-003 | SDD-C-008 | 100% coverage on new code | new test file | T-002–T-013 | — | — |
| NFR-004 | SDD-C-012 | quality bundles pass | make targets | T-041–T-042 | — | `make quality-hooks-run`, `make infra-validate` |
| AC-001 | SDD-C-008 | Disabled gate → no workflow files | `seed_consumer_owned_files` + resolver | T-008 | — | manual init dry-run |
| AC-002 | SDD-C-008 | Enabled gate → workflow files present | `seed_consumer_owned_files` + templates | T-009 | — | manual init dry-run |
| AC-003 | SDD-C-007 | Upgrade engine classifies paths as `consumer-seeded / skip` | `upgrade_consumer.py` (unchanged) | T-017–T-018 (paths added to consumer_seeded list) | — | `make blueprint-upgrade-consumer-validate` |
| AC-004 | SDD-C-008 | Validator rejects bad gate entries | `_validate_consumer_seeded_feature_gates` | T-010–T-013 | — | `make infra-validate` |
| AC-005 | SDD-C-007 | Second gate works without code change | `resolve_consumer_seeded_feature_gates` generic loop | T-007 | — | — |
| AC-006 | SDD-C-007 | app_catalog tests unchanged | pre-existing test suite | T-043 | — | — |
| REQ-009 | SDD-C-007, SDD-C-008 | `blueprint-seed-feature` Make target + `seed_feature.py` | `scripts/bin/blueprint/seed_feature.py`, `make/blueprint.generated.mk` | T-028, T-035, T-036 | `architecture.md § Flow`, `spec.md § REQ-009` | consumer manual run |
| REQ-010 | SDD-C-008 | Exit non-zero + diagnostic on bad FEATURE | `scripts/bin/blueprint/seed_feature.py` | T-029, T-030, T-036 | `spec.md § REQ-010` | — |
| REQ-011 | SDD-C-008 | Idempotent second run | `scripts/bin/blueprint/seed_feature.py` | T-031, T-036 | `spec.md § REQ-011` | — |
| NFR-005 | SDD-C-007 | Pinned ref only — no ref override | `scripts/bin/blueprint/seed_feature.py` | T-028, T-033 (interface has no ref param) | `spec.md § NFR-005`, `spec.md § Explicit Exclusions` | — |
| AC-007 | SDD-C-008 | seed-feature writes gate files, no other files touched | `seed_feature.py` + Make target | T-028, T-036 | — | consumer manual run |
| AC-008 | SDD-C-008 | Unknown gate exits non-zero + diagnostic | `seed_feature.py` | T-029, T-036 | — | — |
| AC-009 | SDD-C-008 | Idempotent — second run identical, exits zero | `seed_feature.py` | T-031, T-036 | — | — |
| REQ-012 | SDD-C-007, SDD-C-008 | `feature_gate_status.py` + `blueprint-feature-gate-status` target | `scripts/bin/blueprint/feature_gate_status.py`, `make/blueprint.generated.mk` | T-048, T-054, T-060 | `spec.md § REQ-012` | consumer manual run |
| REQ-013 | SDD-C-008 | Backlog entry format and idempotent upsert | `scripts/bin/blueprint/feature_gate_status.py` | T-049, T-050, T-051, T-060 | `spec.md § REQ-013` | — |
| REQ-014 | SDD-C-007 | Wire into `upgrade_consumer_postcheck.sh` (non-blocking) | `scripts/bin/blueprint/upgrade_consumer_postcheck.sh` | T-057 | `spec.md § REQ-014` | `make blueprint-upgrade-consumer-postcheck` |
| REQ-015 | SDD-C-007 | Update blueprint-consumer-upgrade skill | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | T-058 | skill file itself | — |
| AC-010 | SDD-C-008 | blueprint-feature-gate-status writes backlog entries for unadopted gates, exits 0 | `feature_gate_status.py` | T-048, T-052 | — | — |
| AC-011 | SDD-C-008 | Idempotent — no duplicate backlog entries | `feature_gate_status.py` | T-049 | — | — |
| AC-012 | SDD-C-008 | Adopted gate → entry marked done, no new open entry | `feature_gate_status.py` | T-050, T-051 | — | — |
| AC-013 | SDD-C-007 | postcheck calls gate status as non-blocking step | `upgrade_consumer_postcheck.sh` | T-057 | — | `make blueprint-upgrade-consumer-postcheck` |

## Validation Summary
- All task items T-001–T-060 confirmed checked in `tasks.md`
- `make infra-validate` — PASS (contract validation, makefile render, bootstrap template drift check)
- `make quality-hooks-run` — PASS on all hooks except pre-existing `infra-contract-test-fast` / `test_template_smoke_assertions.py` failure (`ModuleNotFoundError: No module named 'yaml'` on homebrew Python 3.14.4). Pre-existing constraint confirmed present on commit `1d7b98e` before Slice 8 changes.
- Full pytest suite: Slices 1–4 (22 tests) green with homebrew Python; Slices 5+8 (test_seed_feature + test_feature_gate_status, 10 tests) green with pyenv Python 3.14.3 (PyYAML available)
- Slice 8 tests T-048–T-052 confirmed red before implementation, green after
- Repository-wide finding fixed: governance init test fixtures patched to include `infra/gitops/platform/base/apps/*.yaml.tmpl` templates (pre-existing gap from commit `0e1cecc`)
- Traceability coverage: all REQ/NFR/AC rows have at least one test column entry and one implementation path; no dangling requirements
