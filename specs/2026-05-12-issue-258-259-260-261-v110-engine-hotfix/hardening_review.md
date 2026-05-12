# Hardening Review

## Repository-Wide Findings Fixed

- **Finding 1 — Contract coverage gap (#258):** `pyproject.toml`, `uv.lock`,
  `infra/local/helm/opensearch/values.yaml`, and `infra/local/helm/kms/values.yaml`
  introduced in v1.10.0 were absent from `blueprint/contract.yaml` and its bootstrap
  template, causing `audit_source_tree_coverage` to report 4 uncovered source files on
  every consumer upgrade run.  Fixed by classifying the 4 files under the correct
  ownership classes and extending the `opensearch` and `kms` optional module definitions
  with `helm_path` + `paths_required_when_enabled`.  Bootstrap template synced to eliminate
  `validate_contract.py` drift.

- **Finding 2 — Validate target contamination (#260):** `blueprint-template-smoke` was
  being run as a validation target against generated-consumer repos even though it only
  makes sense in the template-source repo.  Fixed by adding `_get_effective_validation_targets()`
  which filters out `blueprint-template-smoke` when `repo_mode == generated-consumer`.

- **Finding 3 — Volatile artifact false positives (#261):** `upgrade_validate.json` and
  `required_files_status.json` embed absolute repo paths captured from make-target stdout.
  Comparing their SHA-256 checksums across a fresh worktree vs working-tree run always
  produced a divergence.  Fixed by adding both filenames to `_VOLATILE_ARTIFACT_NAMES`.

- **Finding 4 — Transitive source resolution cap (#259):** The behavioral check was
  capped at depth-1 source resolution, causing functions defined in transitively sourced
  files to be flagged as unresolved.  Fixed by replacing the depth-1 loop with a BFS
  traversal (`_collect_defined_functions_transitive`) that uses a frozenset visited guard
  to handle circular source chains.  `uv` and `validate` (added in v1.10.0 scripts) also
  added to `_EXCLUDED_TOKENS` to prevent false positives.

## Observability and Diagnostics Changes

- No changes to logging calls, metric names, or JSON report schemas.
- All existing `log_info`/`log_error`/`[BEHAVIORAL-CHECK]` output lines preserved.
- `ShellBehavioralCheckResult`, `FreshEnvGateResult`, and `UpgradeValidateReport` schemas
  are unchanged — no field additions or removals.

## Architecture and Code Quality Compliance

- SOLID: `_get_effective_validation_targets` is a pure function (single responsibility;
  no side effects).  `_collect_defined_functions_transitive` replaces a depth-1 loop with
  a BFS iteration — same contract, wider scope.
- Clean Code: no new comments beyond required WHY explanations.  Function names are
  self-documenting.
- Test pyramid: 4 new test files classified as `unit` in `test_pyramid_contract.json`.
  All tests use in-memory temp dirs — no network, no cluster access.
- Full test suite (324 tests) passes on branch.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI components
- [x] SC 2.1.1 (Keyboard): N/A — no UI components
- [x] SC 2.4.7 (Focus Visible): N/A — no UI components
- [x] SC 1.4.1 (Use of Color): N/A — no UI components
- [x] SC 3.3.1 (Error Identification): N/A — no UI components
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components

## Proposals Only (Not Implemented)

- **Proposal: Full POSIX shell parser:** Replace the grep-based `_FUNC_DEF_EXTRACT` heuristic
  with a proper POSIX shell parser (e.g., `pash` or `shellcheck --format=json`) to eliminate
  the residual class of missed definitions from complex multi-line or heredoc-embedded function
  declarations.  Deferred — the heuristic covers all known failure classes from production data;
  a full parser requires a new dependency and is out of scope for an MVP hotfix.

- **Proposal: Automated workaround removal migration:** Add a post-upgrade check that warns
  consumers who still have `extra_excluded_tokens: [uv, validate]` in their contract after
  upgrading to the fixed blueprint version.  Deferred to the next consumer-tooling sprint.
