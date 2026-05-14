# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1 (spec scope): `_write_upgrade_triage()` passed only `ownership_class` to `_recommended_action()`, so blueprint-managed catch-all conflicts where the file genuinely exists in the blueprint source (`source_exists=True`) were incorrectly classified as `human_required`. Fixed by passing `source_exists` to `_recommended_action()` and recording it in each triage entry; the inference is safe since issue #270 (PR #290) eliminated consumer-created test files in blueprint-tracked directories.

- Finding 2 (pre-existing; fixed in this PR): `contract_schema.py` custom YAML parser did not strip inline comments from scalar values. `last_applied_version: ""  # engine-managed; written by upgrade_consumer_postcheck on success` was parsed as the full string `'""  # engine-managed...'`, which is truthy. `_resolve_baseline_ref` searched for a non-existent git tag and returned `None`, causing the plan computation to classify all differing files as `ACTION_CONFLICT` instead of `ACTION_MERGE_REQUIRED` — producing 20 incorrect test failures in `tests/blueprint/test_upgrade_consumer.py`. Fixed by adding `_strip_inline_comment()` with an escape-aware quote loop (handles embedded `\"`-style escapes) called from `_parse_scalar()`.

- Finding 3 (pre-existing; fixed in this PR): `test_apply_conflict_creates_artifact_and_fails` in `tests/blueprint/test_upgrade_consumer.py` expected `returncode=1` and `status="failure"` for conflict scenarios. AC-004 (issues #264/#266) intentionally changed this to `returncode=0` and `status="conflicts"`. The test was misaligned with the current design. Renamed to `test_apply_conflict_creates_artifact_and_writes_conflicts_status` and updated both assertions.

- Finding 4 (pre-existing; fixed in this PR): Nine stale test assertions across `tests/blueprint/` reflected outdated states: (a) pipeline stage consolidation — tests expected individual `Stage 8:` / `Stage 9:` markers and a direct `blueprint-upgrade-consumer-validate` call, but the pipeline had consolidated to `Stages 8+9:` + `blueprint-upgrade-consumer-finalize`; (b) file-path moves — tests referenced `tests/infra/test_optional_module_required_env_contract.py` and `tests/infra/test_async_message_contracts.py` after both files had moved to `tests/blueprint/`; (c) Python invocation style — tests checked for `@python3` and `run_cmd python3` strings in production files that had switched to `@uv run python3` and `run_cmd uv run python3`; (d) catalog renderer API — test passed `--app-runtime-backend-image` / `--app-runtime-touchpoints-image` args that were replaced by `--app-descriptor-path` + `--component-image`.

- Finding 5 (new; implemented in this PR): `tests/blueprint/` (953 tests: upgrade engine, pipeline, tooling contracts, quality contracts, schema validation) had no CI or pre-push coverage. These tests were run locally only. All 29 pre-existing failures went undetected in CI. Fixed by adding a `blueprint-test-unit` make target (defined in `blueprint.generated.mk.tmpl` + `blueprint.generated.mk`) wired into `test-unit-all` via the same prerequisite pattern as `test-contracts-all: test-contracts-async-all`. CI propagation: `blueprint-test-unit` → `test-unit-all` → `quality-ci-fast` → `quality-ci-blueprint` PR gate — no CI YAML changes needed. Also added a `blueprint-test-unit` pre-push hook in both `.pre-commit-config.yaml` files (live + bootstrap template) so failures are caught locally before push.

## Observability and Diagnostics Changes
- Metrics/logging/tracing updates: none — upgrade engine tooling only; no runtime observability surface (SDD-C-010 N/A, per spec.md).
- Operational diagnostics updates: `source_exists` field added to each `upgrade_triage.json` conflict entry provides a complete audit trail for every auto-resolution decision.

## Architecture and Code Quality Compliance
- SOLID / Clean Architecture / Clean Code / DDD checks: single-responsibility preserved — `_recommended_action()` remains the sole mapping site; `_write_upgrade_triage()` orchestrates but does not duplicate logic. No cross-layer imports introduced. `_strip_inline_comment()` is a pure function with no side effects; isolated from all other parsing paths.
- Test-automation and pyramid checks: 3 new unit tests added for source_exists inference; 29 pre-existing failures resolved; `tests/blueprint/` suite now runs in CI via `blueprint-test-unit` → `test-unit-all`. Full suite: 953 passed, 0 failures. Pyramid ratio improved (blueprint unit lane formally promoted to CI gate).
- Documentation/diagram/CI/skill consistency checks: ADR approved, Mermaid flowchart in `architecture.md` updated during intake, docs build PASS, docs smoke PASS. `infra-validate` bootstrap template drift check confirmed clean after both `.pre-commit-config.yaml` files were updated in sync.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- [x] SC 4.1.2 (Name, Role, Value): N/A — no UI components (NFR-A11Y-001)
- [x] SC 2.1.1 (Keyboard): N/A — no UI components
- [x] SC 2.4.7 (Focus Visible): N/A — no UI components
- [x] SC 1.4.1 (Use of Color): N/A — no UI components
- [x] SC 3.3.1 (Error Identification): N/A — no UI components
- [x] axe-core WCAG 2.1 AA scan evidence: N/A — no UI components

## Proposals Only (Not Implemented)
- Proposal 1: `test_pyramid_contract.json` contains explicit file-path references that drift silently when files move (demonstrated by the `tests/infra/` → `tests/blueprint/` moves that caused 2 of the 9 stale failures). Automating path validation — e.g., checking all listed paths exist on disk and emitting a diff when they do not — would prevent this class of silent drift. Trigger: on-scope: quality.
- Proposal 2: `quality-ci-upgrade-validate` (end-to-end upgrade validation) runs only on push to main, not on PRs. A breaking upgrade regression could merge undetected. Making it a non-blocking PR annotation or a separate required status would close this gap. Trigger: on-scope: blueprint.
