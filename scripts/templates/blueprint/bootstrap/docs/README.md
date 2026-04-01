# Documentation

This repository uses Markdown as the canonical documentation source and can be rendered via Docusaurus.

In the source blueprint repository this page is maintainer-oriented. Generated consumer repositories replace `docs/README.md` during `make blueprint-init-repo` with a consumer-owned docs index.

## Choose Your Path
- [Blueprint Docs](blueprint/README.md): maintain and evolve the blueprint itself.
- [Platform Docs](platform/README.md): platform docs for generated target repositories.

## If You Are Using the Template (Consumer Track)
Recommended reading order:
1. [First 30 Minutes](platform/consumer/first_30_minutes.md)
2. [Platform Quickstart](platform/consumer/quickstart.md)
3. [Endpoint Exposure Model](platform/consumer/endpoint_exposure_model.md)
4. [Protected API Routes](platform/consumer/protected_api_routes.md)
5. [Event Messaging Baseline](platform/consumer/event_messaging_baseline.md)
6. [Zero-Downtime Evolution](platform/consumer/zero_downtime_evolution.md)
7. [Tenant Context Propagation](platform/consumer/tenant_context_propagation.md)
8. [Platform Troubleshooting](platform/consumer/troubleshooting.md)

Fast path:
```bash
make blueprint-init-repo-interactive
make blueprint-bootstrap
make infra-bootstrap
make infra-validate
```

For CI/non-interactive bootstrap, use:
```bash
cp blueprint/repo.init.secrets.example.env blueprint/repo.init.secrets.env
${EDITOR:-vi} blueprint/repo.init.env blueprint/repo.init.secrets.env
make blueprint-init-repo
```

`make blueprint-init-repo` creates or refreshes tracked defaults in `blueprint/repo.init.env`,
keeps placeholder-only scaffolding in `blueprint/repo.init.secrets.example.env`, and creates
gitignored local sensitive defaults in `blueprint/repo.init.secrets.env`.
For enabled optional modules, required non-sensitive inputs are seeded into `blueprint/repo.init.env`
and required sensitive inputs are scaffolded in the secrets files with non-empty placeholders.
Later `make blueprint-check-placeholders` and infra targets auto-load defaults + secrets files when present.

For existing generated repositories, compare consumer-seeded root files against the latest
seed templates with a supported dry-run workflow:
```bash
make blueprint-resync-consumer-seeds
```
Apply only safe deterministic updates:
```bash
BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds
```
Force full overwrite (including manual-merge candidates):
```bash
BLUEPRINT_RESYNC_APPLY_ALL=true make blueprint-resync-consumer-seeds
```
For full blueprint-managed upgrades on existing generated repos:
```bash
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> make blueprint-upgrade-consumer
BLUEPRINT_UPGRADE_REF=<tag|branch|commit> BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer
make blueprint-upgrade-consumer-validate
```
`BLUEPRINT_UPGRADE_SOURCE` defaults to `remote.upstream.url` when configured, then `remote.origin.url`.

## If You Maintain the Blueprint (Maintainer Track)
Read:
1. [Blueprint README](blueprint/README.md)
2. [Blueprint Execution Model](blueprint/architecture/execution_model.md)
3. [Blueprint System Overview](blueprint/architecture/system_overview.md)
4. [Ownership Matrix](blueprint/governance/ownership_matrix.md)

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
- `make blueprint-resync-consumer-seeds`
- `make blueprint-upgrade-consumer`
- `make blueprint-upgrade-consumer-validate`
- `make blueprint-bootstrap`
- `make blueprint-render-module-wrapper-skeletons`
- `make blueprint-clean-generated`
- `make infra-bootstrap`
- `make infra-local-destroy-all`
- `make infra-destroy-disabled-modules`
- `make infra-validate`
- `make infra-smoke`

Upgrade guardrails:
- `make blueprint-upgrade-consumer` fails fast when the resolved baseline tag and selected upgrade ref point to the same commit (`upgrade baseline collision`).
- When this happens, choose an upgrade ref newer than the baseline tag (or bump `template_bootstrap.template_version` first) before re-running.

If you intentionally need to re-apply consumer-seeded or init-managed files after first init, rerun:
- `BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`

Quality and docs flow:
- `make quality-hooks-fast`
- `make quality-hooks-strict`
- `make quality-hooks-run`
- `make quality-docs-lint`
- `make quality-docs-check-blueprint-template-sync`
- `make quality-test-pyramid`
- `make quality-docs-sync-runtime-identity-summary`
- `make quality-docs-sync-module-contract-summaries`
- `make docs-install`
- `make docs-run`
- `make docs-build`
- `make docs-smoke`

Operational diagnostics and teardown:
- `make infra-context`
- `make infra-status-json`
- `make infra-local-destroy-all`
- `make infra-stackit-destroy-all`
- `artifacts/infra/smoke_result.json`
- `artifacts/infra/smoke_diagnostics.json`
- `artifacts/infra/workload_health.json`
- `artifacts/infra/infra_status_snapshot.json`

## Optional Module Targets (Materialized Conditionally)
`make blueprint-render-makefile` (or `make blueprint-bootstrap`) renders `make/blueprint.generated.mk` from template and only materializes targets for enabled modules.
`make infra-bootstrap` materializes enabled optional-module infra scaffolding and preserves disabled-module scaffolding for safe future enablement.
Use `make infra-destroy-disabled-modules` when resources for a now-disabled module may already exist.

To inspect the currently materialized optional-module targets for your active flags, run:
- `make help`

## App Catalog Contract
- `apps/catalog/manifest.yaml` is the canonical app-layer manifest.
- `apps/catalog/versions.lock` stores pinned app/runtime versions.

## Generated References
- [Contract Metadata (Generated)](reference/generated/contract_metadata.generated.md)
- [Core Make Targets (Generated)](reference/generated/core_targets.generated.md)
