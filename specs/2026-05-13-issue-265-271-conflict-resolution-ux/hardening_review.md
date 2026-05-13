# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: No repository-wide findings — all changes are additive (new triage JSON artifact, new resolve script, new make target); no pre-existing code paths were modified in ways that would surface latent defects.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: The resolve script emits one `upgrade-resolve: <action> <path>` line per applied action to stdout (NFR-OBS-001), making output grep-parseable by agents and CI pipelines.
- Operational diagnostics updates: `artifacts/blueprint/upgrade_resolve.json` records per-action results (`path`, `action_taken`, `result`) for post-run inspection. `artifacts/blueprint/upgrade_triage.json` provides a machine-readable triage manifest for all conflicts.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: `_recommended_action()`, `_write_upgrade_triage()`, and `_resolve()` are small, single-purpose functions. `upgrade_consumer_resolve.py` is standalone-importable (main guard) so tests can exercise `_resolve()` directly without spawning a subprocess.
- Test-automation and pyramid checks: 14 new tests (5 triage + 9 resolve) registered in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope. TDD red-green cycle enforced — failing tests committed before implementation.
- Documentation/diagram/CI/skill consistency checks: `blueprint.generated.mk` regenerated from template; `docs/reference/generated/core_targets.generated.md` regenerated; `SKILL.md` Stage 2 table updated; pipeline usage block updated; `docs/reference/generated/core_targets.generated.md` passes `quality-docs-check-changed`.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — CLI tool with no browser-rendered UI surface (NFR-A11Y-001)
- [x] SC 2.1.1 (Keyboard): N/A — CLI tool with no browser-rendered UI surface
- [x] SC 2.4.7 (Focus Visible): N/A — CLI tool with no browser-rendered UI surface
- [x] SC 1.4.1 (Use of Color): N/A — CLI tool with no browser-rendered UI surface
- [x] SC 3.3.1 (Error Identification): N/A — CLI tool with no browser-rendered UI surface
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — CLI tool with no browser-rendered UI surface

## Proposals Only (Not Implemented)
- Proposal 1 (Option B — source-exists inference for blueprint-managed catch-all): Parked — trigger: after: issue-270. Without explicit consumer ownership markers from #270, auto-applying `take_source` to catch-all files risks overwriting consumer modifications. Safe to re-evaluate once #270 ships.
- Proposal 2 (Interactive TUI — ncurses/lazygit-style): Rejected — heavy external dependency, not portable across consumer environments; residual table is typically under 10 rows; explicitly rejected in ADR at design time.
- Proposal 3 (HTML conflict report): Rejected — browser context-switch adds friction for a small residual table; CLI display is sufficient; explicitly rejected in ADR at design time.
