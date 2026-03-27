# RabbitMQ Module (Optional)

## Purpose
Provision RabbitMQ for transaction state/event propagation and async notifications.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `RABBITMQ_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `RABBITMQ_ENABLED=true`.
- `stackit-*` profiles: module-specific ArgoCD `Application` reconciles `bitnami/rabbitmq` from `infra/gitops/argocd/optional/${ENV}/rabbitmq.yaml`, with runtime credentials seeded as a Kubernetes Secret.
- `local-*` profiles: Helm chart (`bitnami/rabbitmq`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/rabbitmq/values.yaml`.

## Enable
```bash
export RABBITMQ_ENABLED=true
```

## Required Inputs
- `RABBITMQ_INSTANCE_NAME`
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`

## Commands
- `make infra-rabbitmq-plan`
- `make infra-rabbitmq-apply`
- `make infra-rabbitmq-smoke`
- `make infra-rabbitmq-destroy`

## Outputs
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_URI`

`RABBITMQ_HOST` resolves to the in-cluster service host backed by the Helm release in both local and STACKIT fallback-runtime profiles.
