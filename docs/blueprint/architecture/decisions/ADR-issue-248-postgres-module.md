# ADR: Issue #248 — Postgres Module Implementation (Dual-Lane)

- **Status**: approved
- **ADR technical decision sign-off**: approved
- **Date**: 2026-05-07
- **Issue**: #248
- **Work item**: `specs/2026-05-07-issue-248-postgres-module/`

## Context

The `infra/cloud/stackit/terraform/modules/postgres/main.tf` is a 7-line stub. Unlike object-storage and opensearch (which started from a minimal scaffold), the postgres module has the most pre-existing scaffold among the in-scope modules: all four bin scripts (`postgres_{plan,apply,smoke,destroy}.sh`), a partially implemented `postgres.sh` lib, and a Helm values seed file already exist. However, four correctness gaps remain:

1. The local-lane execution class is `provider_backed` (should be `fallback_runtime`, matching opensearch/object-storage/rabbitmq convention).
2. Helm values pass plaintext `auth.username`/`auth.password` instead of using `auth.existingSecret` (security gap).
3. The STACKIT Terraform module is a stub — no `stackit_postgresflex_*` resources declared.
4. No automated tests exist.

The STACKIT provider uses `stackit_postgresflex_instance`, `stackit_postgresflex_user`, and `stackit_postgresflex_database` resources — confirmed from the foundation Terraform layer which already provisions postgres this way for the core platform and Keycloak.

## Decisions

### D-1: Additive standalone Terraform module mirroring foundation pattern

Implement `infra/cloud/stackit/terraform/modules/postgres/` as a standalone module that mirrors the three foundation resources (`stackit_postgresflex_instance`, `stackit_postgresflex_user`, `stackit_postgresflex_database`). The foundation layer continues to manage its own inline resources; the standalone module is available for isolated use and is the implementation target for FR-005.

The module enforces the same ACL constraint as the foundation: `postgres_acl` must be non-empty or `ske_enabled` must be true. A `lifecycle { create_before_destroy = true }` block is added to the instance resource. The database resource uses `depends_on = [stackit_postgresflex_user.postgres]` to ensure the owner user exists before the database is created.

**Rejected alternative:** Have the foundation call the standalone module — rejected due to Terraform state migration risk with no active consumer driver for the refactor.

### D-2: Secret-backed credentials for local lane (matching opensearch/object-storage pattern)

Replace `auth.username`/`auth.password` plaintext fields in the Bitnami postgresql Helm values with `auth.existingSecret` referencing Kubernetes Secret `blueprint-postgres-auth`. The Secret is reconciled on every apply via `apply_optional_module_secret_from_literals` before `run_helm_upgrade_install`. The Secret key is `password` (confirmed from Bitnami postgresql chart templates).

`postgres_render_values_file()` is updated to remove plaintext credential bindings and add `POSTGRES_CREDENTIAL_SECRET_NAME`. The bootstrap template and `bootstrap.sh` `postgres)` case are updated consistently.

**Rejected alternative:** Keep plaintext credentials in values — rejected due to NFR-SEC-001 and consistency with the established pattern.

### D-3: Execution class — `fallback_runtime` for local lane

Change `OPTIONAL_MODULE_EXECUTION_CLASS` from `provider_backed` to `fallback_runtime` for both `postgres:plan|apply` and `postgres:destroy` local-lane routing in `module_execution.sh`. The Bitnami postgresql Helm chart is a development approximation, not the STACKIT-managed PostgreSQL Flex service — `fallback_runtime` is the correct classification. STACKIT lane remains `provider_backed`.

**Rejected alternative:** Keep `provider_backed` — rejected as semantically incorrect and inconsistent with opensearch, object-storage, and rabbitmq which all use `fallback_runtime` for their local-lane Helm charts.

### D-4: State file key naming — rename to `db_name` and `user` (Q-1 resolved 2026-05-07)

The existing `postgres_apply.sh` wrote state keys `database` and `username`. The `module.contract.yaml` lists output names `POSTGRES_DB_NAME` and `POSTGRES_USER`. After owner review (PR #251 comment 2026-05-07), the decision is to rename state file keys to `db_name` and `user` by strictly applying the prefix-strip convention (`POSTGRES_DB_NAME` → `db_name`, `POSTGRES_USER` → `user`), consistent with the opensearch and object-storage modules.

This is a breaking change to `artifacts/infra/postgres_runtime.env` key names. The affected callers within this work item are `postgres_apply.sh` (write), `postgres_smoke.sh` (read/validate), and `test_contract.py` (assert). Downstream consumers reading the raw state file directly MUST update their key references; consumers relying on ESO-synced env vars (`POSTGRES_DB_NAME`, `POSTGRES_USER`) are unaffected.

**Rejected alternative:** Keep current keys (`database`, `username`) — rejected because it creates a non-derivable exception to the established prefix-strip convention; alignment is cheaper now (no passing test suite exists to protect) than later.

## Consequences

- Postgres local lane correctly classified as `fallback_runtime` in observability/routing, consistent with all other local Helm chart modules.
- K8s Secret `blueprint-postgres-auth` is the credential delivery path for local lane; no plaintext credentials appear in Helm values or rendered artifacts.
- STACKIT standalone Terraform module enables isolated postgres provisioning outside the foundation deployment pattern.
- Runtime state file keys `db_name` and `user` follow the strict prefix-strip convention; consumers reading raw state files must update key references from `database`→`db_name` and `username`→`user`.
