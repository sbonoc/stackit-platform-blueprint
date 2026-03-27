# RabbitMQ Module (Optional)

## Purpose
Provision RabbitMQ for transaction state/event propagation and async notifications.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `RABBITMQ_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `RABBITMQ_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions managed RabbitMQ through `stackit_rabbitmq_instance` plus `stackit_rabbitmq_credential`, and wrappers read terraform outputs into the runtime contract.
- `local-*` profiles: Helm chart (`bitnami/rabbitmq`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/rabbitmq/values.yaml`.

## Enable
```bash
export RABBITMQ_ENABLED=true
```

## Required Inputs
- `RABBITMQ_INSTANCE_NAME`

## Optional Inputs
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_VERSION`
- `RABBITMQ_PLAN_NAME`

## Commands
- `make infra-rabbitmq-plan`
- `make infra-rabbitmq-apply`
- `make infra-rabbitmq-smoke`
- `make infra-rabbitmq-destroy`

## Outputs
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_USERNAME`
- `RABBITMQ_PASSWORD`
- `RABBITMQ_URI`

`RABBITMQ_HOST` resolves to the in-cluster Helm service host for local profiles and to provider-managed broker coordinates for `stackit-*` profiles. In dry-run `stackit-*` flows, the wrappers emit deterministic `.stackit.invalid` placeholders until terraform outputs exist.
