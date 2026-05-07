# RabbitMQ Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision RabbitMQ for transactional and notification event flows.
- Enable flag: `RABBITMQ_ENABLED` (default: `false`)
- Required inputs:
  - `RABBITMQ_INSTANCE_NAME`
- Make targets:
  - `infra-rabbitmq-plan`
  - `infra-rabbitmq-apply`
  - `infra-rabbitmq-smoke`
  - `infra-rabbitmq-destroy`
- Outputs:
  - `RABBITMQ_HOST`
  - `RABBITMQ_PORT`
  - `RABBITMQ_USERNAME`
  - `RABBITMQ_PASSWORD`
  - `RABBITMQ_URI`
  - `RABBITMQ_VHOST`
  - `RABBITMQ_MANAGEMENT_URL`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `RABBITMQ_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `RABBITMQ_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions managed RabbitMQ through `stackit_rabbitmq_instance` plus `stackit_rabbitmq_credential`, and wrappers read terraform outputs into the runtime contract.
  - `RABBITMQ_VERSION` defaults to `4.0` and `RABBITMQ_PLAN_NAME` defaults to `stackit-rabbitmq-2.4.10-replica`; both can be overridden explicitly.
  - Runtime artifacts resolve provider-generated host/port/username/password/uri/management_url outputs after apply; dry-run mode keeps deterministic placeholders.
- `local-*` profiles: Helm chart (`bitnami/rabbitmq`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/rabbitmq/values.yaml`.
  - RabbitMQ managed-service major family: `4.0` (derived from `RABBITMQ_LOCAL_IMAGE_TAG` in `scripts/lib/infra/versions.sh`; validated by `make quality-docs-lint`).
  - Local chart/image pins stay on the latest stable Bitnami chart and image line matching the managed-service family.
  - The pinned fallback image uses `docker.io/bitnamilegacy/rabbitmq`; despite the registry namespace, the pinned tag stays on the latest stable supported image line while remaining multi-arch for both amd64 CI nodes and arm64 Docker Desktop clusters.

## Optional Inputs
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_VERSION`
- `RABBITMQ_PLAN_NAME`

`RABBITMQ_HOST` resolves to the in-cluster Helm service host for local profiles and to provider-managed broker coordinates for `stackit-*` profiles. In dry-run `stackit-*` flows, the wrappers emit deterministic `.stackit.invalid` placeholders until terraform outputs exist.

## Credentials

Credentials are delivered via a Kubernetes Secret named `blueprint-rabbitmq-auth` (Secret key: `rabbitmq-password`). No plaintext credentials appear in rendered Helm values or bootstrap templates.

**Local lane apply flow:**
1. `rabbitmq_reconcile_runtime_secret` creates or updates Secret `blueprint-rabbitmq-auth` in namespace `messaging` with the value of `RABBITMQ_PASSWORD` before the Helm upgrade runs.
2. The Bitnami rabbitmq chart mounts the Secret via `auth.existingPasswordSecret: blueprint-rabbitmq-auth`.
3. `rabbitmq_delete_runtime_secret` removes the Secret on destroy.

**STACKIT lane:** credentials are provider-generated; no pre-provisioned Secret is required.

## Vhost

Both lanes use the RabbitMQ default vhost `/`. This is a constant value — the STACKIT provider credential does not expose a vhost attribute, and per-consumer vhost customisation is out of scope for this module.

The `rabbitmq_vhost()` shell function returns `/` on both lanes. The runtime state file records the key `vhost=/`.

## Management URL

The RabbitMQ management dashboard URL is exposed as `RABBITMQ_MANAGEMENT_URL`.

- **Local lane**: constructed as `http://<helm-release-host>:15672` (Bitnami management plugin default port).
- **STACKIT lane**: read from the `rabbitmq_management_url` foundation output, which reflects `stackit_rabbitmq_credential.management` from the provider.

## Standalone STACKIT Terraform Module

A standalone Terraform module is available at `infra/cloud/stackit/terraform/modules/rabbitmq/` for isolated RabbitMQ provisioning outside the foundation deployment pattern.

Resources declared: `stackit_rabbitmq_instance` (with `lifecycle { create_before_destroy = true }`), `stackit_rabbitmq_credential`.

Key variables:

| Variable | Description | Default |
|---|---|---|
| `stackit_project_id` | STACKIT project ID | required |
| `stackit_region` | STACKIT region | `eu01` |
| `rabbitmq_instance_name` | Instance name | required |
| `rabbitmq_version` | RabbitMQ major version | `4.0` |
| `rabbitmq_plan_name` | STACKIT service plan | `stackit-rabbitmq-2.4.10-replica` |

Key outputs: `rabbitmq_host`, `rabbitmq_port`, `rabbitmq_username`, `rabbitmq_password`, `rabbitmq_uri`, `rabbitmq_management_url`.

Validate: `terraform validate` from `infra/cloud/stackit/terraform/modules/rabbitmq/`.

## Runtime State

Apply writes `artifacts/infra/rabbitmq_runtime.env` with all seven contract output keys:

| Key | Description |
|---|---|
| `host` | RabbitMQ broker host |
| `port` | RabbitMQ broker port |
| `username` | Runtime username |
| `password` | Runtime password |
| `uri` | `amqp[s]://username:password@host:port` |
| `vhost` | RabbitMQ vhost (constant `/`) |
| `management_url` | Management dashboard URL |

State file keys follow the strict prefix-strip convention: `RABBITMQ_MANAGEMENT_URL` → `management_url`. Consumers reading `artifacts/infra/rabbitmq_runtime.env` directly must use the stripped key names.

## Smoke Checks

`make infra-rabbitmq-smoke` validates the runtime state file. Checks performed:

- `uri` starts with `amqp://` or `amqps://`
- `host` is non-empty
- `port` is non-empty
- `vhost` is non-empty
- `management_url` is non-empty

Smoke writes `artifacts/infra/rabbitmq_smoke.env` with `status=passed` on success.

## Destroy

`make infra-rabbitmq-destroy` removes the Helm release (local lane) or delegates to the foundation Terraform layer (STACKIT lane) and removes all runtime state files.

**Local lane destroy sequence:**
1. `run_helm_uninstall` (idempotent — tolerates missing release via `--ignore-not-found`)
2. `rabbitmq_delete_runtime_secret` (idempotent — tolerates missing Secret)
3. `remove_state_files_by_prefix rabbitmq_`

Re-running destroy when resources are already absent exits 0.
