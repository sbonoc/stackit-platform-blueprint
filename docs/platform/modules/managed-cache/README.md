# Managed Cache (Redis)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision a managed Redis cache — STACKIT Managed Redis on cloud lanes, bitnami/redis via Helm on the local lane.
- Enable flag: `MANAGED_CACHE_ENABLED` (default: `false`)
- Required inputs:
  - `MANAGED_CACHE_INSTANCE_NAME`
- Make targets:
  - `infra-managed-cache-plan`
  - `infra-managed-cache-apply`
  - `infra-managed-cache-smoke`
  - `infra-managed-cache-destroy`
- Outputs:
  - `MANAGED_CACHE_HOST`
  - `MANAGED_CACHE_PORT`
  - `MANAGED_CACHE_USERNAME`
  - `MANAGED_CACHE_PASSWORD`
  - `MANAGED_CACHE_URI`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

Optional blueprint module that provisions a managed Redis cache: STACKIT Managed Redis on cloud lanes and bitnami/redis via Helm on the local lane.

## Activation

Set `MANAGED_CACHE_ENABLED=true` in your environment before running `make infra-managed-cache-apply`.

The flag defaults to `false` — existing consumers are completely unaffected when the module is disabled.

## Make Targets

| Target | Description |
|---|---|
| `make infra-managed-cache-plan` | Plan managed cache resources |
| `make infra-managed-cache-apply` | Provision Redis and write runtime state |
| `make infra-managed-cache-smoke` | Validate URI scheme and runtime state |
| `make infra-managed-cache-destroy` | Destroy managed cache resources |

## Inputs

| Variable | Required | Default | Description |
|---|---|---|---|
| `MANAGED_CACHE_ENABLED` | Yes | `false` | Enable managed cache provisioning |
| `MANAGED_CACHE_INSTANCE_NAME` | Yes | `marketplace-managed-cache` | STACKIT Redis instance name (STACKIT lane) |
| `MANAGED_CACHE_PASSWORD` | No | `managed-cache-password` | Redis password (local lane) |
| `MANAGED_CACHE_PORT` | No | `6379` | Redis port (local lane) |
| `MANAGED_CACHE_NAMESPACE` | No | `managed-cache` | Kubernetes namespace (local lane) |
| `MANAGED_CACHE_HELM_RELEASE` | No | `blueprint-managed-cache` | Helm release name (local lane) |
| `MANAGED_CACHE_HELM_CHART` | No | `bitnami/redis` | Helm chart (local lane) |
| `MANAGED_CACHE_HELM_CHART_VERSION` | No | `25.5.3` | Helm chart version pin (local lane) |

## Outputs

After `make infra-managed-cache-apply` the runtime state is written to `artifacts/infra/managed_cache_runtime.env`:

| Key | Description |
|---|---|
| `profile` | Blueprint profile used during apply |
| `stack` | Active stack name |
| `host` | Redis host |
| `port` | Redis port |
| `uri` | Redis URI (`redis://:<password>@<host>:<port>/0`) |

**Security**: `password` is never written to the state file (NFR-SEC-001). Retrieve it at runtime via `managed_cache_password()`.

## URI Format

Both lanes produce URIs matching `redis://:.+@.+:[0-9]+/0`:

- **Local lane**: `redis://:<password>@blueprint-managed-cache.managed-cache.svc.cluster.local:6379/0`
- **STACKIT lane**: read directly from `stackit_redis_credential.uri` foundation output

## Username

STACKIT lane provides a `username` credential attribute. The local lane (bitnami/redis standalone) is password-only — `managed_cache_username()` returns an empty string on the local lane.

## Network ACL (STACKIT lane)

`managed_cache_sgw_acl` (a `list(string)` TF variable) is automatically merged with the SKE cluster's egress address ranges at apply time — the same auto-alignment pattern used by the postgres module. The merged list is passed to `stackit_redis_instance.parameters.sgw_acl`. No open-world `0.0.0.0/0` sole entry is permitted. Supply explicit CIDR ranges via `managed_cache_sgw_acl` when `ske_enabled=false`.

## Smoke

`make infra-managed-cache-smoke` validates:
1. `MANAGED_CACHE_URI` is non-empty
2. URI starts with `redis://`

## Rollback

Disable the module (`MANAGED_CACHE_ENABLED=false`) or run `make infra-managed-cache-destroy`. The foundation TF workspace removes the Redis instance and credential.

## Relationship to Issue #172

Credential delivery to applications (ESO-based `ExternalSecret` for `MANAGED_CACHE_PASSWORD`) is tracked under issue #172. This module provisions the Redis instance and exposes the connection details — app-level secret injection is a separate concern.
