# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Contract coverage fix (#258, FR-001, AC-001)

### Test (Red)
- [x] T-101 Write pytest regression fixture: fake source tree with 4 unclassified files; assert `audit_source_tree_coverage` returns `uncovered_source_files_count==0`; confirm RED

### Implementation
- [x] T-001 Add `pyproject.toml` and `uv.lock` to `init_managed` in `blueprint/contract.yaml`
- [x] T-002 Add `infra/local/helm/opensearch/values.yaml` and `infra/local/helm/kms/values.yaml` to `conditional_scaffold` in `blueprint/contract.yaml`

### Verify
- [x] T-201 Run `uv run python3 -m pytest tests/infra/ -k "issue_258" -v` → PASS (GREEN)
- [x] T-202 Run `make infra-validate` → PASS
- [x] T-203 Run `make quality-hooks-fast` → no new failures

## Slice 2 — Validate target filtering (#260, FR-002, AC-002)

### Test (Red)
- [ ] T-102 Write pytest regression fixture: contract with `repo_mode=generated-consumer`; assert `blueprint-template-smoke` NOT in resolved `VALIDATION_TARGETS`; confirm RED

### Implementation
- [ ] T-003 In `scripts/lib/blueprint/upgrade_consumer_validate.py`, filter `VALIDATION_TARGETS` to exclude `blueprint-template-smoke` when `contract.repository.repo_mode == generated-consumer-mode-constant`

### Verify
- [ ] T-204 Run `uv run python3 -m pytest tests/infra/ -k "issue_260" -v` → PASS (GREEN)
- [ ] T-205 Run `make quality-hooks-fast` → no new failures

## Slice 3 — Volatile artifact names (#261, FR-003, AC-003)

### Test (Red)
- [ ] T-103 Write pytest regression fixture: two fake artifact dirs differing only in embedded absolute paths in `upgrade_validate.json`; assert `compute_artifact_checksum_divergences` returns empty list; confirm RED

### Implementation
- [ ] T-004 Add `"upgrade_validate.json"` and `"required_files_status.json"` to `_VOLATILE_ARTIFACT_NAMES` frozenset in `scripts/lib/blueprint/upgrade_fresh_env_gate.py`

### Verify
- [ ] T-206 Run `uv run python3 -m pytest tests/infra/ -k "issue_261" -v` → PASS (GREEN)
- [ ] T-207 Run `make quality-hooks-fast` → no new failures

## Slice 4 — Transitive behavioral check (#259, FR-004, AC-004)

### Test (Red)
- [ ] T-104 Write pytest regression fixture (transitive resolution): 3-file source chain; function defined at depth-2; assert `run_behavioral_check` reports 0 failures; confirm RED
- [ ] T-105 Write pytest regression fixture (bare-command suppression): script references `uv` and `validate` as bare tokens; assert 0 failures; confirm RED
- [ ] T-106 Write pytest regression fixture (cycle guard): `a.sh` sources `b.sh` sources `a.sh`; assert check completes without RecursionError; confirm RED (would recurse without guard)

### Implementation
- [ ] T-005 Introduce `_collect_defined_functions_transitive(script_path, root_dir, visited=None)` in `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` using BFS with a visited-paths set
- [ ] T-006 Replace `collect_defined_functions_depth1` call in `run_behavioral_check` with `_collect_defined_functions_transitive`
- [ ] T-007 Introduce bare-command suppression: tokens that do not appear as function definitions anywhere in the full transitive source chain MUST be excluded from the unresolved symbol report when they match known external command patterns

### Verify
- [ ] T-208 Run `uv run python3 -m pytest tests/infra/ -k "issue_259" -v` → PASS (GREEN) — all three fixtures pass
- [ ] T-209 Run `uv run python3 -m pytest tests/infra/` → full suite PASS; no regressions
- [ ] T-210 Run `make quality-hooks-fast` → no new failures

## Accessibility Testing (Normative)
- [x] T-A01 NFR-A11Y-001 compliance scope: N/A — no UI components; this is a Python tooling and YAML contract fix with no user-facing rendering surface.

## Validation and Release Readiness
- [ ] T-301 Run full validation bundle: `make infra-validate && make quality-hooks-run`
- [ ] T-302 Attach evidence checksums to `traceability.md`
- [ ] T-303 Confirm no stale TODOs or dead code in touched scope
- [ ] T-304 Run `make docs-build && make docs-smoke` → PASS
- [ ] T-305 Run `make quality-hardening-review` → PASS

## Publish
- [ ] P-001 Update `hardening_review.md` with findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template and references `pr_context.md`
- [ ] P-004 Close GH issues #258, #259, #260, #261 via `Closes` references in PR description

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: no app delivery workflow affected by this tooling fix
- [x] A-002 `apps-smoke` — N/A
- [x] A-003 `backend-test-unit` — N/A
- [x] A-004 `backend-test-integration` — N/A
- [x] A-005 `backend-test-contracts` — N/A
- [x] A-006 `backend-test-e2e` — N/A
- [x] A-007 `touchpoints-test-unit` — N/A
- [x] A-008 `touchpoints-test-integration` — N/A
- [x] A-009 `touchpoints-test-contracts` — N/A
- [x] A-010 `touchpoints-test-e2e` — N/A
- [x] A-011 `test-unit-all` — N/A
- [x] A-012 `test-integration-all` — N/A
- [x] A-013 `test-contracts-all` — N/A
- [x] A-014 `test-e2e-all-local` — N/A
- [x] A-015 `infra-port-forward-start` — N/A
- [x] A-016 `infra-port-forward-stop` — N/A
- [x] A-017 `infra-port-forward-cleanup` — N/A
