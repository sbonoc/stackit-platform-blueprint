# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1 (issue #214): `audit_source_tree_coverage` in `upgrade_consumer.py` did not accept a `prune_glob_patterns` parameter; files matching `source_artifact_prune_globs_on_init` (e.g. `docs/blueprint/architecture/decisions/ADR-*.md`) counted as uncovered and incremented `uncovered_source_files_count`, blocking all consumers whose contracts declare prune-globs. Fixed by adding `prune_glob_patterns: frozenset[str]` parameter and resolving matching paths via `fnmatch.fnmatch` against `candidate_rels` before computing the uncovered list.
- Finding 2 (issue #215): `_validate_absent_files` in `validate_contract.py` used `Path.exists()` for all `source_only` entries; directories (e.g. `specs/`) returned `True` from `exists()` and triggered false absent-file errors. Glob entries (entries containing `*`) were evaluated as literal file paths and always reported as absent regardless of matching files. Fixed by classifying entries: glob/directory entries use `fnmatch` against the pre-enumerated consumer file list; plain file entries use `is_file()`.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new structured metrics or traces added; the existing `audit_source_tree_coverage` `WARNING` stderr line for genuinely uncovered files is preserved (NFR-OBS-001).
- Operational diagnostics updates: none — the fix removes false-positive diagnostic noise (uncovered-source-file WARNINGs for prune-glob files) without removing legitimate warnings for truly uncovered files.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: both patches are single-responsibility surgical fixes inside existing helper functions; no new abstractions, no new modules, no cross-layer imports. Entry classification logic is inline in `_validate_absent_files` following the existing helper's style. `fnmatch` is a stdlib module; no external dependencies introduced.
- Test-automation and pyramid checks: 5 unit regression tests added in `tests/blueprint/test_validate_contract.py` covering AC-001–AC-005 (directory entry, glob match, glob no-match, exact-file backward compat, prune-glob coverage); all 5 confirmed red before fix and green after; file classified as `unit` scope in `test_pyramid_contract.json`. Positive-path assertions included (AC-001 and AC-004).
- Documentation/diagram/CI/skill consistency checks: `docs/blueprint/architecture/execution_model.md` updated to document the three `source_only` entry forms and the prune-glob coverage rule; traceability.md FR-001/FR-002/FR-003 doc evidence refs corrected; no Mermaid diagrams or CI workflow changes required (tooling-only fix).

## Proposals Only (Not Implemented)
- Proposal 1: add a validator warning (or hard error) when a `source_only` entry contains `**`, since `fnmatch` does not support recursive globs and such an entry would silently match nothing. Not implemented because no current consumer uses `**` in `source_only`; a targeted follow-up keeps this fix minimal.
