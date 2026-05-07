# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `check_spec_pr_ready.py` had no validation of the Hardening Review's Accessibility Gate section — unchecked gate items could silently pass PR packaging. Fixed by extending the script to flag any unchecked non-N/A Accessibility Gate item (FR-105). Applies retroactively to all future PRs.
- Finding 2: SDD lifecycle templates had no accessibility NFR, no task block, no hardening checklist section, and no WCAG SC traceability column — a11y compliance was entirely ad-hoc per consumer. Fixed by adding NFR-A11Y-001, T-A01–T-A05, the Accessibility Gate section, and the WCAG SC column unconditionally across the four scaffold templates (FR-101–FR-104).
- Finding 3: `quality-hooks-fast` had no staleness gate for the ACR — consumers could let their conformance report go stale indefinitely with no CI signal. Fixed by wiring `quality-a11y-acr-check` into the fast gate recipe (FR-305).
- Finding 4: Bootstrap template `blueprint/contract.yaml` was missing the `spec.quality.accessibility` key added to the live contract — `infra-validate` flagged template drift. Fixed by syncing the bootstrap template.
- Finding 5: `docs/platform/accessibility/acr.md` was not registered in `required_seed_files` — consumers would not receive the ACR scaffold on upgrade. Fixed by adding to `required_seed_files` in both contract files and creating the bootstrap template.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `check_acr_freshness.py` emits a structured diagnostic on every exit path: file path (relative to repo root), days elapsed since last review, configured staleness window, and a concrete remediation command. Follows NFR-OPS-001 and the existing `[quality-a11y-acr-check] FAIL — ...` / `OK — ...` prefix convention. `axe_page_scan.mjs` writes `artifacts/a11y/axe-report-<route>.json` per scanned route and prints a human-readable violation summary to stdout. `start_script_metric_trap` is called in all new shell scripts (`test_a11y.sh`, `a11y_smoke.sh`) for script duration metrics consistent with the rest of the platform.
- Operational diagnostics updates: `quality-a11y-acr-check` is now part of `quality-hooks-fast` output; its PASS/FAIL line appears in the keep-going summary block. `quality-a11y-acr-sync` prints per-row update/add counts when run manually. No new alerting rules; ACR staleness is a pre-PR local gate, not a runtime alert.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: all new scripts (`check_acr_freshness.py`, `sync_acr_criteria.py`) are single-responsibility Python modules following the existing `[quality-*]` prefix pattern. `axe_page_scan.mjs` and `axe_preset.ts` are single-responsibility; the preset export is the only consumer-facing API. No domain logic involved — this is pure tooling.
- Test-automation and pyramid checks: TDD red→green applied across all three slices (14 new contract assertions failing before implementation, green after). Test pyramid maintained: 136 total contract tests pass; unit=95.10% (above 60% floor), integration=3.84% (below 30% cap), e2e=1.07% (below 10% cap). No test pyramid regression.
- Documentation/diagram/CI/skill consistency checks: `docs/blueprint/governance/quality_hooks.md` updated with ACR Staleness Gate section and synced to bootstrap template mirror. `docs/platform/consumer/accessibility.md` new consumer adoption guide registered in `required_seed_files` and bootstrap template. `core_targets.generated.md` auto-regenerated via `make quality-docs-sync-core-targets`. `.agents/skills/blueprint-sdd-step07-pr-packager/SKILL.md` updated with ACR review step. `quality-ci-check-sync` passes. No Mermaid diagram changes (no flow/state changes).

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — tooling and governance change; no UI components
- [x] SC 2.1.1 (Keyboard): N/A — no interactive elements
- [x] SC 2.4.7 (Focus Visible): N/A — no interactive elements
- [x] SC 1.4.1 (Use of Color): N/A — no visual output
- [x] SC 3.3.1 (Error Identification): N/A — no user-facing forms
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components; the work item delivers the axe scanning infrastructure itself

## Proposals Only (Not Implemented)
- Proposal 1 (`consumer_fitness_status.sh`): Q-2 Option B chose to wire `quality-a11y-acr-check` into `quality-hooks-fast` instead of creating a new `consumer_fitness_status.sh` script. The script surface is deferred to a standalone work item when a broader set of consumer fitness checks beyond the ACR check is identified.
- Proposal 2 (`layer:` field in `spec.md` template): Q-1 Option B chose unconditional a11y sections with N/A opt-out. Adding a `layer:` field is a cross-cutting structural change to the spec template that warrants its own work item.
- Proposal 3 (`quality-a11y-acr-check` in `quality-ci-blueprint`): Explicitly excluded — risk of false positives in blueprint's own CI where no consumer ACR exists by default. Reconsidering this would require the blueprint CI to have its own stable ACR or a skip mechanism.
- Proposal 4 (automated W3C JSON fetch in `sync_acr_criteria.py`): The bundled criterion list is static. Fetching from the W3C at CI time adds network dependency; deferred until a caching layer or offline mirror is available.
