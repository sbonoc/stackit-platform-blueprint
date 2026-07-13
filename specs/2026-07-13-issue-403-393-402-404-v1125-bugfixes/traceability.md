# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-001, SDD-C-011 | Guard blocks in seed script | `scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh` | T-101, T-102 | `docs/platform/consumer/troubleshooting.md` | `script_duration_seconds` metric |
| FR-002 | SDD-C-001 | TF-output-wins guard check (`grep -q`) | `stackit_foundation_seed_runtime_secret.sh` | T-102 | spec.md FR-002 | — |
| FR-003 | SDD-C-001 | Env-var-overridable defaults | `stackit_foundation_seed_runtime_secret.sh` | T-101 | spec.md FR-003 | — |
| FR-004 | SDD-C-001 | Placement inside `tooling_is_execution_enabled` branch | `stackit_foundation_seed_runtime_secret.sh` | T-101 | spec.md FR-004 | — |
| FR-005 | SDD-C-001, SDD-C-015 | Strip `export` prefix in `load_env_file_defaults` | `scripts/lib/shell/bootstrap.sh` | T-201, T-202 | spec.md FR-005 | — |
| FR-006 | SDD-C-001 | Pre-existing var restore loop unchanged | `scripts/lib/shell/bootstrap.sh` | T-201, T-202 | — | — |
| FR-007 | SDD-C-001 | `docker buildx build --platform $APPS_GHCR_BUILD_PLATFORMS --push` | `scripts/bin/platform/apps/publish_ghcr.sh` | T-301, T-302 | `docs/platform/consumer/troubleshooting.md` | — |
| FR-008 | SDD-C-001 | `set_default_env APPS_GHCR_BUILD_PLATFORMS linux/amd64,linux/arm64` | `scripts/bin/platform/apps/publish_ghcr.sh` | T-302 | spec.md FR-008 | — |
| FR-009 | SDD-C-002 | Dry-run log includes platform string | `scripts/bin/platform/apps/publish_ghcr.sh` | T-301 | — | — |
| FR-010 | SDD-C-001, SDD-C-011 | `trap -p EXIT` compose in `start_script_metric_trap` | `scripts/lib/shell/exec.sh` | T-401 | spec.md FR-010 | `script_duration_seconds` metric |
| FR-011 | SDD-C-001, SDD-C-015 | `run_cmd_env` function | `scripts/lib/shell/exec.sh` | T-402 | spec.md FR-011 | — |
| FR-012 | SDD-C-001, SDD-C-015 | `run_with_stdin_secret` function | `scripts/lib/shell/exec.sh` | T-403 | spec.md FR-012 | — |
| NFR-SEC-001 | SDD-C-015 | Guard blocks unreachable on non-dev profiles | `stackit_foundation_seed_runtime_secret.sh` | T-101 | spec.md NFR-SEC-001 | — |
| NFR-SEC-002 | SDD-C-015 | `correct` beats `export stale` in precedence | `scripts/lib/shell/bootstrap.sh` | T-201 | spec.md NFR-SEC-002 | — |
| NFR-SEC-003 | SDD-C-015 | `run_cmd_env` trace does not print values | `scripts/lib/shell/exec.sh` | T-402 | spec.md NFR-SEC-003 | — |
| NFR-REL-001 | SDD-C-010, SDD-C-011 | Trap compose handles both orderings | `scripts/lib/shell/exec.sh` | T-401 | spec.md NFR-REL-001 | — |
| AC-001 | SDD-C-001 | All 11 placeholder keys present | `stackit_foundation_seed_runtime_secret.sh` | T-101 | — | — |
| AC-002 | SDD-C-001 | TF-present key not overwritten | `stackit_foundation_seed_runtime_secret.sh` | T-102 | — | — |
| AC-003 | SDD-C-015 | export-prefix bypass closed | `scripts/lib/shell/bootstrap.sh` | T-201 | — | — |
| AC-004 | SDD-C-001 | bare assignment loaded | `scripts/lib/shell/bootstrap.sh` | T-202 | — | — |
| AC-005 | SDD-C-001 | multi-arch flag present | `scripts/bin/platform/apps/publish_ghcr.sh` | T-301 | — | — |
| AC-006 | SDD-C-001 | platform override respected | `scripts/bin/platform/apps/publish_ghcr.sh` | T-302 | — | — |
| AC-007 | SDD-C-010, SDD-C-011 | trap compose fires both handlers | `scripts/lib/shell/exec.sh` | T-401 | — | — |
| AC-008 | SDD-C-015 | run_cmd_env no credential leak | `scripts/lib/shell/exec.sh` | T-402 | — | — |
| AC-009 | SDD-C-001 | tmpfile deleted after use | `scripts/lib/shell/exec.sh` | T-403 | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, NFR-SEC-001, NFR-SEC-002, NFR-SEC-003, NFR-REL-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles: `make quality-sdd-check`, `uv run python3 -m pytest tests/infra/test_seed_runtime_secret_issue_403.py tests/shell/test_load_env_file_defaults_issue_393.py tests/apps/test_publish_ghcr_issue_402.py tests/shell/test_exec_issue_404.py -v`
- Result summary: pending — to be populated at step05
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- `docker buildx` availability in CI environments not using Docker Desktop — must be verified at step05.
- `trap -p EXIT` format portability across bash 4.x / 5.x — verified by T-401 test matrix.
