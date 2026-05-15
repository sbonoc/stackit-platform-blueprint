# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no pre-existing defects identified; this work item is purely additive (new scripts, make targets, hooks wiring, governance docs) with no existing behaviour modified.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: `quality_docs_cross_reference_check_total` (status=success|failure) and `quality_docs_agents_md_structure_check_total` (status=success|failure) emitted by `hooks_fast.sh`; `quality_hooks_skip_total` emitted when structure check skipped in blueprint repo (check=quality-docs-agents-md-structure-check reason=blueprint-repo).
- Operational diagnostics updates: both scripts emit `[quality-docs-cross-reference-check]` / `[quality-docs-agents-md-structure-check]` prefixed violation messages to stderr naming the offending heading — immediate remediation context consistent with existing `check_*.py` output conventions.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: single responsibility per script (`check_docs_cross_reference.py` = heading-overlap only; `check_agents_md_structure.py` = structural elements only); `REPO_ROOT` monkeypatch pattern consistent with existing quality scripts; stdlib-only Python (no subprocess/network) — NFR-PERF-001 satisfied; PyYAML for allowlist parsing (existing dependency).
- Test-automation and pyramid checks: 25 unit tests green in 0.04s (16 cross-reference + 9 structure check); both test files registered in `scripts/lib/quality/test_pyramid_contract.json` as unit-tier entries; pyramid ratios: unit=96.96% (min >60%), int=2.28% (max ≤30%), e2e=0.76% (max ≤10%) — all within bounds.
- Documentation/diagram/CI/skill consistency checks: `quality_hooks.md` updated (Targets table + new § AGENTS.md ↔ north_star.md Checks) and synced to bootstrap template mirror; `troubleshooting.md` updated (§ AGENTS.md structure check fails after blueprint upgrade) and synced; `core_targets.generated.md` regenerated; no stale TODOs or dead code.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 N/A — tooling-only change; no UI or interactive elements introduced.
- [x] SC 2.1.1 N/A — no UI.
- [x] SC 2.4.7 N/A — no UI.
- [x] SC 1.4.1 N/A — no UI.
- [x] SC 3.3.1 N/A — no UI.
- [x] axe-core scan N/A — no UI. See NFR-A11Y-001 in spec.md for rationale.

## Proposals Only (Not Implemented)

- Proposal (Option B — body-heuristic detection): extend `check_docs_cross_reference.py` with section-heading + body heuristic to detect paraphrased content duplication beyond exact heading matching. Deferred per spec Normative Option Decision (OPTION_A selected); adds false-positive risk before Option A consumer feedback is gathered. Outcome: park — trigger: on-scope: quality.
