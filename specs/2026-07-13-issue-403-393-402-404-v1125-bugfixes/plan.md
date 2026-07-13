# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: all four fixes are minimal, targeted changes to existing functions. No new abstractions introduced.
- Anti-abstraction gate: `run_cmd_env` and `run_with_stdin_secret` are direct bash helpers, not wrapper layers.
- Integration-first testing gate: subprocess-based tests with mock stubs cover realistic execution paths before implementation details.
- Positive-path filter/transform test gate: AC-001 and AC-002 assert that correct values are written (positive) and that TF-present values are not overwritten (negative); AC-003 and AC-004 exercise both the guard-pass and guard-skip paths.
- Finding-to-test translation gate: all four issue reproduction steps are translated into failing Python unittest assertions (T-101–T-403) before implementation.

## Delivery Slices

### Slice 1: Tests (red) — issue #403 ESO dev fallback

1. Write `tests/infra/test_seed_runtime_secret_issue_403.py` asserting T-101 (placeholder keys present when TF outputs absent) and T-102 (TF-present key not overwritten). Run → RED.
2. Implement guard blocks in `stackit_foundation_seed_runtime_secret.sh`. Run → GREEN.

### Slice 2: Tests (red) — issue #393 export-prefix bypass

1. Write `tests/shell/test_load_env_file_defaults_issue_393.py` asserting T-201 (export-prefix bypass closed) and T-202 (bare assignment still loaded). Run → RED.
2. Fix `load_env_file_defaults` in `scripts/lib/shell/bootstrap.sh`. Run → GREEN.

### Slice 3: Tests (red) — issue #402 multi-arch publish

1. Write `tests/apps/test_publish_ghcr_issue_402.py` asserting T-301 (multi-arch flag) and T-302 (APPS_GHCR_BUILD_PLATFORMS override). Run → RED.
2. Fix `scripts/bin/platform/apps/publish_ghcr.sh`. Run → GREEN.

### Slice 4: Tests (red) — issue #404 exec.sh gaps

1. Write `tests/shell/test_exec_issue_404.py` asserting T-401 (trap compose), T-402 (run_cmd_env no credential leak), T-403 (run_with_stdin_secret tmpfile deleted). Run → RED.
2. Fix `scripts/lib/shell/exec.sh`. Run → GREEN.

### Slice 5: Documentation and ADR

- Sync `docs/platform/consumer/troubleshooting.md` with `APPS_GHCR_BUILD_PLATFORMS` note and ESO dev-fallback placeholder keys.
- Sync bootstrap template mirror at `scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md`.
- Register all new test files in `scripts/lib/quality/test_pyramid_contract.json`.

## Change Strategy
- Migration/rollout sequence: all changes are to blueprint source; consumers pick up the fix at v1.12.5 upgrade.
- Backward compatibility policy: all changes are backward-compatible. `APPS_GHCR_BUILD_PLATFORMS` defaults to multi-arch. `run_cmd_env` and `run_with_stdin_secret` are new additions; no existing callers affected.
- Rollback plan: revert commits to the four affected files.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/infra/test_seed_runtime_secret_issue_403.py tests/shell/test_load_env_file_defaults_issue_393.py tests/apps/test_publish_ghcr_issue_402.py tests/shell/test_exec_issue_404.py -v`
- Contract checks: `make quality-sdd-check`
- Integration checks: none required (all fixes are shell-library layer, no K8s cluster dependency)
- E2E checks: N/A

## App Onboarding Contract (Normative)
- App onboarding impact: no-impact
- Notes: `make apps-publish-ghcr` behavior changes (multi-arch default), but no new required make targets.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/platform/consumer/troubleshooting.md` — add `APPS_GHCR_BUILD_PLATFORMS` override note; add ESO dev-fallback placeholder key list.
- Consumer docs updates: bootstrap template mirror sync.
- Mermaid diagrams updated: none
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate: not required — no HTTP route/filter changes.
- Publish checklist:
  - Requirement/contract coverage via test assertions
  - Key reviewer files: four modified scripts + four new test files
  - Validation evidence: pytest output
  - Rollback notes: revert the four script changes

## Operational Readiness
- Logging/metrics/traces: `start_script_metric_trap` fix ensures `script_duration_seconds` metric is always emitted; no new dashboards required.
- Alerts/ownership: none
- Runbook updates: `docs/platform/consumer/troubleshooting.md` only

## Risks and Mitigations
- Risk 1 (buildx availability in CI) → mitigation: add `docker buildx version` preflight check in `publish_ghcr.sh` execute mode; document requirement in troubleshooting guide.
- Risk 2 (trap -p format differences across bash versions) → mitigation: test the `sed` extraction of trap body on bash 4.x and 5.x in the test suite.
