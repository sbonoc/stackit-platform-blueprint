# ADR: v1.12.5 patch batch — four shell-layer defects (#403, #393, #402, #404)

- **Status:** proposed
- **Date:** 2026-07-13
- **Issues:** #403, #393, #402, #404
- **Spec:** `specs/2026-07-13-issue-403-393-402-404-v1125-bugfixes/spec.md`

## Context

Four independently reproducible defects were surfaced during dhe-marketplace consumer work and STACKIT dev cluster bootstrapping:

1. **#403 (P1)** — `stackit_foundation_seed_runtime_secret.sh` dev fallback does not write the 11 lowercase connection-detail keys (`postgres_host`, `postgres_port`, `postgres_database`, `postgres_username`, `postgres_password`, `opensearch_scheme`, `opensearch_host`, `opensearch_host_clean`, `opensearch_port`, `opensearch_username`, `opensearch_password`) that the STACKIT-specific ExternalSecrets reference. On a fresh dev cluster where Terraform has not yet provisioned managed services, every ESO ExternalSecret referencing these keys stays in `SecretSyncedError` indefinitely.

2. **#393 (P2)** — `load_env_file_defaults` in `bootstrap.sh` uses `set_default_env` which guards with `[[ -z "${!var_name:-}" ]]`. This guard works for bare `VAR=value` assignments but is bypassed by `export VAR=value` lines: because `bootstrap.sh` loads `.env.local` with a bare `source` before calling `blueprint_load_env_defaults`, any `export VAR=value` in `.env.local` sets the variable in the shell environment and the secrets-file value is silently discarded. Credential precedence is both incorrect and undocumented.

3. **#402 (P2)** — `publish_ghcr.sh` uses `docker build ... --platform linux/amd64` (hardcoded). On Apple Silicon developer machines running Docker Desktop Kubernetes (arm64 nodes), this produces a single-arch amd64-only OCI manifest that causes `ImagePullBackOff` whenever a pod is scheduled on a node without a pre-cached image.

4. **#404 (P2)** — `exec.sh` has three foundational gaps: (a) `start_script_metric_trap` installs its EXIT handler with a plain `trap`, silently dropping any previously-installed EXIT trap and causing the existing handler to be silently dropped if the script later installs its own cleanup trap; (b) `run_cmd` prints all positional args via `printf '+ %s\n' "$*"`, exposing credential values passed as positional arguments in trace output; (c) no canonical helper exists for credential injection into subprocesses without exposing values in argv.

## Decision

Apply targeted, minimal fixes to each affected file:

### #403 — TF-output-wins guard blocks in seed script

Add eleven `if ! grep -q "^key=" "$secret_env_file"; then echo "key=$DEFAULT"; fi >> "$secret_env_file"` guard blocks inside the `tooling_is_execution_enabled` branch, immediately after the `stackit_runtime_secret_env.py` call. Each guard only writes the placeholder when the key was not already written by the Python transformer. Default values use in-cluster DNS service names, overridable via env vars.

**Alternatives considered:**
- A) Extend `stackit_runtime_secret_env.py` to emit placeholder rows — rejected: the Python transformer's contract is Terraform-outputs-only; dev fallbacks belong in the shell orchestration layer.
- B) Add a separate dev-profile initialization script — rejected: adds a new touch point that consumers must discover and invoke; modifying the existing seed script is simpler and more discoverable.

### #393 — Strip `export` prefix before snapshot and source

Modify `load_env_file_defaults` to strip `export ` prefixes from lines when building the variable-name snapshot (the `sed -nE` extraction) and when sourcing the file (via a stripped temporary copy or `sed` pipe), so `export VAR=val` and `VAR=val` are treated identically. Pre-existing env vars are still protected by the restore loop.

**Alternatives considered:**
- A) Load `.env.local` via `load_env_file_defaults` instead of bare `source` — viable, but does not fix the underlying bypass; a later caller with a bare source would reintroduce the issue.
- B) Document the precedence chain only — insufficient; the bug causes silent incorrect behavior.
- C) Deprecate `.env.local` — breaking change, out of scope for a patch.

### #402 — `docker buildx build --platform` with configurable default

Replace `docker build -f ... -t ... $ctx && docker push $image` with `docker buildx build --platform "$APPS_GHCR_BUILD_PLATFORMS" -f ... -t ... --push $ctx`. Add `set_default_env APPS_GHCR_BUILD_PLATFORMS "linux/amd64,linux/arm64"` at script top.

**Alternatives considered:**
- A) Build separate manifests and combine with `docker manifest create` — more steps, same result; buildx is the modern approach.
- B) Detect host arch at runtime and build only matching arch — does not serve CI (which must produce manifests for all target platforms).

### #404 — Composed trap + credential-safe helpers

- `start_script_metric_trap`: capture `trap -p EXIT` before installing the metric handler; construct a compound handler that fires both the captured body and the metric emit.
- `run_cmd_env`: new function that accepts `KEY=val` env prefix args before `--` separator; calls `env "${env_pairs[@]}" "${cmd[@]}"` without printing env values in the trace.
- `run_with_stdin_secret`: new function that reads CMD stdin from a caller-provided tmpfile and deletes the tmpfile after the command exits.

**Alternatives considered:**
- A) Modify `run_cmd` to detect and redact credential-looking args — rejected: no reliable heuristic; creates false negatives.
- B) Use `setsid` + named pipe for credential injection — more complex; `run_with_stdin_secret` with a tmpfile is simpler and sufficient for the use cases identified.

## Consequences

- **#403:** Fresh STACKIT dev bootstrap with postgres+opensearch enabled no longer produces `SecretSyncedError`. Existing bootstraps (with real TF outputs) are unaffected (TF-output-wins guard).
- **#393:** Silent credential-bypass via `export`-prefixed `.env.local` lines is closed. All existing bare-assignment usage is unchanged.
- **#402:** `make apps-publish-ghcr` now produces multi-arch OCI images by default. Consumers requiring single-arch builds set `APPS_GHCR_BUILD_PLATFORMS=linux/amd64`. Build time increases modestly for multi-arch cross-compilation.
- **#404:** All scripts using `start_script_metric_trap` now reliably emit duration metrics regardless of EXIT trap composition order. `run_cmd_env` and `run_with_stdin_secret` are available as documented, credential-safe subprocess patterns.

## Diagrams

No diagram required — all four fixes are within-function changes to existing shell scripts; control flow is linear and does not span components or services.
