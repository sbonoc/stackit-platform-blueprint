# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Slice 1 — Issue #403: ESO dev fallback

- [ ] T-101 Write `tests/infra/test_seed_runtime_secret_issue_403.py` (red: all 11 keys missing when TF outputs absent)
- [ ] T-102 Add T-102 assertion: TF-present key not overwritten by guard
- [ ] T-103 Implement guard blocks in `stackit_foundation_seed_runtime_secret.sh` (green)
- [ ] T-104 Register `tests/infra/test_seed_runtime_secret_issue_403.py` in `test_pyramid_contract.json`

## Slice 2 — Issue #393: load_env_file_defaults export-prefix bypass

- [ ] T-201 Write `tests/shell/test_load_env_file_defaults_issue_393.py` (red: export-prefix bypass test + bare-assignment test)
- [ ] T-202 Fix `load_env_file_defaults` in `scripts/lib/shell/bootstrap.sh` (green)
- [ ] T-203 Register `tests/shell/test_load_env_file_defaults_issue_393.py` in `test_pyramid_contract.json`

## Slice 3 — Issue #402: publish_ghcr multi-arch

- [ ] T-301 Write `tests/apps/test_publish_ghcr_issue_402.py` (red: multi-arch flag + platform override)
- [ ] T-302 Fix `scripts/bin/platform/apps/publish_ghcr.sh` (green)
- [ ] T-303 Register `tests/apps/test_publish_ghcr_issue_402.py` in `test_pyramid_contract.json`

## Slice 4 — Issue #404: exec.sh foundational gaps

- [ ] T-401 Write `tests/shell/test_exec_issue_404.py` (red: trap compose + run_cmd_env no leak + run_with_stdin_secret tmpfile delete)
- [ ] T-402 Fix `scripts/lib/shell/exec.sh` (green)
- [ ] T-403 Register `tests/shell/test_exec_issue_404.py` in `test_pyramid_contract.json`

## Slice 5 — Documentation

- [ ] T-501 Update `docs/platform/consumer/troubleshooting.md` (APPS_GHCR_BUILD_PLATFORMS note + ESO dev-fallback keys)
- [ ] T-502 Sync bootstrap template mirror `scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md`

## Validation and Release Readiness

- [ ] T-V01 Run `uv run python3 -m pytest tests/infra/test_seed_runtime_secret_issue_403.py tests/shell/test_load_env_file_defaults_issue_393.py tests/apps/test_publish_ghcr_issue_402.py tests/shell/test_exec_issue_404.py -v` — all green
- [ ] T-V02 Run `make quality-sdd-check` — pass
- [ ] T-V03 Confirm no stale TODOs or dead code
- [ ] T-A01 N/A — no user-facing flow (no accessibility tasks required)

## Publish

- [ ] P-001 Update `hardening_review.md`
- [ ] P-002 Update `pr_context.md`
- [ ] P-003 PR description follows repository template; references `pr_context.md` and `Closes #403`, `Closes #393`, `Closes #402`, `Closes #404`
