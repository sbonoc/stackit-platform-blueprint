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
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `RABBITMQ_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `RABBITMQ_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions managed RabbitMQ through `stackit_rabbitmq_instance` plus `stackit_rabbitmq_credential`, and wrappers read terraform outputs into the runtime contract.
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
