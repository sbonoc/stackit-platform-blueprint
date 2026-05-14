# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: `upgrade_consumer_pipeline.sh` Stage 1c/2c failure exit codes now propagate correctly via `stage1c_rc` / `stage2c_rc` variables captured before the `|| rc=$?` pattern — previously a failing subprocess would have silently set `rc` to 0 on some shells due to how `||` interacts with `set -e`. Fixed during implementation.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: no new metrics or traces introduced; all observability is via structured log lines with `[PIPELINE] Stage 1c:` / `[PIPELINE] Stage 2c:` prefixes as specified in FR-004 and FR-007. Log lines carry workaround id and title for operator grep-ability.
- Operational diagnostics updates: new artefact `artifacts/blueprint/workarounds_applied.json` (NFR-OPS-001) gives downstream tooling per-workaround `status` (`applied`, `skipped`, `failed`, `reverted`) without requiring log parsing.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: engine (`upgrade_workarounds.py`) follows Single-Responsibility — loading, evaluation, dispatch, and writing are separate methods; action kinds are plain function boundaries not class hierarchies, appropriate for 3 well-bounded strategies. Parser and filer are independent modules with no coupling to the engine.
- Test-automation and pyramid checks: 34 new tests (22 engine + 8 parser + 4 filer) all registered in `scripts/lib/quality/test_pyramid_contract.json` under `unit` scope; test pyramid contract gate verified.
- Documentation/diagram/CI/skill consistency checks: SKILL.md extended with Workaround Catalogue section (catalogue mechanics, filing step, authoring guide); ADR-issue-268 authored and approved; spec cross-referenced from AGENTS.backlog.md.

## Known Gap (Deferred — see Proposals section)
- `action_path` existence in the manifest is not validated by CI: a blueprint author who commits a manifest entry pointing at a non-existent file will only see the failure at consumer upgrade time. Deferred from initial scope per spec explicit exclusions; tracked as a follow-up proposal below.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI components (NFR-A11Y-001)
- [x] SC 2.1.1 (Keyboard): N/A — no UI components (NFR-A11Y-001)
- [x] SC 2.4.7 (Focus Visible): N/A — no UI components (NFR-A11Y-001)
- [x] SC 1.4.1 (Use of Color): N/A — no UI components (NFR-A11Y-001)
- [x] SC 3.3.1 (Error Identification): N/A — no UI components (NFR-A11Y-001)
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components (NFR-A11Y-001)

## Proposals Only (Not Implemented)
- Proposal 1 (`env_var` action kind): support modifying `.envrc` / environment variable exports as a workaround action kind. Excluded from initial scope due to risk of persistent consumer environment pollution. Revisit when a concrete use case arises with a clear revert path.
- Proposal 2 (manifest `action_path` CI validation): add a `make quality-workaround-manifest-check` target that verifies every `action_path` referenced in `manifest.yaml` resolves to an existing file in the catalogue tree. Prevents silent failures at consumer upgrade time. Suitable as a quality hook addition in the next hardening cycle.
