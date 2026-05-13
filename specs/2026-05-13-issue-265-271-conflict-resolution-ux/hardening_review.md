# Hardening Review

## Repository-Wide Findings Fixed
- No repository-wide findings were identified or fixed in this work item. All changes are additive (new triage JSON artifact, new resolve script, new make target); no pre-existing code paths were modified in ways that would surface latent defects.

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
- Option B (source-exists inference for blueprint-managed catch-all): deferred until Issue #270 ships explicit consumer ownership markers. Without those markers, auto-applying `take_source` to catch-all files risks overwriting consumer modifications. Safe to re-evaluate after #270.
- Interactive TUI (ncurses/lazygit-style): rejected; heavy dependency, not portable across consumer environments.
- HTML conflict report: rejected; browser context switch adds friction for the typically-small residual table.
