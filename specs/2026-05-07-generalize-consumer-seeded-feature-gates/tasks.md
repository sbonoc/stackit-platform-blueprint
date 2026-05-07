# Tasks — Generalize Consumer-Seeded Feature Gates

## App Onboarding Minimum Targets (Normative)
No app delivery scope affected; all targets below remain unaffected by this work item.
- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected
- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected
- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected
- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected
- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm ADR status is `approved` in `spec.md`

## Slice 1 — Failing tests (red)
- [ ] T-001 Create `tests/blueprint/test_consumer_seeded_feature_gates.py`
- [ ] T-002 Write `test_resolve_gates_empty_list` (assert returns `[]`)
- [ ] T-003 Write `test_resolve_gate_default_disabled` (no env var → disabled)
- [ ] T-004 Write `test_resolve_gate_env_var_true` (`"true"` → enabled)
- [ ] T-005 Write `test_resolve_gate_env_var_false` (`"false"` → disabled)
- [ ] T-006 Write `test_resolve_gate_env_var_1` (`"1"` → enabled)
- [ ] T-007 Write `test_resolve_gate_multiple_gates` (two gates resolve independently)
- [ ] T-008 Write `test_seed_disabled_gate_prunes_paths` (disabled → files absent after seed)
- [ ] T-009 Write `test_seed_enabled_gate_keeps_paths` (enabled → files present after seed)
- [ ] T-010 Write `test_validate_gate_missing_key_fails`
- [ ] T-011 Write `test_validate_gate_enabled_by_default_true_fails`
- [ ] T-012 Write `test_validate_gate_missing_enable_flag_fails`
- [ ] T-013 Write `test_validate_gate_path_not_in_consumer_seeded_fails`
- [ ] T-014 Confirm all Slice 1 tests fail (red)

## Slice 2 — Contract schema + YAML
- [ ] T-015 Add `CLAUDE_AI_ENABLED` to `spec.toggles` in `blueprint/contract.yaml`
- [ ] T-016 Add `consumer_seeded_feature_gates` list with `claude_ai_integration` gate to `blueprint/contract.yaml`
- [ ] T-017 Add `.github/workflows/claude.yml` to `consumer_seeded_paths` in `blueprint/contract.yaml`
- [ ] T-018 Add `.github/workflows/claude-code-review.yml` to `consumer_seeded_paths` in `blueprint/contract.yaml`
- [ ] T-019 Add `.github/workflows/claude.yml` to `required_files` in `blueprint/contract.yaml`
- [ ] T-020 Add `.github/workflows/claude-code-review.yml` to `required_files` in `blueprint/contract.yaml`

## Slice 3 — Resolver + seeding update (green)
- [ ] T-021 Implement `resolve_consumer_seeded_feature_gates(repo_root)` in `init_repo_contract.py`
- [ ] T-022 Update `seed_consumer_owned_files` to call resolver and prune disabled-gate paths
- [ ] T-023 Confirm T-002–T-009 pass (green)

## Slice 4 — Validator (green)
- [ ] T-024 Implement `_validate_consumer_seeded_feature_gates(repo_root, contract)` in `validate_contract.py`
- [ ] T-025 Wire `_validate_consumer_seeded_feature_gates` into the top-level `_validate_contract` orchestrator
- [ ] T-026 Confirm T-010–T-013 pass (green)

## Slice 5 — Template files + governance test updates
- [ ] T-027 Create `scripts/templates/consumer/init/.github/workflows/claude.yml.tmpl`
- [ ] T-028 Create `scripts/templates/consumer/init/.github/workflows/claude-code-review.yml.tmpl`
- [ ] T-029 Update `contract_refactor_governance_init_cases.py` to assert `consumer_seeded_feature_gates:` in contract
- [ ] T-030 Update `contract_refactor_scripts_cases.py` to assert `resolve_consumer_seeded_feature_gates` in `init_repo_contract.py`

## Slice 6 — Quality gates + publish
- [ ] T-031 Run `make quality-hooks-run` — confirm pass
- [ ] T-032 Run `make infra-validate` — confirm pass
- [ ] T-033 Run full pytest suite — confirm all pre-existing tests pass
- [ ] T-034 Complete `hardening_review.md`
- [ ] T-035 Complete `pr_context.md`
- [ ] T-036 Complete `traceability.md` validation summary
