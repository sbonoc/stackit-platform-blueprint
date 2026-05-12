# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Engine silently treated file conflicts identically to fatal errors (both `return 1`); pipeline aborted Stages 3–10 for every conflict. Fixed by returning 0 with `status="conflicts"` so the pipeline can continue to resolution stages.
- Finding 2: `_resolve_baseline_ref` always used `template_version` (the immutable init-time version) as the baseline for 3-way merges. On multi-hop upgrades this caused incorrect diffs. Fixed by preferring `last_applied_version` when set, falling back to `template_version`.
- Finding 3: Pipeline never set `BLUEPRINT_UPGRADE_APPLY=true` as the default; every invocation was silently plan-only unless callers explicitly set the variable. Fixed by adding `set_default_env BLUEPRINT_UPGRADE_APPLY true` and a `PLAN-ONLY mode` banner.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: Pipeline Stage 2 now logs `status=` from the apply artifact (e.g., `status=conflicts`, `status=success`) rather than just the make exit code, improving operator visibility. `_write_last_applied_version` prints the version it wrote to `blueprint/contract.yaml`. PLAN-ONLY banner emitted at pipeline startup when `BLUEPRINT_UPGRADE_APPLY != true`.
- Operational diagnostics updates: `upgrade_apply.json` status field now distinguishes `"conflicts"` from `"failure"`, enabling automated tooling to route each outcome to the correct follow-up action without parsing stderr.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Single-responsibility preserved — `_write_last_applied_version` is a focused helper in postcheck, not embedded in the main flow. `_resolve_baseline_ref` parameter added without changing callers' other behaviour. No new abstractions introduced beyond what the spec required.
- Test-automation and pyramid checks: 9 new tests added to the integration tier (registered in `test_pyramid_contract.json`). TDD red-green cycle followed for all 4 slices. Tests use source-code assertion pattern (stable, no real git setup needed for pipeline/engine source-level checks) and mock-based unit assertions for the postcheck helper.
- Documentation/diagram/CI/skill consistency checks: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` updated to document `BLUEPRINT_UPGRADE_APPLY=false` plan-only override and the new pipeline default. Usage block in `upgrade_consumer_pipeline.sh` updated. No diagram changes required (upgrade pipeline architecture unchanged).

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI changes; backend pipeline and Python scripts only
- [x] SC 2.1.1 (Keyboard): N/A — no UI changes
- [x] SC 2.4.7 (Focus Visible): N/A — no UI changes
- [x] SC 1.4.1 (Use of Color): N/A — no UI changes
- [x] SC 3.3.1 (Error Identification): N/A — no UI changes
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI changes; no frontend artifacts produced

## Proposals Only (Not Implemented)
- none
