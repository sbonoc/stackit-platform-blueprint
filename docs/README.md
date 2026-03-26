# Documentation

This repository uses Markdown as the canonical documentation source and can be rendered via Docusaurus.

## Choose Your Path
- [Blueprint Docs](blueprint/README.md): maintain and evolve the blueprint itself.
- [Platform Docs](platform/README.md): seeded baseline docs for generated target repositories.

## If You Are Using the Template (Consumer Track)
Recommended reading order:
1. [First 30 Minutes](platform/consumer/first_30_minutes.md)
2. [Platform Quickstart](platform/consumer/quickstart.md)
3. [Platform Troubleshooting](platform/consumer/troubleshooting.md)
4. [Platform Upgrade Runbook](platform/consumer/upgrade_runbook.md)

Fast path:
```bash
make blueprint-init-repo-interactive
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
```

For CI/non-interactive bootstrap, use:
```bash
set -a
source blueprint/repo.init.example.env
set +a
make blueprint-init-repo
```

## If You Maintain the Blueprint (Maintainer Track)
Read:
1. [Blueprint README](blueprint/README.md)
2. [Blueprint Execution Model](blueprint/architecture/execution_model.md)
3. [Blueprint System Overview](blueprint/architecture/system_overview.md)
4. [Ownership Matrix](blueprint/governance/ownership_matrix.md)
5. [Template Release Policy](blueprint/governance/template_release_policy.md)

## Canonical Infra Paths
- STACKIT Terraform: `infra/cloud/stackit/terraform/`
- Local provisioning: `infra/local/crossplane/`
- Local Helm values: `infra/local/helm/`
- GitOps overlays and optional apps: `infra/gitops/argocd/`

## Optional Modules
- [Observability](platform/modules/observability/README.md)
- [Workflows](platform/modules/workflows/README.md)
- [Langfuse](platform/modules/langfuse/README.md)
- [Postgres](platform/modules/postgres/README.md)
- [Neo4j](platform/modules/neo4j/README.md)
- [Object Storage](platform/modules/object-storage/README.md)
- [RabbitMQ](platform/modules/rabbitmq/README.md)
- [DNS](platform/modules/dns/README.md)
- [Public Endpoints](platform/modules/public-endpoints/README.md)
- [Secrets Manager](platform/modules/secrets-manager/README.md)
- [KMS](platform/modules/kms/README.md)
- [Identity-Aware Proxy](platform/modules/identity-aware-proxy/README.md)

## Command Reference
Command discovery:
- `make help`
- `make infra-help-reference`

Common baseline flow:
- `make blueprint-init-repo-interactive`
- `make blueprint-init-repo`
- `make blueprint-bootstrap`
- `make blueprint-render-module-wrapper-skeletons`
- `make blueprint-clean-generated`
- `make infra-bootstrap`
- `make infra-destroy-disabled-modules`
- `make infra-validate`
- `make infra-smoke`

Quality and docs flow:
- `make quality-hooks-run`
- `make docs-install`
- `make docs-run`
- `make docs-build`
- `make docs-smoke`

## Optional Module Targets (Materialized Conditionally)
`make blueprint-render-makefile` (or `make blueprint-bootstrap`) renders `make/blueprint.generated.mk` from template and only materializes targets for enabled modules.
`make infra-bootstrap` materializes/prunes optional-module infra scaffolding from previously enabled optional modules.
Use `make infra-destroy-disabled-modules` before pruning when module resources may already exist.

To inspect the currently materialized optional-module targets for your active flags, run:
- `make help`

## App Catalog Contract
- `apps/catalog/manifest.yaml` is the canonical app-layer manifest.
- `apps/catalog/versions.lock` stores pinned app/runtime versions.

## Generated Contract Reference
- [Contract Metadata (Generated)](reference/generated/contract_metadata.generated.md)
