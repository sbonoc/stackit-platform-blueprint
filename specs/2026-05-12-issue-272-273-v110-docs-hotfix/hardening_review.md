# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1 (#272): `--ignore-workspace` removed from `docs_pnpm_install`, `docs_pnpm_build`, and `docs_pnpm_start` in v1.10.0. Consumers with a root `pnpm-workspace.yaml` that excludes `docs/` received a silently empty `docs/node_modules/` and a `docusaurus: not found` error on `make docs-build`. Fixed by restoring the flag and its explanatory comment to all three functions.
- Finding 2 (#273): `_docs_assert_pnpm_version` `log_fatal` message named only two of three pnpm version sources ("local pnpm installation" and "CI action's corepack prepare pin") but omitted the most common mismatch cause — the root `package.json#packageManager` field auto-activated by corepack on `pnpm install` from repo root. Fixed by rewriting the message to enumerate all three sources with alignment instructions.

## Observability and Diagnostics Changes

- Metrics/logging/tracing updates: no new log channels, metrics, or trace spans introduced. `_docs_assert_pnpm_version` continues to emit via `log_fatal` (NFR-OBS-001 preserved). The `log_fatal` message text is expanded to name all three pnpm version sources, making the fatal error actionable without manual investigation.
- Operational diagnostics updates: `docs/platform/consumer/troubleshooting.md` updated with a v1.10.0 docs build section covering both regressions, symptom tables, and remediation steps. Bootstrap template mirror synced.
- Alerts/ownership: none — docs build failures surface in CI log output; no alert configuration changed.
- Runbook updates: `docs/platform/consumer/troubleshooting.md` is the consumer-facing runbook; updated in the document phase.

## Architecture and Code Quality Compliance

- SOLID / Clean Architecture / Clean Code / DDD checks: no new abstractions, no new functions, no new modules. Both fixes are targeted single-line or single-block edits to an existing shell script. `--ignore-workspace` is a flag restoration (not a behavior change in direction). `log_fatal` multi-argument form is idiomatic for the existing logging contract (`_log_emit "$*"` joins with `$IFS` space). No layering violations — `scripts/lib/docs/site.sh` is a tooling script with no domain/application/infrastructure separation concern.
- Test-automation and pyramid checks: 6 new unit-tier regression tests added (`tests/infra/test_docs_site_sh_issue_272_273.py`); registered in `test_pyramid_contract.json`. Tests are content-level (read file, assert string), require no network, cluster, or pnpm installation. Pyramid ratios after addition: unit 96%, integration 3%, e2e 1% — all within policy limits.
- Documentation/diagram/CI/skill consistency checks: troubleshooting doc and bootstrap template mirror are byte-identical (verified via `diff`). No skill runbooks changed. No CI workflow changed. No Make contract changed. ADR diagrams are spec-only (Mermaid in ADR file) — no live docs diagram updated because no live diagram existed for pnpm invocation details.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI components
- [x] SC 2.1.1 (Keyboard): N/A — no UI components
- [x] SC 2.4.7 (Focus Visible): N/A — no UI components
- [x] SC 1.4.1 (Use of Color): N/A — no UI components
- [x] SC 3.3.1 (Error Identification): N/A — no UI components
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components; pure shell script and docs changes

## Proposals Only (Not Implemented)

- Proposal 1: `blueprint-align-pnpm-pins` migration target — a Make target backed by `scripts/bin/blueprint/align_pnpm_pins.sh` that takes `docs/package.json` as canonical and rewrites all other `packageManager` fields to match (with dry-run support). Rationale for deferral: expands hotfix scope with a new automation script; the Option A error message improvement is sufficient for operators to resolve drift manually. Suggested approach: new standalone blueprint-scope work item with dry-run default, confirmation prompt, and a test suite for the rewrite logic.
- Proposal 2: Preflight pnpm version drift detection — a `quality-pnpm-version-contract` check (or extension of `infra-validate`) that scans all `package.json#packageManager` fields and reports drift before any install runs. Rationale for deferral: new quality hook out of scope for a two-line hotfix. Suggested approach: quality-scope work item; integrate into `infra-validate` or as a standalone `quality-pnpm-version-contract` target; emit structured drift report with file paths and conflicting versions.
