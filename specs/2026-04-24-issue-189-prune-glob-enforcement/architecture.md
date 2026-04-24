# Architecture

## Context
- Work item: issue-189 — prune-glob enforcement in upgrade validate and postcheck
- Owner: platform blueprint maintainer
- Date: 2026-04-24

## Stack and Execution Model
- Backend stack profile: python3 (existing upgrade tooling stack)
- Frontend stack profile: none
- Test automation profile: pytest (existing test suite in tests/blueprint/)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `source_artifact_prune_globs_on_init` is enforced at init time only. After upgrade, operators who manually resolve merge conflicts may add files that match prune globs (blueprint-internal ADRs, spec folders), re-introducing them into generated-consumer repos with no warning. The upgrade tooling has no awareness of these globs post-init. The fix adds a prune glob scan to `upgrade_consumer_validate.py` (post-apply validate phase), surfaces the result in `upgrade_consumer_postcheck.py`, and adds an explicit required check step to the operator skill runbook.
- Scope boundaries: three files — `scripts/lib/blueprint/upgrade_consumer_validate.py` (new `_scan_prune_glob_violations()` function + `prune_glob_check` section + status gate update), `scripts/lib/blueprint/upgrade_consumer_postcheck.py` (read `prune_glob_check` from validate report, emit `prune_glob_violations` section, add `prune-glob-violations` to `blocked_reasons`), `.agents/skills/blueprint-consumer-upgrade/SKILL.md` (add required check step after manual merge resolution).
- Out of scope: upgrade planner (`upgrade_consumer.py`), plan/apply JSON schema changes, new CLI flags, new environment variables, consumer repo enforcement.

## Bounded Contexts and Responsibilities
- Validate module (`scripts/lib/blueprint/upgrade_consumer_validate.py`): owns post-apply state verification; is the authoritative place for the prune glob check because it already loads the blueprint contract and scans the consumer working tree. A new `_scan_prune_glob_violations()` function uses `pathlib.Path.rglob()` with each pattern from `source_artifact_prune_globs_on_init` and collects matching paths.
- Postcheck module (`scripts/lib/blueprint/upgrade_consumer_postcheck.py`): aggregates validate + reconcile + behavioral check results into `blocked_reasons`. Reads `prune_glob_check` from the validate report; if `violation_count > 0`, adds `prune-glob-violations` to `blocked_reasons` and writes a `prune_glob_violations` section to `upgrade_postcheck.json`.
- Skill runbook (`.agents/skills/blueprint-consumer-upgrade/SKILL.md`): operator-facing upgrade procedure. Must add an explicit required check step after the manual merge resolution phase, naming the canonical glob patterns by value.

## High-Level Component Design
- Domain layer: the prune glob check is a post-merge-resolution concern. The validate phase runs after the operator resolves all merge conflicts — violations are surfaced before the upgrade branch is pushed, which is the correct enforcement point.
- Application layer: `_scan_prune_glob_violations(repo_root, contract)` iterates `contract.source_artifact_prune_globs_on_init`, calls `repo_root.rglob(pattern)` for each, and returns a sorted list of repo-relative POSIX paths. The validate main flow appends the `prune_glob_check` section to the report JSON and sets `summary.status = "failure"` when `violation_count > 0`. The postcheck reads the new section from the validate payload; if violations are present, it appends `prune-glob-violations` to `blocked_reasons` and writes `prune_glob_violations: {violation_count, violations}` to the postcheck JSON.
- Infrastructure adapters: `pathlib.Path.rglob()` exclusively — no subprocess, no shell expansion. Symlinks that resolve outside the repo root MUST NOT be followed. Contract access via existing `load_blueprint_contract()`.
- Presentation/API/workflow boundaries: `make blueprint-upgrade-consumer-validate` and `make blueprint-upgrade-consumer-postcheck` invocation signatures are unchanged. JSON report schema changes are additive only — a new `prune_glob_check` section in `upgrade_validate.json`, a new `prune_glob_violations` section in `upgrade_postcheck.json`.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` (`source_artifact_prune_globs_on_init`) must be loadable. If it cannot be loaded, the existing `contract_load_error` gate already covers that failure path; `prune_glob_check.status` is set to `skipped` with no additional failure contribution.
- Downstream dependencies: `upgrade_consumer_postcheck.py` reads `prune_glob_check` from `upgrade_validate.json`. The postcheck is modified only to read this new additive field.
- Data/API/event contracts touched: `upgrade_validate.json` gains `prune_glob_check` (additive). `upgrade_postcheck.json` gains `prune_glob_violations` (additive). `docs/blueprint/architecture/execution_model.md` MUST be updated to document the prune glob check in the validate phase.

## Non-Functional Architecture Notes
- Security: `pathlib.Path.rglob()` is used exclusively — no shell expansion, no subprocess. Symlinks that resolve outside the repo root MUST NOT be followed (use `Path.resolve()` check against `repo_root` before collecting). Glob patterns come from `blueprint/contract.yaml` (blueprint-controlled, not operator-supplied at runtime).
- Observability: one `stderr` line per violation in the format `prune-glob violation: <path> (matches: <glob>)`. Violations are also listed in `upgrade_validate.json` under `prune_glob_check.violations`. No new metrics required.
- Reliability and rollback: if the contract cannot be loaded, `prune_glob_check.status = "skipped"` — the existing `contract_load_error` block already handles this path with no additional failure contribution. If `prune_glob_check` is absent from the validate report (e.g. stale report from before this fix), the postcheck treats `violation_count` as 0 and does not block.
- Monitoring/alerting: no changes to existing alerting surface. Violations surface in JSON reports and in the make target exit code.

## Risks and Tradeoffs
- Risk 1: a glob pattern that matches many files could be slow to evaluate. Mitigation: patterns are narrow (`specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*`, `docs/blueprint/architecture/decisions/ADR-*.md`); scope is a single consumer repo. No realistic performance concern.
- Tradeoff 1: the validate gate runs after the operator resolves manual merges. There is a window between apply and validate where violations may exist undetected. This is acceptable — violations are surfaced before the upgrade branch is pushed, which is the correct and sufficient enforcement point.
