# RabbitMQ Module (Optional)

## Purpose
Provision RabbitMQ for transaction state/event propagation and async notifications.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `RABBITMQ_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `RABBITMQ_ENABLED=true`.
- `stackit-*` profiles: runtime reconciliation through ArgoCD optional manifest `infra/gitops/argocd/optional/${ENV}/rabbitmq.yaml`.
- `local-*` profiles: Helm chart (`bitnami/rabbitmq`) using `infra/local/helm/rabbitmq/values.yaml`.

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
