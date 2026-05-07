# Implementation Plan — Generalize Consumer-Seeded Feature Gates

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- `SPEC_READY: true` — gate open.

## Sequenced Delivery Slices

### Slice 1 — Failing tests (red)
**Scope**: `tests/blueprint/test_consumer_seeded_feature_gates.py` (new), `tests/blueprint/test_seed_feature.py` (new)
**Depends on**: none — tests are written against interfaces not yet implemented; all must fail
**Owner**: Software Engineer
**Delivers**: test scaffolding for Slices 3, 4, 5 (no production requirements delivered yet)

Write unit tests that assert the expected behavior of `resolve_consumer_seeded_feature_gates`,
the gate-pruning branch in `seed_consumer_owned_files`, `_validate_consumer_seeded_feature_gates`,
and `seed_feature.py` before any implementation code exists. Tests MUST fail at this point (red).

Tests to write in `test_consumer_seeded_feature_gates.py`:
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

Tests to write in `test_seed_feature.py`:
- `test_seed_feature_writes_gate_paths` — target writes correct files from fetched source
- `test_seed_feature_unknown_gate_exits_nonzero` — unknown gate ID → non-zero exit + diagnostic
- `test_seed_feature_missing_feature_param_exits_nonzero` — missing FEATURE arg → non-zero exit
- `test_seed_feature_idempotent` — second run produces same content, exits zero

**Validation gate**: `pytest tests/blueprint/test_consumer_seeded_feature_gates.py tests/blueprint/test_seed_feature.py` — all tests fail (red confirmed).

### Slice 2 — Contract schema + YAML
**Scope**: `blueprint/contract.yaml`
**Depends on**: none (pure YAML, no code dependency)
**Owner**: Software Engineer
**Delivers**: REQ-001, REQ-004, REQ-005 → partial AC-003

Add `consumer_seeded_feature_gates` list to `blueprint/contract.yaml` with the `claude_ai_integration`
gate. Add both Claude workflow paths to `consumer_seeded_paths` (`ownership_path_classes.consumer_seeded`)
and `required_files`. Add `CLAUDE_AI_ENABLED` toggle entry to `spec.toggles` in contract.

**Validation gate**: `make infra-validate` passes (schema parse succeeds; existing validator does not reject the new YAML key).

### Slice 3 — Resolver + seeding update (green)
**Scope**: `scripts/lib/blueprint/init_repo_contract.py`
**Depends on**: Slice 1 (tests must exist to turn green), Slice 2 (contract YAML must declare the gates list)
**Owner**: Software Engineer
**Delivers**: REQ-002, REQ-003, NFR-001, NFR-002 → AC-001, AC-002, AC-005, AC-006

Implement `resolve_consumer_seeded_feature_gates(repo_root: Path) -> list[tuple[str, bool, list[str]]]`
and update `seed_consumer_owned_files` to call it after the normal `consumer_seeded_paths` seeding
pass. Call `remove_path` for every path belonging to a disabled gate. Turn Slice 1
resolver/seeding tests green.

**Validation gate**: `pytest tests/blueprint/test_consumer_seeded_feature_gates.py::test_resolve_*` and `::test_seed_*` all pass; `make quality-hooks-fast` passes.

### Slice 4 — Validator (green)
**Scope**: `scripts/bin/blueprint/validate_contract.py`
**Depends on**: Slice 1 (validator tests must exist to turn green), Slice 2 (contract YAML must have the gates list to validate)
**Owner**: Software Engineer
**Delivers**: REQ-007, REQ-008 → AC-004

Implement `_validate_consumer_seeded_feature_gates(repo_root, contract)` enforcing all six
structural rules (presence, types, `enabled_by_default: false`, toggle reference, non-empty paths,
paths-in-consumer_seeded). Wire it into the top-level `_validate_contract` orchestrator. Turn
Slice 1 validator tests green.

**Validation gate**: `pytest tests/blueprint/test_consumer_seeded_feature_gates.py::test_validate_*` all pass; `make infra-validate` passes end-to-end.

### Slice 5 — `blueprint-seed-feature` Make target (red → green)
**Scope**: `tests/blueprint/test_seed_feature.py` (new — already created in Slice 1), `scripts/bin/blueprint/seed_feature.py` (new), `make/blueprint.generated.mk` (updated), `tests/blueprint/contract_refactor_scripts_cases.py` (updated)
**Depends on**: Slice 1 (seed_feature tests must exist), Slice 2 (gate definitions used by the script), Slice 3 (resolver function used by seed_feature to resolve gate IDs)
**Owner**: Software Engineer
**Delivers**: REQ-009, REQ-010, REQ-011, NFR-005 → AC-007, AC-008, AC-009

Implement `scripts/bin/blueprint/seed_feature.py`:
- Reads pinned `BLUEPRINT_UPGRADE_REF` from `blueprint/repo.init.env`
- Clones blueprint source at that ref into a tempdir using the same cloning mechanism as `upgrade_consumer.py` — do NOT duplicate cloning logic; extract or reuse the shared helper
- Resolves gate by ID from the fetched source's `consumer_seeded_feature_gates`
- Renders `.tmpl` files from fetched source using the same template renderer as the init engine
- Writes rendered files to the consumer repo
- Exits non-zero with a clear diagnostic when FEATURE arg is missing or gate ID not found
- Second run produces identical output (idempotent)

Add `blueprint-seed-feature` target to `make/blueprint.generated.mk`:
- Namespaced under `blueprint-` prefix
- Self-documenting via `##` comment
- Passes `FEATURE` variable to `seed_feature.py`; exits non-zero if FEATURE is not set

Update `contract_refactor_scripts_cases.py` to assert `seed_feature` appears in the scripts inventory.

**Validation gate**: all four `test_seed_feature_*` tests pass (green); `make quality-hooks-fast` passes.

### Slice 6 — Template files + governance test updates
**Scope**: `scripts/templates/consumer/init/.github/workflows/claude.yml.tmpl` (new), `scripts/templates/consumer/init/.github/workflows/claude-code-review.yml.tmpl` (new), `tests/blueprint/contract_refactor_governance_init_cases.py` (updated), `tests/blueprint/contract_refactor_scripts_cases.py` (updated)
**Depends on**: Slice 2 (contract must declare the gates before governance tests can assert them), Slice 3 (governance tests assert `resolve_consumer_seeded_feature_gates` exists in `init_repo_contract.py`)
**Owner**: Software Engineer
**Delivers**: REQ-006 → AC-003

Create the two Claude workflow `.tmpl` files. Template content MUST be taken from the merged
PR #252 branch (`add-claude-github-actions-1778138840576`) at the point this work item merges.
The files contain no consumer-specific tokens; the `{{...}}` substitution pass runs on them but
produces no changes.

Update governance tests:
- `contract_refactor_governance_init_cases.py`: assert `consumer_seeded_feature_gates:` key present in contract
- `contract_refactor_scripts_cases.py`: assert `resolve_consumer_seeded_feature_gates` appears in `init_repo_contract.py`

**Validation gate**: updated governance tests pass; `make infra-validate` passes.

### Slice 7 — Quality gates + publish
**Scope**: `pr_context.md`, `hardening_review.md`, `traceability.md` (validation summary)
**Depends on**: all previous slices complete and passing
**Owner**: Software Engineer
**Delivers**: NFR-003, NFR-004

Run `make quality-hooks-run` and `make infra-validate`. Fix any violations. Run the full
pytest suite. Complete `pr_context.md` and `hardening_review.md`. Fill in the Validation Summary
section in `traceability.md`.

**Validation gate**: `make quality-hooks-run` passes; `make infra-validate` passes; full pytest suite passes with all new tests green and zero regressions.

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

- **Unit (Slices 1, 3, 4, 5):** pytest for resolver, pruning, validator, and seed_feature; 100% coverage on new code (NFR-003)
- **Contract refactor (Slice 6):** existing governance tests extended to cover new contract structure
- **Integration (Slices 4, 7):** `make infra-validate` runs full `validate_contract.py` against the repo; verifies REQ-007+REQ-008 end-to-end

## Risk and Rollback

- **Risk:** Existing `app_catalog_scaffold_contract` tests or governance refactor tests break.
  Mitigation: Run full test suite after each slice; app_catalog code is untouched (NFR-001).
- **Risk:** Claude workflow `.tmpl` files drift from the PR #252 branch.
  Mitigation: Template content taken directly from the merged PR #252 branch at implementation time.
- **Risk:** `seed_feature.py` cloning logic diverges from the upgrade engine's cloning approach.
  Mitigation: Extract shared cloning helper from `upgrade_consumer.py` or reuse it directly; do not duplicate cloning logic.
- **Rollback:** Revert YAML additions to `blueprint/contract.yaml`, remove new functions and `seed_feature.py`.
  Existing consumers are unaffected (upgrade engine never applies `consumer_seeded` paths — NFR-002).
