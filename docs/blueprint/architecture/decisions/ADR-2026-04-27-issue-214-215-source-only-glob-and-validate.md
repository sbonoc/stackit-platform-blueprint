# ADR: source_only Glob and Directory-Prefix Support in Audit Coverage and Contract Validation

- **Status:** proposed
- **ADR technical decision sign-off:** pending
- **Date:** 2026-04-27
- **Issues:** #214, #215
- **Work item:** `specs/2026-04-27-issue-214-215-source-only-glob-and-validate/`

## Context

Two complementary bugs were discovered by the dhe-marketplace consumer during their v1.7.0 → v1.8.0 blueprint upgrade.

**Bug #214 — audit_source_tree_coverage ignores source_artifact_prune_globs_on_init**

`audit_source_tree_coverage` builds `all_coverage_roots` from `required_files | source_only | init_managed | conditional | managed_roots | feature_gated`. It does **not** include files matching `consumer_init.source_artifact_prune_globs_on_init`. These files (e.g. blueprint-internal ADRs under `docs/blueprint/architecture/decisions/ADR-*.md`) are intentionally pruned at consumer init and never delivered to the consumer — yet they appear as uncovered source files, causing `uncovered_source_files_count > 0` and blocking `upgrade-plan`.

**Bug #215 — _validate_absent_files uses exists() instead of is_file()**

`_validate_absent_files` checks `(repo_root / path).exists()` for each `source_only` entry. `Path.exists()` returns `True` for both files and directories. If a consumer adds a directory-prefix entry (e.g. `docs/blueprint/architecture/decisions/`) to cover all prune-globbed ADRs with a single line — the natural ergonomic fix for #214 — the validator rejects it because the directory exists (it may contain consumer-owned files such as a README.md). Glob patterns (`ADR-*.md`) are also unsupported.

Together these bugs form a closed loop: #214 requires consumers to enumerate prune-globbed files; #215 blocks the compact directory-prefix workaround.

## Decision

**FR-001 — Extend audit coverage with prune-glob resolved files**

`audit_source_tree_coverage` SHALL extend `all_coverage_roots` with the set of files in the source repository that match any glob in `consumer_init.source_artifact_prune_globs_on_init`, resolved via `fnmatch.fnmatch` against the pre-enumerated tracked-file list. This eliminates the per-release maintenance burden on consumers and is semantically correct: prune-glob-matched files are intentionally excluded from delivery.

**FR-002/FR-003 — Add is_file() and glob support to _validate_absent_files**

`_validate_absent_files` SHALL classify each `source_only` entry before checking:
- **File entry** (no `*`, does not end with `/`): check `is_file()` instead of `exists()`. A directory that happens to share the name of a `source_only` entry will no longer trigger a false error.
- **Glob/prefix entry** (contains `*` or ends with `/`): enumerate matching consumer repo files via `fnmatch` against a pre-built file list; emit an error for each matching file found.

## Consequences

- Consumers with `source_artifact_prune_globs_on_init` no longer need to maintain a per-ADR enumeration in `source_only`.
- Consumers that want to use a directory-prefix or glob as a `source_only` entry (e.g. for audit explicitness) can now do so without validation errors.
- Exact-file `source_only` entries continue to behave identically (backward-compatible).
- `fnmatch` does not support `**` recursive patterns. Prune-globs containing `**` are not supported; the resolver will warn if `**` appears.

## Alternatives Considered

**Option B — Consumer enumerates each file in source_only**: No code changes; all maintenance burden on consumers. Rejected: every new blueprint ADR requires a coordinated consumer update, which scales poorly and was the root cause of #214.

## Diagrams

No diagram required — changes are isolated two-function patches in existing scripts with no new component boundaries.
