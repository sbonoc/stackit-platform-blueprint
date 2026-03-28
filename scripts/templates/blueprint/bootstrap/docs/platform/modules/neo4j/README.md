# Neo4j Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Deploy Neo4j graph database and publish canonical runtime connection contract.
- Enable flag: `NEO4J_ENABLED` (default: `false`)
- Required inputs:
  - `NEO4J_AUTH_USERNAME`
  - `NEO4J_AUTH_PASSWORD`
- Make targets:
  - `infra-neo4j-plan`
  - `infra-neo4j-apply`
  - `infra-neo4j-deploy`
  - `infra-neo4j-smoke`
  - `infra-neo4j-destroy`
- Outputs:
  - `NEO4J_URI`
  - `NEO4J_USERNAME`
  - `NEO4J_PASSWORD`
  - `NEO4J_DATABASE`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `NEO4J_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `NEO4J_ENABLED=true`.
- Provision/deploy intent is expressed through ArgoCD optional manifests:
  - `infra/gitops/argocd/optional/<env>/neo4j.yaml`
- Local Helm values are maintained in:
  - `infra/local/helm/neo4j/values.yaml`
