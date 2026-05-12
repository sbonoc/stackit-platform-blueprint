# PR Context

## Summary

- **Work item:** `specs/2026-05-12-issue-258-259-260-261-v110-engine-hotfix`
- **Objective:** Fix 4 independent defects in the v1.10.0 upgrade engine that collectively
  block every consumer upgrade: contract coverage gap, validate-target contamination,
  volatile-artifact false positives, and transitive source-resolution cap in the shell
  behavioral check.
- **Scope boundaries:** Python tooling under `scripts/lib/blueprint/` and `blueprint/contract.yaml`
  + its bootstrap template.  No app delivery, no UI, no API changes.

## Requirement Coverage

- **Requirement IDs covered:** FR-001, FR-002, FR-003, FR-004
- **Acceptance criteria covered:** AC-001, AC-002, AC-003, AC-004
- **Non-functional requirements:** NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- **Contract surfaces changed:**
  - `blueprint/contract.yaml` — `init_managed` (+2 entries), `conditional_scaffold` (+2 entries),
    `optional_modules.opensearch` (+`helm_path`, +`paths_required_when_enabled[helm_path]`),
    `optional_modules.kms` (+`helm_path`, +`paths_required_when_enabled[helm_path]`)
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — same changes mirrored
    (bootstrap template drift fix)

## Key Reviewer Files

**Primary files to review first:**
1. `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_collect_defined_functions_transitive` (BFS + cycle guard), `_EXCLUDED_TOKENS` additions
2. `scripts/lib/blueprint/upgrade_consumer_validate.py` — `_get_effective_validation_targets`, `_GENERATED_CONSUMER_SKIP_TARGETS`
3. `blueprint/contract.yaml` — new `init_managed` and `conditional_scaffold` entries, updated optional module definitions

**Supporting files:**
4. `scripts/lib/blueprint/upgrade_fresh_env_gate.py` — `_VOLATILE_ARTIFACT_NAMES` additions
5. `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — template sync
6. `scripts/lib/quality/test_pyramid_contract.json` — 4 new test file registrations

**Regression tests (4 new files, ~30 test methods):**
- `tests/infra/test_upgrade_contract_coverage_issue_258.py`
- `tests/infra/test_upgrade_consumer_validate_issue_260.py`
- `tests/infra/test_upgrade_fresh_env_gate_issue_261.py`
- `tests/infra/test_upgrade_shell_behavioral_check_issue_259.py`

**Existing test updated:**
- `tests/blueprint/test_upgrade_consumer.py` — 2 assertions updated to account for generated-consumer target filter (7 targets instead of 8)

## Validation Evidence

**Commands executed (2026-05-12):**

| Command | Result |
|---|---|
| `uv run python3 -m pytest tests/infra/ -k "issue_258" -v` | PASS |
| `uv run python3 -m pytest tests/infra/ -k "issue_260" -v` | PASS |
| `uv run python3 -m pytest tests/infra/ -k "issue_261" -v` | PASS |
| `uv run python3 -m pytest tests/infra/ -k "issue_259" -v` | PASS |
| `uv run python3 -m pytest tests/infra/` | PASS (324 tests, 0 failures) |
| `make infra-validate` | PASS |
| `make quality-hooks-fast` | PASS (no new failures) |
| `make quality-hooks-run` | PASS except pre-existing `blueprint-template-smoke` bash3/bash4 issue |
| `make docs-build` | PASS |
| `make docs-smoke` | PASS |
| `make quality-hardening-review` | PASS |

**Pre-existing known failure:**
`blueprint-template-smoke` fails with `declare: -A: invalid option` (bash 3 vs bash 4
associative array syntax in `scripts/bin/blueprint/prune_codex_skills.sh:53`) on macOS.
Verified present on `main` branch with no local changes.  Not introduced by this PR.

**File checksums (SHA-256):** See `traceability.md` § File Checksums.

## Risk and Rollback

**Main risks:**
1. **Transitive BFS depth increase:** The BFS resolver now walks the full source chain
   instead of depth-1.  Worst case: deeply nested source chains slow down the behavioral
   check for large files.  Mitigated by the frozenset visited guard (no revisits) and the
   fact that the existing source chain depth in all consumer repos is ≤ 3.
2. **`_get_effective_validation_targets` mode check:** Relies on
   `contract.repository.repo_mode == contract.repository.consumer_init.mode_to`.  If the
   contract schema changes the field name, the filter silently falls through to the full
   target list (safe degradation — no targets are skipped unintentionally).

**Rollback strategy:**
1. Revert PR — all changes are backward-compatible YAML and Python additions; no database
   migrations, no infrastructure changes.
2. Consumers who added `extra_excluded_tokens: [uv, validate]` workarounds retain those
   entries harmlessly after rollback (they become redundant once the fix is merged, but
   cause no harm if the fix is reverted).

## Deferred Proposals

- Full POSIX shell parser to replace grep-based `_FUNC_DEF_EXTRACT` heuristic.
- Automated post-upgrade warning for consumers who still carry `extra_excluded_tokens` workarounds.

See `hardening_review.md` § Proposals Only for details.
