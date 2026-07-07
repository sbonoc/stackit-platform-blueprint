# PR Context

## Work Item
- Work item: issue-383-384-385-386-366-395-v1122-bugfixes
- Objective: Fix six P2 infrastructure bugs in v1.12.2 so consumers on v1.12.1 can upgrade without placeholder collisions, provider validation errors, GitOps drift loops, or Bitnami image security gate rejections.
- Scope boundaries: Module contract YAML files, shell library scripts, Helm values files, a deploy script, and module READMEs. No Terraform provider changes, no new make targets, no API or event contract changes.
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Key Reviewer Files
- Primary files to review first:
  - `blueprint/modules/postgres/module.contract.yaml` — POSTGRES_INSTANCE_NAME and POSTGRES_PASSWORD moved from required_env to optional_env (FR-001, FR-005)
  - `blueprint/modules/object-storage/module.contract.yaml` — OBJECT_STORAGE_BUCKET_NAME moved to optional_env (FR-002)
  - `blueprint/modules/rabbitmq/module.contract.yaml` — RABBITMQ_INSTANCE_NAME moved to optional_env (FR-003)
  - `blueprint/modules/opensearch/module.contract.yaml` — OPENSEARCH_INSTANCE_NAME moved to optional_env; version and plan defaults corrected (FR-004)
  - `scripts/lib/infra/stackit_layers.sh` — conditional -var= emit guards for all four instance-name variables (FR-001–004)
  - `scripts/lib/infra/rabbitmq.sh` — removed set_default_env RABBITMQ_INSTANCE_NAME from seed_env_defaults; removed require_env_vars (FR-003)
  - `scripts/lib/infra/opensearch.sh` — removed set_default_env OPENSEARCH_INSTANCE_NAME from seed_env_defaults; removed require_env_vars; corrected OPENSEARCH_VERSION default to "2" and OPENSEARCH_PLAN_NAME to replica plan (FR-004)
  - `scripts/lib/infra/postgres.sh` — POSTGRES_PASSWORD require gated on is_stackit_profile (FR-005)
  - `infra/local/helm/rabbitmq/values.yaml` and bootstrap template — global.security.allowInsecureImages: true (FR-006)
  - `scripts/bin/infra/public_endpoints_deploy.sh` — run_manifest_apply for gateway_manifest_path removed from argocd_application_chart branch (FR-007)

## Validation Evidence
- Required commands executed: `uv run python3 -m pytest tests/infra/test_v1122_bugfixes.py -v`, `uv run python3 -m pytest tests/ -x -q`, `make quality-hooks-fast`, `make quality-hardening-review`, `make quality-sdd-check`, `make quality-docs-check-changed`
- Result summary: 27/27 AC-specific tests pass; full suite 1483+ tests pass; quality-hooks-fast pass; quality-hardening-review pass; quality-sdd-check pass; quality-docs-check-changed pass

## Fix Inventory

| FR | Issue | File(s) | Change |
|---|---|---|---|
| FR-001 | #383 | `blueprint/modules/postgres/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh` | `POSTGRES_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit |
| FR-002 | #384 | `blueprint/modules/object-storage/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/object_storage.sh` | `OBJECT_STORAGE_BUCKET_NAME` moved to `optional_env`; conditional `-var=` emit; remove inert `require_env_vars` |
| FR-003 | #385 | `blueprint/modules/rabbitmq/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/rabbitmq.sh` | `RABBITMQ_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit; remove unconditional `require_env_vars`; remove `set_default_env` for instance name |
| FR-004 | #385 | `blueprint/modules/opensearch/module.contract.yaml`, `scripts/lib/infra/stackit_layers.sh`, `scripts/lib/infra/opensearch.sh`, `scripts/bin/infra/opensearch_plan.sh` | `OPENSEARCH_INSTANCE_NAME` moved to `optional_env`; conditional `-var=` emit; remove unconditional `require_env_vars`; remove `set_default_env` for instance name; correct `OPENSEARCH_VERSION` default to `"2"`; correct `OPENSEARCH_PLAN_NAME` to replica plan |
| FR-005 | #386 | `blueprint/modules/postgres/module.contract.yaml`, `scripts/lib/infra/postgres.sh` | `POSTGRES_PASSWORD` moved to `optional_env`; gate `require_env_vars` on non-STACKIT profiles only |
| FR-006 | #366 | `infra/local/helm/rabbitmq/values.yaml`, `scripts/templates/infra/bootstrap/infra/local/helm/rabbitmq/values.yaml` | Add `global.security.allowInsecureImages: true` |
| FR-007 | #395 | `scripts/bin/infra/public_endpoints_deploy.sh` | Remove `run_manifest_apply "$gateway_manifest_path"` from `argocd_application_chart` branch |

## Requirement Coverage

| Requirement | Implementation | Test |
|---|---|---|
| FR-001 | `blueprint/modules/postgres/module.contract.yaml` required_env; `stackit_layers.sh` conditional guard | `AC001PostgresInstanceNameOptionalTests` (3 assertions) |
| FR-002 | `blueprint/modules/object-storage/module.contract.yaml` required_env; `stackit_layers.sh` guard; `object_storage.sh` require removed | `AC002ObjectStorageBucketNameOptionalTests` (4 assertions) |
| FR-003 | `blueprint/modules/rabbitmq/module.contract.yaml` required_env; `rabbitmq.sh` seed_env_defaults + require removed; `stackit_layers.sh` guard; `rabbitmq_plan.sh` guard | `AC003RabbitmqInstanceNameOptionalTests` (6 assertions) |
| FR-004 | `blueprint/modules/opensearch/module.contract.yaml` required_env; `opensearch.sh` seed_env_defaults + require removed; version + plan defaults; `stackit_layers.sh` guard; `opensearch_plan.sh` guard | `AC004OpensearchInstanceNameOptionalTests` (8 assertions) |
| FR-005 | `blueprint/modules/postgres/module.contract.yaml` required_env; `postgres.sh` is_stackit_profile guard | `AC005PostgresPasswordStackitOptionalTests` (3 assertions) |
| FR-006 | `infra/local/helm/rabbitmq/values.yaml`; bootstrap template mirror | `AC006RabbitmqAllowInsecureImagesTests` (2 assertions) |
| FR-007 | `scripts/bin/infra/public_endpoints_deploy.sh` argocd_application_chart branch | `AC007PublicEndpointsNoGatewayDriftTests` (1 assertion) |
| NFR-SEC-001 | allowInsecureImages is a chart flag, not a credential; bitnamilegacy/rabbitmq is the existing pinned image | Code review + AC-006 |
| NFR-REL-001 | Conditional -var= emit omits the flag when unset; Terraform falls back to locals.tf naming_prefix derivation identical to prior hardcoded value | Code review + AC-001–004 |
| NFR-OPS-001 | required_env cleared for all four module contracts | AC-001–004 contract assertions |

## Risk and Rollback
- Main risks: (1) OPENSEARCH_PLAN_NAME default slug `stackit-opensearch-2.17-replica` was inferred from naming convention; if STACKIT renames the plan, terraform plan will fail with a provider validation error. (2) Consumers who currently set instance-name vars in blueprint/repo.init.env continue to pass those values to Terraform (conditional guard emits when non-empty) — no runtime change for those consumers. (3) pnpm lockfile (lockfileVersion 9.0) may emit version warnings under pnpm@11 in future CI runs; --ignore-scripts unblocks the gate.
- Rollback strategy: Each FR is independently reversible via git revert. FR-001–004: restore set_default_env lines in seed_env_defaults and remove conditional guards in stackit_layers.sh. FR-005: remove is_stackit_profile guard from postgres.sh. FR-006: remove global.security.allowInsecureImages from both rabbitmq values files. FR-007: restore the run_manifest_apply call in public_endpoints_deploy.sh.

## Operator Upgrade Notes

Consumers upgrading from v1.12.1 to v1.12.2 may safely remove the following from `blueprint/repo.init.env`:
- `POSTGRES_INSTANCE_NAME` — now optional; Terraform derives a unique per-environment name from `naming_prefix`.
- `OBJECT_STORAGE_BUCKET_NAME` — now optional; same derivation.
- `RABBITMQ_INSTANCE_NAME` — now optional; same derivation.
- `OPENSEARCH_INSTANCE_NAME` — now optional; same derivation.
- `POSTGRES_PASSWORD` (STACKIT profiles only) — provider-generated output, not an input.

Removing these entries causes `blueprint-check-placeholders` to pass rather than fail. Terraform behaviour is unchanged.

## Deferred Proposals

- Proposal 1 (not implemented): OpenSearch plan slug auto-discovery — Parked — trigger: on-scope: infra — Requires Terraform provider data source work; surfaces when any STACKIT OpenSearch work touches `infra/cloud/stackit/terraform/foundation`. Out of scope for a patch release.
- Proposal 2 (not implemented): Consumer migration guide for removed required vars — Parked — trigger: after: #167 — `make blueprint-upgrade-consumer` enhancement to detect now-optional vars and emit a migration warning. Blocked on issue #167 upgrade tooling track.
- Proposal 3 (not implemented): pnpm lockfile regeneration — Parked — trigger: on-scope: docs — `docs/pnpm-lock.yaml` lockfileVersion 9.0 was generated by pnpm@10; regeneration under pnpm@11 produces lockfileVersion 10. `--ignore-scripts` is a safe working fix; surfaces when any developer bumps pnpm or changes docs dependencies.
