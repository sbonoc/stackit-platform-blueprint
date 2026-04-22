# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1 (triggered by issue-118-137): all four SDD publish-gate files (plan.md, tasks.md, hardening_review.md, pr_context.md) shipped with verbatim scaffold placeholder content in the previous work item because `quality-sdd-check` has no coverage for these files. Fixed by adding `check_spec_pr_ready.py` and wiring it into `hooks_fast.sh`; test coverage in `tests/blueprint/test_spec_pr_ready.py` prevents recurrence.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new runtime metrics; `check_spec_pr_ready.py` emits violations to stdout prefixed with `[quality-spec-pr-ready]` — machine-readable by CI log parsers and the operator's terminal.
- Operational diagnostics updates: each violation includes the file name and line number so the author can locate the placeholder immediately; the exit code is the only signal consumed by make and `hooks_fast.sh`.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: four focused check functions (`_check_tasks`, `_check_plan`, `_check_hardening_review`, `_check_pr_context`), each with single responsibility; `_resolve_spec_dir` isolates resolution logic; `main()` is a thin orchestrator; constants are module-level; no shared state.
- Test-automation and pyramid checks: 39 tests added covering positive-path (fully-filled spec dir exits 0), per-file negative-path (each placeholder variant), branch-pattern regex, spec-slug env var override, missing spec dir, and missing file cases; all tests are deterministic and require no external dependencies.
- Documentation/diagram/CI/skill consistency checks: ADR created; `quality-spec-pr-ready` added to the PHONY list and target section in both the makefile template and regenerated makefile; `hooks_fast.sh` updated with branch-pattern guard; `quality-docs-sync-core-targets` will update the core-targets doc on sync.

## Proposals Only (Not Implemented)
- Proposal 1: add a spec template drift test that asserts the constant tuples in `check_spec_pr_ready.py` are consistent with labels in `.spec-kit/templates/blueprint/` — deferred; requires parsing template markdown or maintaining a separate allowlist contract, which is a larger scope than this work item.
- Proposal 2: extend `check_spec_pr_ready.py` to also validate `architecture.md` and `context_pack.md` for placeholder content — deferred; these files are already covered by `check_sdd_assets.py`.
