# Tasks — Generalize Consumer-Seeded Feature Gates

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm ADR status is `approved` in `spec.md`

## Slice 1 — Failing tests (red)
- [x] T-001 Create `tests/blueprint/test_consumer_seeded_feature_gates.py`
- [x] T-002 Write `test_resolve_gates_empty_list` (assert returns `[]`)
- [x] T-003 Write `test_resolve_gate_default_disabled` (no env var → disabled)
- [x] T-004 Write `test_resolve_gate_env_var_true` (`"true"` → enabled)
- [x] T-005 Write `test_resolve_gate_env_var_false` (`"false"` → disabled)
- [x] T-006 Write `test_resolve_gate_env_var_1` (`"1"` → enabled)
- [x] T-007 Write `test_resolve_gate_multiple_gates` (two gates resolve independently)
- [x] T-008 Write `test_seed_disabled_gate_prunes_paths` (disabled → files absent after seed)
- [x] T-009 Write `test_seed_enabled_gate_keeps_paths` (enabled → files present after seed)
- [x] T-010 Write `test_validate_gate_missing_key_fails`
- [x] T-011 Write `test_validate_gate_enabled_by_default_true_fails`
- [x] T-012 Write `test_validate_gate_missing_enable_flag_fails`
- [x] T-013 Write `test_validate_gate_path_not_in_consumer_seeded_fails`
- [x] T-014 Confirm all Slice 1 tests fail (red)

## Slice 2 — Contract schema + YAML
- [x] T-015 Add `CLAUDE_AI_ENABLED` to `spec.toggles` in `blueprint/contract.yaml`
- [x] T-016 Add `consumer_seeded_feature_gates` list with `claude_ai_integration` gate to `blueprint/contract.yaml`
- [x] T-017 Add `.github/workflows/claude.yml` to `consumer_seeded_paths` in `blueprint/contract.yaml`
- [x] T-018 Add `.github/workflows/claude-code-review.yml` to `consumer_seeded_paths` in `blueprint/contract.yaml`
- [x] T-019 Add `.github/workflows/claude.yml` to `required_files` in `blueprint/contract.yaml`
- [x] T-020 Add `.github/workflows/claude-code-review.yml` to `required_files` in `blueprint/contract.yaml`

## Slice 3 — Resolver + seeding update (green)
- [x] T-021 Implement `resolve_consumer_seeded_feature_gates(repo_root)` in `init_repo_contract.py`
- [x] T-022 Update `seed_consumer_owned_files` to call resolver and prune disabled-gate paths
- [x] T-023 Confirm T-002–T-009 pass (green)

## Slice 4 — Validator (green)
- [ ] T-024 Implement `_validate_consumer_seeded_feature_gates(repo_root, contract)` in `validate_contract.py`
- [ ] T-025 Wire `_validate_consumer_seeded_feature_gates` into the top-level `_validate_contract` orchestrator
- [ ] T-026 Confirm T-010–T-013 pass (green)

## Slice 5 — `blueprint-seed-feature` Make target (red → green)
- [x] T-027 Create `tests/blueprint/test_seed_feature.py`
- [x] T-028 Write `test_seed_feature_writes_gate_paths` (target writes correct files from fetched source)
- [x] T-029 Write `test_seed_feature_unknown_gate_exits_nonzero` (unknown gate ID → non-zero exit + diagnostic)
- [x] T-030 Write `test_seed_feature_missing_feature_param_exits_nonzero` (missing FEATURE → non-zero exit)
- [x] T-031 Write `test_seed_feature_idempotent` (second run produces same content, exits zero)
- [x] T-032 Confirm T-028–T-031 fail (red)
- [ ] T-033 Implement `scripts/bin/blueprint/seed_feature.py` (reads pinned ref, fetches blueprint source, resolves gate, renders templates, writes to consumer repo)
- [ ] T-034 Add `blueprint-seed-feature` target to `make/blueprint.generated.mk`
- [ ] T-035 Update `contract_refactor_scripts_cases.py` to assert `seed_feature` in scripts
- [ ] T-036 Confirm T-028–T-031 pass (green)

## Slice 6 — Template files + governance test updates
- [ ] T-037 Create `scripts/templates/consumer/init/.github/workflows/claude.yml.tmpl`
- [ ] T-038 Create `scripts/templates/consumer/init/.github/workflows/claude-code-review.yml.tmpl`
- [ ] T-039 Update `contract_refactor_governance_init_cases.py` to assert `consumer_seeded_feature_gates:` in contract
- [ ] T-040 Update `contract_refactor_scripts_cases.py` to assert `resolve_consumer_seeded_feature_gates` in `init_repo_contract.py`

## Slice 7 — Quality gates + publish
- [ ] T-041 Run `make quality-hooks-run` — confirm pass
- [ ] T-042 Run `make infra-validate` — confirm pass
- [ ] T-043 Run full pytest suite — confirm all pre-existing tests pass
- [ ] T-044 Complete `hardening_review.md`
- [ ] T-045 Complete `pr_context.md`
- [ ] T-046 Complete `traceability.md` validation summary
