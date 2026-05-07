# Implementation Plan — Generalize Consumer-Seeded Feature Gates

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Sequenced Delivery Slices

### Slice 1 — Failing tests (red)
Write unit tests that assert the expected behavior of `resolve_consumer_seeded_feature_gates` and
the gate-pruning branch in `seed_consumer_owned_files` before any implementation code exists.
Tests MUST fail at this point (red).

Files touched:
- `tests/blueprint/test_consumer_seeded_feature_gates.py` (new)

Tests to write:
- `test_resolve_gates_empty_list` — no gates → returns empty list
- `test_resolve_gate_default_disabled` — gate with `enabled_by_default: false`, env var absent → `(id, False, paths)`
- `test_resolve_gate_env_var_true` — env var set to `"true"` → `(id, True, paths)`
- `test_resolve_gate_env_var_false` — env var set to `"false"` → `(id, False, paths)`
- `test_resolve_gate_env_var_1` — env var set to `"1"` → enabled
- `test_resolve_gate_multiple_gates` — two independent gates resolve independently
- `test_seed_disabled_gate_prunes_paths` — seeding with disabled gate removes gate paths from repo
- `test_seed_enabled_gate_keeps_paths` — seeding with enabled gate leaves gate paths present
- `test_validate_gate_missing_key_fails` — missing `consumer_seeded_feature_gates` key → validation error
- `test_validate_gate_enabled_by_default_true_fails` — `enabled_by_default: true` → error
- `test_validate_gate_missing_enable_flag_fails` — missing `enable_flag` → error
- `test_validate_gate_path_not_in_consumer_seeded_fails` — path not in `consumer_seeded_paths` → error

### Slice 2 — Contract schema + YAML
Add `consumer_seeded_feature_gates` list to `blueprint/contract.yaml` with the `claude_ai_integration`
gate. Add both Claude workflow paths to `consumer_seeded_paths` and `required_files`.
Add `CLAUDE_AI_ENABLED` toggle entry to `spec.toggles` in contract.

Files touched:
- `blueprint/contract.yaml`

### Slice 3 — Resolver + seeding update (green)
Implement `resolve_consumer_seeded_feature_gates` in `init_repo_contract.py` and update
`seed_consumer_owned_files` to call it. Turn Slice 1 unit tests green.

Files touched:
- `scripts/lib/blueprint/init_repo_contract.py`

### Slice 4 — Validator (green)
Implement `_validate_consumer_seeded_feature_gates` in `validate_contract.py` and wire it into
the top-level validator. Turn validation unit tests green.

Files touched:
- `scripts/bin/blueprint/validate_contract.py`

### Slice 5 — Template files + contract refactor test update
Create the two Claude workflow `.tmpl` files. Update any contract-refactor governance tests that
assert the structure of `blueprint/contract.yaml` or `init_repo_contract.py`.

Files touched:
- `scripts/templates/consumer/init/.github/workflows/claude.yml.tmpl` (new)
- `scripts/templates/consumer/init/.github/workflows/claude-code-review.yml.tmpl` (new)
- `tests/blueprint/contract_refactor_governance_init_cases.py` (update)
- `tests/blueprint/contract_refactor_scripts_cases.py` (update)

### Slice 6 — Quality gates + publish
Run `make quality-hooks-run` and `make infra-validate`. Fix any violations.
Complete `pr_context.md` and `hardening_review.md`.

## App Onboarding Contract (Normative)
- Required minimum make targets (all unaffected by this work item):
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
- Notes: no app delivery scope affected; all targets above remain functional

## Validation Strategy

- **Unit (Slice 1, 3, 4):** pytest for resolver, pruning, and validator; 100% coverage on new code
- **Contract refactor (Slice 5):** existing governance tests extended to cover new contract structure
- **Integration (Slice 6):** `make infra-validate` runs full `validate_contract.py` against the repo

## Risk and Rollback

- **Risk:** Existing `app_catalog_scaffold_contract` tests or governance refactor tests break.
  Mitigation: Run full test suite after each slice; app_catalog code is untouched.
- **Risk:** Claude workflow `.tmpl` files drift from the PR #252 branch.
  Mitigation: Template content taken directly from the merged PR #252 branch at implementation time.
- **Rollback:** Revert the YAML additions to `blueprint/contract.yaml` and remove the new functions.
  Existing consumers are unaffected (upgrade engine never applies `consumer_seeded` paths).
