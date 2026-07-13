# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/platform/architecture/decisions/ADR-issue-403-393-402-404-v1125-bugfixes.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-010, SDD-C-011, SDD-C-015
- Control exception rationale: SDD-C-004 through SDD-C-009 (API/event/Pact contracts) not applicable — all four fixes are shell-script or bash-library-level changes with no API surface or event schema change. SDD-C-012 through SDD-C-014 (frontend/accessibility) not applicable — no user-facing flow.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: bats_or_shell_unit
- Agent execution model: none
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — all fixes target shell scripts and a bash library; no managed-service module changes
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals found — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: Four independently reproducible defects that block STACKIT dev bootstraps (#403), cause silent credential-precedence confusion (#393), break arm64 local cluster image pulls (#402), and mask script metric data while potentially leaking credentials in trace output (#404) are resolved in a single v1.12.5 patch release.
- Success metric: (a) fresh STACKIT dev bootstrap with postgres+opensearch enabled produces no `SecretSyncedError` ESO conditions; (b) `load_env_file_defaults` with `export VAR=val` collision resolves to the semantically correct precedence; (c) `publish_ghcr.sh` produces a multi-arch OCI manifest consumable on both amd64 and arm64 nodes; (d) `start_script_metric_trap` composes with any previously-set EXIT trap without dropping metrics; (e) `run_cmd_env` and `run_with_stdin_secret` are available as credential-safe subprocess invocation paths.

## Normative Requirements

### Issue #403 — ESO dev fallback missing postgres + opensearch keys (P1)

- FR-001 MUST add TF-output-wins guard blocks in `stackit_foundation_seed_runtime_secret.sh` for all 11 keys missing from the `stackit-dev` profile fallback path: `postgres_host`, `postgres_port`, `postgres_database`, `postgres_username`, `postgres_password`, `opensearch_scheme`, `opensearch_host`, `opensearch_host_clean`, `opensearch_port`, `opensearch_username`, `opensearch_password`.
- FR-002 Each guard block MUST write the placeholder value only when the key is absent from `$secret_env_file` (TF-output-wins: when `stackit_runtime_secret_env.py` already wrote the key from real Terraform outputs, the guard MUST NOT overwrite it).
- FR-003 Placeholder default values MUST be overridable via environment variables (`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB_NAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `OPENSEARCH_SCHEME`, `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD`), with in-cluster DNS service names as the built-in defaults (`blueprint-postgres.data.svc.cluster.local`, `blueprint-opensearch.search.svc.cluster.local`).
- FR-004 The guard blocks MUST be placed inside the `tooling_is_execution_enabled` branch of `stackit_foundation_seed_runtime_secret.sh`, after the `uv run python3 ... stackit_runtime_secret_env.py` call that populates TF outputs into `$secret_env_file`.

### Non-Functional Requirements — #403

- NFR-SEC-001 Dev placeholder passwords (`local-dev-postgres-password`, `local-dev-opensearch-password`) MUST only be injected when `BLUEPRINT_PROFILE=stackit-dev`; the guard blocks MUST be unreachable for `stackit-stage` and `stackit-prod` profiles because they live inside the `tooling_is_execution_enabled` branch which is only reached from those profiles via a separate non-dev code path — and per FR-004 the guard blocks MUST NOT duplicate into non-dev branches.

### Issue #393 — load_env_file_defaults export-prefix bypass (P2)

- FR-005 `load_env_file_defaults` in `scripts/lib/shell/bootstrap.sh` MUST strip leading `export ` prefixes (and any intervening whitespace) from variable assignment lines when building the snapshot of variable names before sourcing, and MUST also strip them from the sourced file content (via a temporary stripped copy or `sed` pipe), so that `export VAR=value` and `VAR=value` are treated identically for precedence purposes.
- FR-006 The fix MUST preserve the existing precedence semantics: variables already set in the shell environment before `load_env_file_defaults` is called MUST NOT be overwritten; variables present only in the env file MUST be exported into the shell.

### Non-Functional Requirements — #393

- NFR-SEC-002 After the fix, an operator whose `repo.init.secrets.env` sets `SOME_TOKEN=correct-value` and whose `.env.local` (loaded first by bootstrap.sh) sets `export SOME_TOKEN=stale-value` MUST see `SOME_TOKEN=correct-value` — the secrets file wins because the env var was already set when `load_env_file_defaults` processes `.env.local`.

### Issue #402 — publish_ghcr.sh hardcoded amd64 (P2)

- FR-007 `scripts/bin/platform/apps/publish_ghcr.sh` MUST build and push multi-arch OCI images by default, replacing `docker build` + `docker push` with `docker buildx build --platform "$APPS_GHCR_BUILD_PLATFORMS" --push` in execute mode.
- FR-008 `APPS_GHCR_BUILD_PLATFORMS` MUST default to `linux/amd64,linux/arm64` and MUST be configurable by the operator to restrict to a single arch.
- FR-009 Dry-run log messages MUST reflect the actual `$APPS_GHCR_BUILD_PLATFORMS` value in use.

### Issue #404 — exec.sh foundational gaps (P2)

- FR-010 `start_script_metric_trap` in `scripts/lib/shell/exec.sh` MUST compose with any previously-installed EXIT trap by capturing `trap -p EXIT` output before installing the metric handler, and constructing a compound handler that fires both the existing trap body and the metric emit. The composition MUST handle the case where no prior EXIT trap exists.
- FR-011 MUST add `run_cmd_env` as a new function in `exec.sh`: accepts `KEY=val` prefix arguments followed by `--` separator followed by the command and its args. The trace line (`printf '+ %s\n'`) MUST print the command and args but MUST NOT print the `KEY=val` env pairs or their values.
- FR-012 MUST add `run_with_stdin_secret` as a new function in `exec.sh`: `run_with_stdin_secret TMPFILE CMD [ARGS...]` — redirects CMD stdin from TMPFILE and deletes TMPFILE after the command exits, returning the command exit code. Credential contents in TMPFILE are never exposed as positional arguments.

### Non-Functional Requirements — #404

- NFR-SEC-003 `run_cmd_env` trace output MUST NOT contain the value of any `KEY=val` prefix argument; it MUST be omitted or replaced with a non-revealing indicator.
- NFR-REL-001 `start_script_metric_trap` composition MUST handle both orderings: (a) caller sets EXIT trap before `start_script_metric_trap`, and (b) caller sets EXIT trap after `start_script_metric_trap`.

## Contract Changes (Normative)
- Config/Env contract: `APPS_GHCR_BUILD_PLATFORMS` — new optional env var in `publish_ghcr.sh` (default: `linux/amd64,linux/arm64`). No other new env vars.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `make apps-publish-ghcr` now produces multi-arch OCI images by default; operators requiring single-arch builds MUST set `APPS_GHCR_BUILD_PLATFORMS=linux/amd64`.
- Docs contract: `docs/platform/consumer/troubleshooting.md` — add notes about `APPS_GHCR_BUILD_PLATFORMS` override and ESO dev-fallback placeholder keys.

## Blueprint Upstream Defect Escalation (Normative)
- #403 Temporary workaround path: manually patch `runtime-credentials-source` secret in `security` namespace with the 11 missing keys after bootstrap; replacement trigger: blueprint v1.12.5.
- #393 Temporary workaround path: avoid `export VAR=value` in `.env.local`; use bare assignments only; replacement trigger: blueprint v1.12.5.
- #402 Temporary workaround path: consumer PR sbonoc/dhe-marketplace#120 (`fix/2026-07-09-publish-ghcr-multiarch`); replacement trigger: blueprint v1.12.5.
- #404 Temporary workaround path: consumer PRs sbonoc/dhe-marketplace#125 (credential hygiene) + #126 (EXIT trap composition); replacement trigger: blueprint v1.12.5.
- Workaround review date: 2026-10-01

## Normative Acceptance Criteria

### #403 — ESO fallback
- AC-001 [dev fallback writes all 11 missing keys when TF outputs absent] — verified by T-101, which MUST assert that after invoking the seed script with an empty TF outputs JSON and `BLUEPRINT_PROFILE=stackit-dev`, `$secret_env_file` contains all 11 placeholder key-value pairs with non-empty values.
- AC-002 [TF-output-wins: guard does not overwrite an existing key] — verified by T-102, which MUST assert that when `postgres_host=tf-real-host` is already present in `$secret_env_file` before the guard block runs, the file still contains `postgres_host=tf-real-host` after the guard.

### #393 — export-prefix bypass
- AC-003 [export-prefix bypass closed: pre-set env var wins over export in loaded file] — verified by T-201, which MUST assert that after calling `load_env_file_defaults` with a file containing `export SOME_TOKEN=stale`, a variable pre-set to `correct` in the shell environment retains value `correct`.
- AC-004 [bare assignment is still loaded when var not previously set] — verified by T-202, which MUST assert that a bare `FRESH_VAR=loaded-value` in the env file is exported into the shell when `FRESH_VAR` was not previously set.

### #402 — multi-arch build
- AC-005 [multi-arch platform flag present in execute mode] — verified by T-301, which MUST assert that in execute mode the command invoked to build includes `--platform linux/amd64,linux/arm64` and `--push` (via mock terraform/docker stub or log-line inspection).
- AC-006 [platform overridable via APPS_GHCR_BUILD_PLATFORMS] — verified by T-302, which MUST assert that setting `APPS_GHCR_BUILD_PLATFORMS=linux/amd64` causes the build command to use `--platform linux/amd64` only.

### #404 — exec.sh gaps
- AC-007 [start_script_metric_trap composes with prior EXIT trap] — verified by T-401, which MUST assert that when an EXIT trap is set before `start_script_metric_trap`, both the prior handler body and the metric emit are invoked on script exit.
- AC-008 [run_cmd_env does not print credential values in trace] — verified by T-402, which MUST assert that running `run_cmd_env SECRET=s3cr3t -- echo hello` produces trace output that does NOT contain `s3cr3t`.
- AC-009 [run_with_stdin_secret deletes tmpfile after use] — verified by T-403, which MUST assert that the tmpfile path passed to `run_with_stdin_secret` no longer exists after the helper returns.

## Informative Notes (Non-Normative)
- Context: All four issues were discovered during dhe-marketplace consumer work and STACKIT dev cluster bootstrapping. They represent foundational reliability and security gaps in the blueprint's shell library layer.
- Tradeoffs: Multi-arch buildx (`linux/amd64,linux/arm64`) increases CI build time moderately; this is acceptable for a manual/CI publish step. Composing EXIT traps with `trap -p` is a bash-only construct — the fix is safe within the blueprint's bash-only tooling baseline.
- Clarifications: none

## Explicit Exclusions
- `opensearch_host_clean` as a dedicated TF output key: out of scope — the fallback derives it from `OPENSEARCH_HOST`; adding it to `ALLOWED_OUTPUTS` and Terraform is a separate enhancement.
- Full precedence-chain documentation overhaul (#393 option 3): out of scope for this patch; a follow-up docs-only PR can add it.
- Removing `.env.local` as a mechanism (#393): out of scope — would be a breaking change.
- Redacting credentials passed as positional args to `run_cmd` via inspection: out of scope — `run_cmd_env` provides the safe alternative; modifying `run_cmd` would break existing call sites.

## Potential Deferred Proposals
- Document the full `.env.local` > `repo.init.secrets.env` precedence chain with explicit warnings in `repo.init.secrets.example.env` and `blueprint/contract.yaml`; low urgency after the export-bypass is closed.
- `run_cmd` credential-argument lint rule: add a shellcheck or CI rule flagging `run_cmd ... $SECRET_VAR` patterns; surfaces when CI hardening is next in scope.
- `opensearch_host_clean` as a derived Terraform local or output: surfaces when any OpenSearch Terraform work is next in scope.
