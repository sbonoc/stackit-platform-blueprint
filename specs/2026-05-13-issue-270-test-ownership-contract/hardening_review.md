# Hardening Review

## Repository-Wide Findings Fixed
- Finding 1: Blueprint-author test files were incorrectly listed in `spec.repository.required_files` and delivered to consumer repos via the upgrade resolver's 3-way merge, causing false-positive failures. Files relocated to `tests/blueprint/` (source_only); contract assertion (FR-005) enforces the rule going forward.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none
- Operational diagnostics updates: none

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: Single-responsibility improvement — `tests/infra/` now contains only consumer-runtime assertions; `tests/blueprint/` now contains only blueprint-author assertions. The split is enforced by a new contract assertion (FR-005).
- Test-automation and pyramid checks: 5 new test files registered in `test_pyramid_contract.json` under `unit` scope; test pyramid ratios remain within bounds (unit 96.70%, integration 2.48%, e2e 0.83%).
- Documentation/diagram/CI/skill consistency checks: `docs/blueprint/governance/ownership_matrix.md` updated with normative `## Test Directory Taxonomy` section; bootstrap template mirror synced; `scripts/bin/infra/contract_test_fast.sh` updated to reference relocated paths; `infra-contract-test-fast` passes 68 tests.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [N/A] SC 4.1.2 (Name, Role, Value): blueprint tooling only; no UI components
- [N/A] SC 2.1.1 (Keyboard): blueprint tooling only; no UI components
- [N/A] SC 2.4.7 (Focus Visible): blueprint tooling only; no UI components
- [N/A] SC 1.4.1 (Use of Color): blueprint tooling only; no UI components
- [N/A] SC 3.3.1 (Error Identification): blueprint tooling only; no UI components
- [N/A] axe-core WCAG 2.1 AA scan evidence: N/A — no UI (NFR-A11Y-001)

## Proposals Only (Not Implemented)
- Proposal 1: Active cleanup of stale relocated files from existing consumer repos (delete-on-upgrade) — out of scope per D-3 in architecture.md; consumers can delete manually or re-run `make blueprint-init-repo`.
