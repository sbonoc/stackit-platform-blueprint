# PR Context

## Summary

- Work item: `specs/2026-05-12-issue-258-259-260-261-v110-engine-hotfix`
- Objective: Fix 5 defects in the v1.10.0 upgrade engine — contract coverage gap (#258), transitive behavioral check false positives (#259), validate-target contamination (#260), volatile-artifact fresh-env divergences (#261), and stale extra_excluded_tokens warnings (implemented from deferred proposal) — that collectively block every consumer upgrade.
- Scope boundaries: Python tooling under `scripts/lib/blueprint/` and `blueprint/contract.yaml` + its bootstrap template. No app delivery, no UI, no API changes.

## Requirement Coverage

- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Non-functional requirements: NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Contract surfaces changed:
  - `blueprint/contract.yaml` — `init_managed` (+2 entries), `conditional_scaffold` (+2 entries), `optional_modules.opensearch` (+`helm_path`, +`paths_required_when_enabled[helm_path]`), `optional_modules.kms` (+`helm_path`, +`paths_required_when_enabled[helm_path]`)
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — same changes mirrored

## Key Reviewer Files

- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — `_collect_defined_functions_transitive` (BFS + cycle guard), `_EXCLUDED_TOKENS` additions (`uv`, `validate`), stale-token WARNING logic
  - `scripts/lib/blueprint/upgrade_consumer_validate.py` — `_get_effective_validation_targets`, `_GENERATED_CONSUMER_SKIP_TARGETS`
  - `blueprint/contract.yaml` — new `init_managed` and `conditional_scaffold` entries, updated optional module definitions
- Supporting files:
  - `scripts/lib/blueprint/upgrade_fresh_env_gate.py` — `_VOLATILE_ARTIFACT_NAMES` additions
  - `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` — template sync
  - `scripts/lib/quality/test_pyramid_contract.json` — 5 new test file registrations
- Regression tests (5 new files, ~36 test methods):
  - `tests/infra/test_upgrade_contract_coverage_issue_258.py`
  - `tests/infra/test_upgrade_consumer_validate_issue_260.py`
  - `tests/infra/test_upgrade_fresh_env_gate_issue_261.py`
  - `tests/infra/test_upgrade_shell_behavioral_check_issue_259.py`
  - `tests/infra/test_upgrade_shell_behavioral_check_stale_tokens.py`
- Existing test updated: `tests/blueprint/test_upgrade_consumer.py` — 2 assertions updated for generated-consumer target filter (7 targets instead of 8)

## Validation Evidence

- Required commands executed: `uv run python3 -m pytest tests/infra/`, `make infra-validate`, `make quality-hooks-fast`, `make quality-hooks-run`, `make docs-build`, `make docs-smoke`, `make quality-hardening-review`
- Result summary: All per-slice pytest runs PASS; full suite (330 tests) PASS; `make infra-validate` PASS; `make quality-hooks-fast` PASS; `make docs-build`/`docs-smoke` PASS; `make quality-hardening-review` PASS. `blueprint-template-smoke` fails in `quality-hooks-run` with pre-existing bash 3 vs bash 4 `declare -A` incompatibility (`prune_codex_skills.sh:53`) — verified present on `main` with no local changes; not introduced by this PR.
- Artifact references: File checksums in `traceability.md` § File Checksums; ADR at `docs/blueprint/architecture/decisions/ADR-issue-258-259-260-261-v110-engine-hotfix.md`.

## Risk and Rollback

- Main risks: (1) Transitive BFS depth increase — worst case: deep source chains slow behavioral check; mitigated by frozenset visited guard and ≤3 actual depth in all consumer repos. (2) `_get_effective_validation_targets` mode check relies on `contract.repository.repo_mode == contract.repository.consumer_init.mode_to` — schema rename would cause silent fall-through to full target list (safe degradation).
- Rollback strategy: Revert PR — all changes are backward-compatible YAML and Python additions; no database migrations, no infrastructure changes. Consumers who added `extra_excluded_tokens: [uv, validate]` workarounds retain them harmlessly after rollback (they become redundant once the fix is merged, but cause no harm if reverted).

## Deferred Proposals

- Proposal 1 (not implemented): Full POSIX shell parser — replace grep-based `_FUNC_DEF_EXTRACT` heuristic with `shellcheck --format=json` or similar. Parked — trigger: on-scope: blueprint. See `hardening_review.md` § Proposals Only.
