# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 1
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 1
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-248-postgres-module.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-015: No app onboarding make-target contract changes — this work item affects only infra module wrappers, not app delivery workflows.
  - SDD-C-018: No blueprint upstream defect escalation — this is a blueprint-internal implementation.
  - SDD-C-022: Not applicable — no HTTP route handlers or new API endpoints in scope.
  - SDD-C-023: Not applicable — no filter or payload-transform logic in scope.
  - SDD-C-024: Not applicable — no pre-PR smoke/curl/deterministic-check findings to translate; no reproducible failures exist at intake time.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: local lane uses Bitnami postgresql Helm chart (dev-only, not production-managed); this is the established blueprint pattern for local lane provisioning
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Elevate the postgres module from partial scaffold to production-grade optional module: correct execution class (`fallback_runtime` on local lane), Secret-backed credentials (no plaintext in rendered Helm values), working STACKIT Terraform standalone module (`stackit_postgresflex_*` resources), and complete module documentation with verified test coverage.
- Success metric: `pytest tests/infra/modules/postgres/ -v` passes (≥ 20 assertions); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` passes; local lane applies with `auth.existingSecret` and no plaintext credentials in the rendered values artifact.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 MUST correct the local-lane execution class in `scripts/lib/infra/module_execution.sh` from `provider_backed` to `fallback_runtime` for both `postgres:plan|apply` and `postgres:destroy` routing blocks, matching the opensearch and object-storage convention.
- FR-002 MUST add three Secret lifecycle functions to `scripts/lib/infra/postgres.sh`: `postgres_credential_secret_name()`, `postgres_reconcile_runtime_secret()`, and `postgres_delete_runtime_secret()`; `postgres_render_values_file()` MUST NOT pass plaintext `POSTGRES_USER` or `POSTGRES_PASSWORD` as template bindings.
- FR-003 MUST update `infra/local/helm/postgres/values.yaml` to use `auth.existingSecret: {{POSTGRES_CREDENTIAL_SECRET_NAME}}` in place of `auth.username`/`auth.password` so no plaintext credentials appear in the rendered Helm values artifact.
- FR-004 MUST update `scripts/bin/infra/postgres_apply.sh` (`helm)` case) to call `postgres_reconcile_runtime_secret` before `run_helm_upgrade_install`; MUST update `scripts/bin/infra/postgres_destroy.sh` (`helm)` case) to call `postgres_delete_runtime_secret` after `run_helm_uninstall`; destroy MUST pass `--ignore-not-found` to `run_helm_uninstall` and `postgres_delete_runtime_secret` MUST tolerate a missing Secret.
- FR-005 MUST implement the STACKIT standalone Terraform module at `infra/cloud/stackit/terraform/modules/postgres/` with three resources: `stackit_postgresflex_instance`, `stackit_postgresflex_user`, and `stackit_postgresflex_database`; the module MUST mirror the ACL policy (`forbid_default_open_world`) enforced in the foundation layer.
- FR-006 MUST write a runtime state file on apply with all six contract-declared output keys: `host`, `port`, `database`, `username`, `password`, `dsn`; `dsn` MUST use the `postgresql://` scheme.
- FR-007 MUST add explicit smoke validations beyond DSN format: `host` MUST be non-empty, `port` MUST be non-empty, `database` MUST be non-empty in the `postgres_smoke.sh` state file checks.
- FR-008 MUST update `scripts/bin/infra/bootstrap.sh` (`postgres)` case) to use `POSTGRES_CREDENTIAL_SECRET_NAME` as a template binding instead of plaintext `POSTGRES_USER`/`POSTGRES_PASSWORD`; the bootstrap template `scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml` MUST use `auth.existingSecret: {{POSTGRES_CREDENTIAL_SECRET_NAME}}`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST NOT expose plaintext credentials in rendered Helm values or bootstrap templates; the K8s Secret `blueprint-postgres-auth` created by `postgres_reconcile_runtime_secret` MUST be the sole credential delivery path for the local lane.
- NFR-OBS-001 All four scripts (`postgres_{plan,apply,smoke,destroy}.sh`) MUST emit metric events via the existing `start_script_metric_trap` framework call; no new metric emitters are required beyond the framework guarantee.
- NFR-REL-001 `postgres_destroy.sh` MUST be idempotent: `run_helm_uninstall` with `--ignore-not-found` and `postgres_delete_runtime_secret` tolerating a missing Secret; re-running destroy when resources are already absent MUST exit 0.
- NFR-OPS-001 The runtime state file MUST contain all six contract output keys; `postgres_smoke.sh` MUST validate `host`, `port`, `database`, and the `dsn` prefix.
- NFR-A11Y-001 N/A — no UI component; postgres is an infrastructure module with no browser-facing surface.

## Open Questions

> **[NEEDS CLARIFICATION]** Q-1: State file key naming alignment. `module.contract.yaml` lists `POSTGRES_DB_NAME` and `POSTGRES_USER` as output env var names, but the existing `postgres_apply.sh` runtime state file uses keys `database` and `username`. These two naming conventions diverge. Which should be canonical?
>
> **Options:**
> - **A)** Keep state file keys as-is (`database`, `username`, `dsn`) and treat them as the canonical runtime state keys; module.contract.yaml `POSTGRES_DB_NAME`/`POSTGRES_USER` remain as the ESO-synced env var names. No breaking change to runtime artifacts. (agent recommendation)
> - **B)** Rename state file keys to `db_name`, `user`, `dsn` to strictly match the module.contract.yaml output env var names by stripping the `POSTGRES_` prefix. Breaking change to any consumer reading the raw state file.
>
> **Agent recommendation:** Option A — the runtime state key naming convention is not required to match the env var prefix-stripped name (opensearch similarly uses `uri` for `OPENSEARCH_URI`); the existing `database`/`username` keys are already established in the apply script and have no known consumers directly parsing the raw state file. Changing them would be a risky breaking change with no functional benefit for the current consumer set.

## Normative Option Decision
- Option A: Implement all missing pieces additively: execution class fix, secret lifecycle addition, Terraform module, smoke hardening, tests, docs. No breaking changes to env var names or state file schema.
- Option B: Simultaneously rename output env vars (`POSTGRES_DATABASE`, `POSTGRES_USERNAME`, `POSTGRES_URI`) to align with issue #248 wording, rename state file keys, and update all callers.
- Selected option: OPTION_A
- Rationale: The module.contract.yaml output names (`POSTGRES_DB_NAME`, `POSTGRES_USER`, `POSTGRES_DSN`) are already confirmed correct by the issue-118-137 spec. Option B would introduce breaking changes across ESO, runtime scripts, and consumer downstream repos for cosmetic alignment. All functional gaps can be closed additively.

## Contract Changes (Normative)
- Config/Env contract: `POSTGRES_CREDENTIAL_SECRET_NAME` added as a new internal template variable in Helm values rendering (not exposed to consumers); no consumer-visible env var changes.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `infra-postgres-{plan,apply,smoke,destroy}` targets unchanged; no new targets.
- Module execution contract: `OPTIONAL_MODULE_EXECUTION_CLASS` changes from `provider_backed` to `fallback_runtime` for the local lane; STACKIT lane class unchanged (`provider_backed`). `tests/infra/test_tooling_contracts.py` gains two new assertions for postgres local and STACKIT class resolution.
- Docs contract: `docs/platform/modules/postgres/README.md` completed with both-lanes usage, credentials section, smoke section, and destroy section.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 MUST: Local apply (`helm)` case) calls `postgres_reconcile_runtime_secret` before `run_helm_upgrade_install` — verified by unit test.
- AC-002 MUST: `infra/local/helm/postgres/values.yaml` uses `auth.existingSecret` and contains no `auth.username` or `auth.password` fields — verified by unit test.
- AC-003 MUST: `postgres_render_values_file()` does NOT bind `POSTGRES_USER` or `POSTGRES_PASSWORD` as template variables — verified by unit test.
- AC-004 MUST: `postgres_destroy.sh` calls `postgres_delete_runtime_secret` after uninstall — verified by unit test.
- AC-005 MUST: `module_execution.sh` local lane for `postgres:plan|apply|destroy` uses `fallback_runtime` class — verified by tooling contract test.
- AC-006 MUST: STACKIT lane for `postgres:plan|apply|destroy` uses `provider_backed` class — verified by tooling contract test.
- AC-007 MUST: STACKIT Terraform module declares `stackit_postgresflex_instance`, `stackit_postgresflex_user`, `stackit_postgresflex_database` resources — verified by unit test.
- AC-008 MUST: Terraform module `variables.tf` binds all contract inputs (`postgres_instance_name`, `postgres_db_name`, `postgres_username`, `postgres_version`) — verified by unit test.
- AC-009 MUST: Terraform module `outputs.tf` exposes all contract output keys (`postgres_host`, `postgres_port`, `postgres_username`, `postgres_password`, `postgres_database`) — verified by unit test.
- AC-010 MUST: Smoke passes with valid runtime state containing all six keys — verified by unit test.
- AC-011 MUST: Smoke fails when `dsn` does not start with `postgresql://` — verified by unit test.
- AC-012 MUST: Smoke fails when `host` is empty — verified by unit test.
- AC-013 MUST: Contract test confirms runtime state has all six declared output keys (`host`, `port`, `database`, `username`, `password`, `dsn`) — verified by contract test.
- AC-014 MUST: Bootstrap template uses `{{POSTGRES_CREDENTIAL_SECRET_NAME}}` and contains no `{{POSTGRES_USER}}` or `{{POSTGRES_PASSWORD}}` placeholders — verified by unit test.

## Informative Notes (Non-Normative)
- Context: The postgres module has the most pre-existing scaffold among the in-scope modules: all four bin scripts (`postgres_{plan,apply,smoke,destroy}.sh`), a partial `postgres.sh` lib, and a Helm values seed file already exist. The main gaps are the execution class, Secret-backed credential pattern (matching what object-storage/opensearch use), the STACKIT Terraform module, and test coverage.
- Tradeoffs: Using `auth.existingSecret` means the K8s Secret must exist before the pod starts; `postgres_reconcile_runtime_secret` ensures it is created before `run_helm_upgrade_install`. If apply fails mid-way the Secret exists but the chart does not — idempotent re-run resolves this.
- Clarifications: The STACKIT provider resource name is `stackit_postgresflex_*` (not `stackit_postgresql_*`) — confirmed from the foundation Terraform layer which already provisions postgres this way.

## Explicit Exclusions
- High-availability replica configuration for the STACKIT lane (configurable via `stackit_postgresflex_instance.replicas` but defaulted to 1 for cost; a separate work item covers multi-replica scenarios).
- Per-consumer database or schema isolation (handled at consumer-side; module provisions a single database as declared in `module.contract.yaml`).
- SSL/TLS termination configuration in the local lane (Docker Desktop K8s; consumers connect via in-cluster service DNS; TLS required only on STACKIT lane where the provider handles it).
- Connection pooling or PgBouncer integration (deferred to a separate work item when a consumer requires it).
