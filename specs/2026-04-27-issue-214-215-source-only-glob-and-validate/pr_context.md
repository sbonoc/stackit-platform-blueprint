# PR Context

## Summary
- Work item: 2026-04-27-issue-214-215-source-only-glob-and-validate
- Objective: Fix two bugs reported by dhe-marketplace during v1.8.0 upgrade: (1) `audit_source_tree_coverage` in `upgrade_consumer.py` does not count files matched by `source_artifact_prune_globs_on_init` as covered, causing false-positive `uncovered_source_files_count > 0` failures that block every consumer using prune-globs (issue #214); (2) `_validate_absent_files` in `validate_contract.py` uses `exists()` instead of `is_file()`, so directory-prefix `source_only` entries trigger false absent-file errors, and glob patterns in `source_only` are unsupported (issue #215).
- Scope boundaries: Two surgical function patches in Python blueprint tooling — `scripts/lib/blueprint/upgrade_consumer.py::audit_source_tree_coverage` and `scripts/bin/blueprint/validate_contract.py::_validate_absent_files`; new test file `tests/blueprint/test_validate_contract.py` (5 regression tests); `test_pyramid_contract.json` registration; `docs/blueprint/architecture/execution_model.md` documentation update. No consumer-facing Make targets, no runtime changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001 (prune-glob files not in uncovered list), AC-002 (directory entry no longer triggers absent error), AC-003 (glob entry matches file → error emitted), AC-004 (glob entry with no matching file → no error), AC-005 (exact-file entry with file present → error, backward compat)
- Contract surfaces changed: `audit_source_tree_coverage` gains optional `prune_glob_patterns: frozenset[str]` parameter (default: empty, backward-compatible); `_validate_absent_files` now classifies entries as glob/directory vs. exact-file and uses `fnmatch` against the consumer file list for glob entries.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_consumer.py` — `audit_source_tree_coverage`: new `prune_glob_patterns` param; prune-glob coverage resolved via `fnmatch.fnmatch` against `candidate_rels` before computing uncovered list; call site updated to pass prune-glob list from contract
  - `scripts/bin/blueprint/validate_contract.py` — `_validate_absent_files`: entry classifier (contains `*` → glob branch, otherwise `is_file()` branch); lazy consumer file list built once per call; `fnmatch` used to match glob entries against consumer files
  - `tests/blueprint/test_validate_contract.py` — 5 regression tests covering AC-001–AC-005: confirmed red before fix, green after; `TestValidateAbsentFiles` class
- High-risk files: none — changes are limited to the two function bodies listed above; no cross-module imports introduced; no subprocess or external calls; all glob resolution is bounded to pre-enumerated repo file lists

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/blueprint/test_validate_contract.py -v` (5 new regression tests, all red before fix); `python3 -m pytest tests/blueprint/ -q` (full suite); `make quality-sdd-check`; `make quality-hooks-run`; `make quality-hardening-review`
- Result summary: 5/5 new regression tests green after fix; full suite 89 passed; `quality-sdd-check` clean; `quality-hooks-run` clean; `quality-hardening-review` clean. Pre-existing failures in other test files are out of scope and confirmed on main.
- Artifact references: `traceability.md` (validation summary populated); `docs/blueprint/architecture/execution_model.md` updated with source_only entry format documentation.

## Risk and Rollback
- Main risks: `fnmatch` does not support `**` recursive glob patterns — an entry like `docs/**/*.md` in `source_only` would silently match nothing rather than failing; documented as a known limitation (see Deferred Proposals). Blast radius is bounded to the two patched functions; no other caller code changed.
- Rollback strategy: revert `scripts/lib/blueprint/upgrade_consumer.py` and `scripts/bin/blueprint/validate_contract.py` to pre-PR state; consumers with prune-glob contracts must re-apply per-file source_only workarounds; `infra-validate` directory-prefix errors will reappear but will not corrupt data. No DB migrations, no API contract changes, no consumer migrations required.

## Deferred Proposals
- Proposal 1 (not implemented): Add a validator warning (or error) when a `source_only` entry contains `**`, because `fnmatch` does not support recursive glob patterns and such an entry would silently match nothing. Deferred — no current consumer uses `**` in `source_only`; addressing it in a follow-up keeps this fix surgical. Issue filed: https://github.com/sbonoc/stackit-platform-blueprint/issues/229
