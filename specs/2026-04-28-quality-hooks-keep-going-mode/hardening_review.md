# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Redundant `run_cmd make quality-docs-lint` and `run_cmd make quality-test-pyramid` calls in `hooks_fast.sh` caused double execution when pre-commit was installed; removed (pre-commit hooks run them) and replaced the pre-commit-missing fallback with a `log_warn` that names the install URL.
- Finding 2: `hooks_fast.sh` had no path-gating on `infra-validate` and `infra-contract-test-fast`; docs/spec-only commits paid the full infra validation cost (~80s); gated behind `quality_paths_match_infra_gate` with `QUALITY_HOOKS_FORCE_FULL` override.
- Finding 3: Agent inner-loop documentation was fragmented across five skills with no single canonical source and no agent-agnostic env kit; unified under AGENTS.md `§ Quality Hooks — Inner-Loop and Pre-PR Usage` with cross-links from all six skill files and `.envrc`/`.claude/settings.json` defaults.
- Finding 4: EXIT trap in keep-going helper composes with existing `start_script_metric_trap` trap via `_KG_PREV_TRAP` capture; temp directory cleanup fires even under SIGTERM.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: added `quality_hooks_keep_going_total` metric (labels: `status`, `phase`, `failed_checks`) emitted by `keep_going_finalize`; added `quality_hooks_skip_total` metric (labels: `phase`, `check`, `reason`) emitted on path-gate and phase-gate skips; per-check `log_info` start lines and stderr tail re-emission under keep-going; `log_metric quality_ci_check_sync_total` and `quality_template_smoke_total` unchanged.
- Operational diagnostics updates: summary block (`===== quality-hooks keep-going summary =====` ... per-check PASS/FAIL/duration lines ... `===== N check(s) failed =====`) provides at-a-glance diagnosis without re-reading full log; tail re-emission captures last 40 lines (configurable via `QUALITY_HOOKS_KEEP_GOING_TAIL_LINES`) of each failed check inline.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: helper follows Single Responsibility (aggregation only); entry scripts retain their existing structure with additive guards; no shared mutable state between entry scripts; `quality_gating.sh` is a pure-predicate module with no side effects except on `QUALITY_HOOKS_FORCE_FULL` shortcut; default code path preserved byte-for-byte under the `else` branch.
- Test-automation and pyramid checks: 12 new test files classified as `unit` in `test_pyramid_contract.json`; 793 tests pass (781 existing + 12 new files, total count verified post-implementation); coverage spans helper contract, gating predicates, each entry-script path, AC-001..AC-019; no integration or e2e tests required (all tests use synthetic fixtures or subprocess with temp repos).
- Documentation/diagram/CI/skill consistency checks: `make/blueprint.generated.mk` re-rendered from template; `docs/blueprint/governance/quality_hooks.md` added; six skill files cross-linked; `AGENTS.md` and `scripts/templates/consumer/init/AGENTS.md.tmpl` mirrored; ADR status moved to `approved`; no CI workflow changes required (CI runs `make quality-hooks-fast` without keep-going; behavior unchanged).

## Proposals Only (Not Implemented)
- Proposal 1 (not implemented): parallel execution of independent checks (deferred — see ADR Alternative D; adds process management complexity and interleaved log ordering issues; deferred to a follow-up work item once the serial aggregation model proves valuable).
- Proposal 2 (not implemented): structured JSON summary output for machine consumers (deferred — see Explicit Exclusions item 4 in spec.md; no current consumer; design when the need is concrete).
