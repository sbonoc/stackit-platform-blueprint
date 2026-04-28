# PR Context

## Summary
- Work item: 2026-04-28-quality-hooks-keep-going-mode (FR-001..FR-017, AC-001..AC-019)
- Objective: Add `--keep-going` / `QUALITY_HOOKS_KEEP_GOING=true` aggregate mode to `hooks_fast.sh`, `hooks_strict.sh`, and `hooks_run.sh`; add path-gating on infra checks; add phase-gating on `quality-spec-pr-ready`; remove double-execution of `quality-docs-lint` + `quality-test-pyramid`; propagate policy to AGENTS.md, six skill files, and env kit.
- Scope boundaries: `scripts/lib/shell/keep_going.sh` (new), `scripts/lib/shell/quality_gating.sh` (new), `scripts/bin/quality/hooks_fast.sh`, `scripts/bin/quality/hooks_strict.sh`, `scripts/bin/quality/hooks_run.sh`, `AGENTS.md`, six skill files, `.envrc`, `.claude/settings.json`, `docs/blueprint/governance/quality_hooks.md`, `docs/blueprint/architecture/decisions/ADR-20260428-quality-hooks-keep-going-mode.md`, `make/blueprint.generated.mk`; no HTTP routes, no DB migrations, no consumer breaking changes.

## Requirement Coverage
- Requirement IDs covered: FR-001..FR-017, NFR-SEC-001, NFR-OBS-001, NFR-OBS-002, NFR-REL-001, NFR-OPS-001, NFR-OPS-002
- Acceptance criteria covered: AC-001..AC-019 (all)
- Contract surfaces changed: `scripts/lib/shell/keep_going.sh` public API (`keep_going_active`, `keep_going_init`, `run_check`, `keep_going_finalize`); `scripts/lib/shell/quality_gating.sh` public API (`_quality_changed_paths`, `quality_paths_match_infra_gate`, `quality_spec_is_ready`); `hooks_fast.sh` / `hooks_strict.sh` / `hooks_run.sh` `--help` text and `--keep-going` flag; `.envrc` and `.claude/settings.json` env defaults.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/shell/keep_going.sh` — aggregation helper (4-function public API, EXIT trap composition)
  - `scripts/lib/shell/quality_gating.sh` — path/phase gate predicates
  - `scripts/bin/quality/hooks_fast.sh` — main entry point; path-gating + phase-gating + dedup wiring
  - `scripts/bin/quality/hooks_run.sh` — cross-phase sentinel pattern
  - `AGENTS.md § Quality Hooks — Inner-Loop and Pre-PR Usage` — canonical policy subsection
- High-risk files: `scripts/bin/quality/hooks_fast.sh` (default code path must remain byte-identical; verify `else` branches match the pre-PR baseline); `scripts/lib/shell/keep_going.sh` (EXIT trap composition — must not clobber the metric trap from `start_script_metric_trap`).

## Validation Evidence
- Required commands executed: `make quality-hooks-fast` (keep-going active via `.envrc`, ~169s); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (~174s); `make docs-build` (pass); `make docs-smoke` (pass); `make quality-hardening-review` (pass); `python3 -m pytest tests/blueprint/ -q` (793 tests, all pass); `make quality-sdd-check` (pass).
- Result summary: all 793 tests pass; `docs-build` and `docs-smoke` pass after fixing MDX `&lt;1 s` escape and removing broken relative link to `AGENTS.md` from `quality_hooks.md`; `quality-docs-check-changed` fixed by running `sync_blueprint_template_docs.py` to add `quality_hooks.md` to the blueprint template docs; `quality-hardening-review` pass; only outstanding failure is `quality-spec-pr-ready` which fails until all publish tasks are marked complete (self-referential gate, by design).
- Artifact references: `specs/2026-04-28-quality-hooks-keep-going-mode/traceability.md`, `specs/2026-04-28-quality-hooks-keep-going-mode/hardening_review.md`, `docs/blueprint/governance/quality_hooks.md`, `docs/blueprint/architecture/decisions/ADR-20260428-quality-hooks-keep-going-mode.md`.

## Risk and Rollback
- Main risks: (1) Default-path regression — mitigated by preserving verbatim `run_cmd` lines under `else` branches and adding a contract test (T-106/AC-001) that asserts only the first failure is observed with no summary marker; (2) EXIT trap clobber — mitigated by `_KG_PREV_TRAP` capture pattern; (3) path-gating false-skip on new infra paths — mitigated by conservative gating set; `QUALITY_HOOKS_FORCE_FULL=true` override available; CI runs unconditionally.
- Rollback strategy: revert the patch; `keep_going.sh` and `quality_gating.sh` can be deleted or left in place (the `if keep_going_active` guards become dead code without the env var); no state to migrate, no data to recover, no consumer breaking changes.

## Deferred Proposals
- Proposal 1 (not implemented): parallel execution of independent checks — deferred; see ADR Alternative D and hardening_review.md Proposals Only section.
- Proposal 2 (not implemented): structured JSON summary output for machine consumers — deferred; no current consumer; design when the need is concrete.
