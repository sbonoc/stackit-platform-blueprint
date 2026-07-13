# Architecture

## Context
- Work item: v1.12.5 patch batch — issues #403, #393, #402, #404
- Owner: bonos
- Date: 2026-07-13

## Stack and Execution Model
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: bats_or_shell_unit (Python unittest + subprocess stubs)
- Agent execution model: none

## Problem Statement
- What needs to change and why: Four shell-layer defects discovered during consumer work and STACKIT dev bootstrapping require targeted fixes: (1) missing ESO secret keys block fresh dev cluster startup; (2) silent env-var precedence bypass causes operators to run with stale credentials; (3) single-arch Docker publish breaks arm64 local clusters; (4) EXIT trap replacement drops metrics and `run_cmd` exposes credential values in trace.
- Scope boundaries: `scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh`, `scripts/lib/shell/bootstrap.sh`, `scripts/bin/platform/apps/publish_ghcr.sh`, `scripts/lib/shell/exec.sh`, and their test files.
- Out of scope: Terraform modules, Kubernetes manifests, Python service code, frontend, managed-service configuration.

## Bounded Contexts and Responsibilities

### #403 — ESO secret seeding (infra layer)
`stackit_foundation_seed_runtime_secret.sh` → `stackit_runtime_secret_env.py` → Kubernetes `runtime-credentials-source` Secret. The Python transformer reads Terraform outputs; when outputs are absent (fresh cluster, no TF apply yet), the shell script provides dev-profile placeholders.

### #393 — env-file loading (shell library)
`scripts/lib/shell/bootstrap.sh::load_env_file_defaults` is the single loading function for all `.env.*` files. It must enforce consistent precedence regardless of whether assignment lines use `export VAR=val` or bare `VAR=val` syntax.

### #402 — container image publishing (apps layer)
`publish_ghcr.sh` wraps `docker build` + `docker push`. The fix lifts the hardcoded amd64 constraint to `docker buildx build --platform ...` with a configurable default.

### #404 — script lifecycle and subprocess safety (shell library)
`scripts/lib/shell/exec.sh` provides `run_cmd`, `start_script_metric_trap`, and related primitives used by all scripts. Composed EXIT trap + new credential-safe helpers are additive, non-breaking additions.

## High-Level Component Design

### #403 fix
After `stackit_runtime_secret_env.py` writes TF-sourced keys into `$secret_env_file`, a series of `grep -q "^key=" "$secret_env_file" || echo "key=$DEFAULT" >> "$secret_env_file"` guard blocks inject placeholder values for each of the 11 missing keys. Guard blocks are gated on `BLUEPRINT_PROFILE=stackit-dev` (implicitly — they live inside the `tooling_is_execution_enabled` branch which is only reached from dev profile in the usual flow) and use TF-output-wins semantics via the `grep -q` check.

### #393 fix
`load_env_file_defaults` currently: (1) snapshots variable names from the file via `sed`, (2) `source`s the file with `set -a`, (3) restores pre-existing values. The fix applies `sed 's/^[[:space:]]*export[[:space:]]\+//'` to the variable-name extraction regex and to the file content before sourcing, so `export VAR=val` lines are treated as `VAR=val` at both the snapshot and the source step.

### #402 fix
Replace `docker build -f ... -t ... $ctx; docker push $image` with `docker buildx build --platform "$APPS_GHCR_BUILD_PLATFORMS" -f ... -t ... --push $ctx`. Add `set_default_env APPS_GHCR_BUILD_PLATFORMS "linux/amd64,linux/arm64"` at the top of the script.

### #404 fix
- `start_script_metric_trap`: capture existing trap with `_prior="$(trap -p EXIT | sed ...)"`, then build compound handler.
- `run_cmd_env`: parse `KEY=val` args before `--`, build env array, call `env "${env_args[@]}" "${cmd[@]}"`, trace only the cmd part.
- `run_with_stdin_secret`: `"$@" < "$tmpfile"; rc=$?; rm -f "$tmpfile"; return $rc`.

## Integration and Dependency Edges
- #403: `stackit_runtime_secret_env.py` (upstream caller), Kubernetes ESO (downstream consumer of `runtime-credentials-source` Secret)
- #393: all scripts that `source bootstrap.sh` (entire blueprint script fleet — fix is additive/non-breaking)
- #402: `docker buildx` CLI (must be installed; Docker Desktop provides it by default), GHCR OCI registry
- #404: all scripts that call `start_script_metric_trap`, `run_cmd`, or set EXIT traps

## Non-Functional Architecture Notes
- Security: #393 closes a silent credential-bypass; #404 prevents credential leakage in trace output. Both changes are additive; no existing secure paths are altered.
- Observability: #404 preserves metric emission regardless of script-local EXIT trap composition order.
- Reliability and rollback: all changes are in shell scripts tracked in git; rollback is a revert commit. #402 buildx cross-compilation increases build time but is otherwise backward-compatible.
- Monitoring/alerting: no new dashboards or alerts required.

## Risks and Tradeoffs
- Risk 1 (#402): `docker buildx` requires a buildx builder that supports multi-arch (QEMU or native arm64 runner). Docker Desktop provides this by default; CI may need explicit `docker buildx create --use` setup if not already present.
- Risk 2 (#404 trap composition): `trap -p EXIT` output format is bash-version-dependent. The `sed` extraction of the handler body must be tested on the minimum bash version in use (4.x).
- Tradeoff 1 (#402): multi-arch builds take longer (two-platform cross-compilation). Acceptable for a manual/CI publish step; mitigated by `APPS_GHCR_BUILD_PLATFORMS` override for environments that do not need arm64.
