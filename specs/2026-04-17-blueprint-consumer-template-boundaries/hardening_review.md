# Hardening Review

## Repository-Wide Findings Fixed
- Added contract-governed `source_artifact_prune_globs_on_init` in source and bootstrap contract surfaces.
- Added contract-governed blueprint docs template allowlist (`spec.docs_contract.blueprint_docs.template_sync_allowlist`) as the single source for docs mirror scope.
- Added initial-mode-only prune helper in init flow so consumer-owned artifacts remain safe after transition.
- Hardened prune logic to reject unsafe glob patterns, skip out-of-root resolved candidates, and avoid following symlinked directories during deletion.
- Refactored blueprint docs template sync to explicit allowlist and deterministic missing-source failure behavior.
- Removed source-only docs from bootstrap template mirror to prevent blueprint-history duplication in generated repositories.
- Updated governance ownership matrix to document source-only SDD/ADR boundary.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates:
  - No new telemetry series added; deterministic diagnostics remain in existing check command output and `ChangeSummary` action reporting.
- Operational diagnostics updates:
  - Added targeted tests that surface prune-mode and docs-allowlist drift failures with explicit assertions.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks:
  - Contract declaration, parser support, and runtime behavior are split across focused modules (`contract_schema`, `init_repo_contract`, docs sync utility).
  - Ownership boundary policy is explicit in governance docs and decision log.
- Test-automation and pyramid checks:
  - Added focused unit/contract tests in existing blueprint suites; no duplicate high-level end-to-end test expansion for this scope.
- Documentation/diagram/CI/skill consistency checks:
  - SDD artifacts completed and synchronized with code/test evidence.
  - PR packaging and hardening gates validated via canonical make targets.

## Proposals Only (Not Implemented)
- Add a dedicated contract checker that verifies every `source_artifact_prune_globs_on_init` pattern is documented in ownership matrix source-only rows.
