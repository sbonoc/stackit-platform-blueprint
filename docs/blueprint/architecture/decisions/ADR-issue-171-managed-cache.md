# ADR — issue-171-managed-cache: Managed Cache Optional Module (STACKIT Redis + bitnami/redis)

**Status:** proposed
**Date:** 2026-05-27
**ADR technical decision sign-off:** pending

## Context

No blueprint module exists for managed Redis/cache. Consumer use cases — server-side session store (Keycloak JWT overflow), rate-limiting counter store, inbox idempotency cache, and Postal email backing store (issue #172) — currently require bespoke per-consumer Redis wiring with no shared secret contract, no ESO integration, and no consistent env-var naming.

The blueprint already provides the pattern for optional managed-service modules via rabbitmq, opensearch, and postgres. This ADR covers the architectural decisions for adding `managed-cache` following the same pattern.

## Decision 1: Local lane — bitnami/redis Helm chart (Option A)

**Decision:** Use the `bitnami/redis` Helm chart for the local lane, with Helm release name `blueprint-managed-cache` in the `managed-cache` namespace.

**Rationale:**

| Option | Pros | Cons |
|---|---|---|
| A — bitnami/redis (selected) | Consistent with bitnami/postgresql, bitnami/rabbitmq, bitnami/opensearch local lane pattern; well-maintained; password auth built-in | Subject to same bitnami deprecation risk as postgres (issue #324) |
| B — custom Redis via official `redis` Docker image + manual K8s manifests | No bitnami dependency | Significant setup overhead; no precedent in blueprint; maintenance burden |

bitnami/redis is the established local-lane pattern. The bitnami deprecation concern is tracked under issue #324 for the postgres module; this module follows the same migration scope when that lands.

## Decision 2: STACKIT lane — foundation-contract execution model

**Decision:** The managed-cache TF module is invoked by the foundation TF workspace via `resolve_optional_module_execution`, not called directly. A `managed_cache_enabled` boolean variable (default `false`) in the foundation workspace guards the module call.

**Rationale:** All optional managed-service modules in the blueprint follow this pattern (rabbitmq, postgres, opensearch). Direct module invocation would require a separate TF workspace with its own state, which creates credential management complexity. Foundation-contract execution means a single apply call produces all outputs via the already-authenticated foundation workspace.

## Decision 3: STACKIT Redis resource — stackit_redis_instance + stackit_redis_credential (Option A, pending verification)

**Decision:** Use `stackit_redis_instance` and `stackit_redis_credential` TF resources from the STACKIT Terraform provider. Credential attributes: `host`, `port`, `password`, `uri`.

**Rationale:** The STACKIT provider follows a consistent naming pattern across managed services. The expected resource names follow the same convention as `stackit_rabbitmq_instance` / `stackit_rabbitmq_credential` and `stackit_postgresql_instance` / `stackit_postgresql_credential`. Redis has no `username` field — auth is password-only.

**Open question (Q-1 — blocking Slice 3):** The resource names must be verified against the live provider schema (`terraform providers schema -json` for provider version `= 0.88.0`) before writing TF code. Incorrect resource names block `terraform apply`. Slice 3 implementation is gated on this resolution.

## Decision 4: Credential delivery — shell lib abstraction + ESO ExternalSecret

**Decision:** A shell lib (`managed_cache.sh`) exposes `managed_cache_uri()`, `managed_cache_host()`, `managed_cache_port()`, `managed_cache_password()` as the credential contract abstraction. Consumer workloads receive credentials via ESO ExternalSecret referencing a K8s Secret created by the apply script.

**Rationale:** Same pattern as rabbitmq and opensearch — shell lib isolates callers from lane differences; ESO ExternalSecret is the standard blueprint credential delivery mechanism. The URI is the canonical consumer credential (`redis://:<password>@<host>:<port>/0`).

## Decision 5: Password excluded from state file

**Decision:** `managed_cache_apply.sh` writes `managed_cache_runtime.env` with keys `profile`, `stack`, `host`, `port`, `uri` only. `MANAGED_CACHE_PASSWORD` MUST NOT be written to the state file.

**Rationale:** SDD-C-009 (credential non-persistence). On STACKIT, the password is read at runtime from the sensitive foundation TF output via `managed_cache_password()` → `stackit_foundation_output_value_or_default`. On local lane, it is read from the in-process shell environment. Neither path requires the password to be persisted to disk in cleartext.

## Decision 6: Network ACL — SKE egress CIDR alignment

**Decision:** The `stackit_redis_instance` TF resource MUST declare a network ACL aligned with SKE egress CIDR ranges. Open-world access (`0.0.0.0/0`) MUST NOT be the sole ACL entry.

**Rationale:** NFR-SEC-002. Same ACL policy as postgres (see blueprint postgres TF module). The STACKIT Managed Redis instance should only accept connections from the SKE cluster nodes, not from arbitrary internet addresses.

## Consequences

- Running the apply target with `MANAGED_CACHE_ENABLED=true` on a STACKIT profile provisions a Redis instance via the foundation TF workspace and writes `managed_cache_runtime.env`.
- `MANAGED_CACHE_ENABLED=false` (the default) means zero impact on existing consumers — no new TF resources, no new K8s objects, no new make targets invoked automatically.
- `platform-email` module (issue #172) can depend on `MANAGED_CACHE_URI` as its Redis backing store once this module is merged.
- bitnami/redis local lane is subject to the same migration scope as bitnami/postgresql when issue #324 lands.
- Q-1 resolution is required before any `terraform apply` on a STACKIT profile — implementation is deliberately blocked at plan time.
