# Neo4j Module (Optional)

## Purpose
Deploy Neo4j and expose canonical graph connection values to runtime consumers.

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `NEO4J_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `NEO4J_ENABLED=true`.
- Provision/deploy intent is expressed through ArgoCD optional manifests:
  - `infra/gitops/argocd/optional/<env>/neo4j.yaml`
- Local Helm values are maintained in:
  - `infra/local/helm/neo4j/values.yaml`

## Enable
Set:

```bash
export NEO4J_ENABLED=true
```

## Required Inputs
- `NEO4J_AUTH_USERNAME`
- `NEO4J_AUTH_PASSWORD`

## Commands
- `make infra-neo4j-plan`
- `make infra-neo4j-apply`
- `make infra-neo4j-deploy`
- `make infra-neo4j-smoke`
- `make infra-neo4j-destroy`

## Outputs
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`
