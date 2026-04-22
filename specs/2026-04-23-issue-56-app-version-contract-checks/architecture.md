# Architecture

## Context
- Work item: 2026-04-23-issue-56-app-version-contract-checks
- Owner: bonos
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `apps-audit-versions` audits shell var drift but does NOT cross-check that catalog artifacts (`versions.lock`, `manifest.yaml`) reflect the same values. A consumer can update `versions.sh` without re-running bootstrap, leaving stale catalog artifacts. `apps-smoke` validates manifest structure but not pin values.
- Scope boundaries: `scripts/lib/platform/apps/`, `scripts/bin/platform/apps/`, `tests/infra/`. No new make targets, no changes to templates or catalog format.
- Out of scope: source file checks (`pyproject.toml`, `package.json`); new canonical version variables.

## Bounded Contexts and Responsibilities
- Context A (blueprint governance): owns `scripts/bin/platform/apps/` and `scripts/lib/platform/apps/`; the new checker belongs here.
- Context B (generated-consumer catalog): owns `apps/catalog/versions.lock` and `apps/catalog/manifest.yaml`; checker reads these without writing.

## High-Level Component Design
- Domain layer: `version_contract_checker.py` — pure functions for lock parse, lock check, manifest check, consistency check.
- Application layer: `audit_versions.sh` (extended drift+contract checks), `smoke.sh` (extended consistency check), `audit_versions_cached.sh` (expanded fingerprint).
- Infrastructure adapters: `pathlib.Path.read_text` for file I/O; `re.search` for manifest line matching. No external deps.
- Presentation/API/workflow boundaries: human-readable stdout report; `apps_version_contract_check_total` metric; non-zero exit on failure.

## Integration and Dependency Edges
- Upstream dependencies: `versions.sh` (sourced in `audit_versions.sh`) provides expected var values; `apps/catalog/versions.lock` and `apps/catalog/manifest.yaml` are catalog artifacts.
- Downstream dependencies: `audit_cache_calculate_fingerprint` (in `audit_cache.sh`) receives expanded `fingerprint_files[]`.
- Data/API/event contracts touched: `apps_version_contract_check_total` metric added; `apps_version_audit_summary_total` metric extended with `contract_checks` and `contract_failures` labels.

## Non-Functional Architecture Notes
- Security: all file reads via `pathlib`; no subprocess calls; no shell injection vectors from version value interpolation (values are `re.escape`d in regex patterns).
- Observability: `apps_version_contract_check_total` metric per invocation with status label; per-check results printed to stdout.
- Reliability and rollback: missing catalog files → skip silently; unreadable files → `(OSError, UnicodeDecodeError)` caught, check returns failed result; revert commit to roll back.
- Monitoring/alerting: `contract_failures` label in summary metric can drive alert thresholds.

## Risks and Tradeoffs
- Risk 1: text-based manifest matching may produce false negatives if the manifest format changes. Mitigated by: the manifest is machine-generated from a fixed template; format changes would be a breaking template change requiring a separate SDD.
- Tradeoff 1: no PyYAML dependency (text-match) vs. robustness of a proper YAML parse. Accepted: the fixed schema makes regex sufficient and keeps the runtime footprint minimal.
