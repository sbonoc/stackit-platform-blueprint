# PR Context

## Work Item
- Spec slug: issue-383-384-385-386-366-395-v1122-bugfixes
- GitHub issues: #383, #384, #385, #386, #366, #395
- Target release: v1.12.2 (release/v1.12.x branch)
- Bypass track: bug-fix

## Summary
Six P2 infrastructure bugs affecting consumers on v1.12.1. All fixes are isolated to module contract YAML files, shell library scripts, a Helm values file, and a deploy script. No Terraform provider changes, no new make targets, no API or event contract changes.

## Fix Inventory

| FR | Issue | File(s) | Change |
|---|---|---|---|
| FR-001 | #383 | `blueprint/modules/postgres/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh` | `POSTGRES_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit |
| FR-002 | #384 | `blueprint/modules/object-storage/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/object_storage.sh` | `OBJECT_STORAGE_BUCKET_NAME` moved to `optional_env`; conditional `-var=` emit; remove inert `require_env_vars` |
| FR-003 | #385 | `blueprint/modules/rabbitmq/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/rabbitmq.sh` | `RABBITMQ_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit; remove unconditional `require_env_vars` |
| FR-004 | #385 | `blueprint/modules/opensearch/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/opensearch.sh` | `OPENSEARCH_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit; remove unconditional `require_env_vars`; correct version and plan defaults |
| FR-005 | #386 | `blueprint/modules/postgres/module.contract.yaml`, `scripts/lib/infra/postgres.sh` | `POSTGRES_PASSWORD` moved to `optional_env`; gate `require_env_vars` on non-STACKIT profiles only |
| FR-006 | #366 | `infra/local/helm/rabbitmq/values.yaml`, `scripts/templates/infra/bootstrap/infra/local/helm/rabbitmq/values.yaml` | Add `global.security.allowInsecureImages: true` |
| FR-007 | #395 | `scripts/bin/infra/public_endpoints_deploy.sh` | Remove `run_manifest_apply "$gateway_manifest_path"` from `argocd_application_chart` branch |

## Risk and Rollback
- **FR-001–004 (optional instance names):** Re-running Terraform after removing the `-var=` flag is idempotent — the provider derives the same name from `naming_prefix`. Zero risk of resource recreation. Rollback: re-add the conditional var emit.
- **FR-005 (POSTGRES_PASSWORD optional on STACKIT):** On STACKIT the password is never an input; removing the require cannot break provisioning. On local/Helm paths the profile guard preserves the existing require. Rollback: remove the profile guard.
- **FR-006 (allowInsecureImages):** Chart accepts the same image it already used; no image change. Rollback: remove the three YAML lines.
- **FR-007 (gateway drift fix):** Consumers in `argocd_application_chart` mode with GitOps-managed Gateways are unblocked. Consumers who relied on the direct apply (contradicts GitOps ownership by definition) would lose it. Rollback: restore the `run_manifest_apply "$gateway_manifest_path"` call.

## Operator Upgrade Notes
Consumers upgrading from v1.12.1 to v1.12.2 may safely remove `POSTGRES_INSTANCE_NAME`, `OBJECT_STORAGE_BUCKET_NAME`, `RABBITMQ_INSTANCE_NAME`, and `OPENSEARCH_INSTANCE_NAME` from `blueprint/repo.init.env` if they were set there as placeholders. Terraform continues to derive identical names. `POSTGRES_PASSWORD` should also be removed from `blueprint/repo.init.env` for STACKIT profiles — it is a provider output, not an input.
