# ADR: Issue #248 — OpenSearch Module First-Class Implementation (Dual-Lane)

- **Status**: approved
- **Date**: 2026-05-06
- **Issue**: #248
- **Work item**: `specs/2026-05-06-issue-248-opensearch-module/`
- **ADR technical decision sign-off**: approved (sbonoc, PR #249 comment 2026-05-06)

## Context

The blueprint declares an `opensearch` optional module with a STACKIT lane that routes through the `foundation_contract` driver and a local lane that is a `noop`. Consumers cannot independently manage OpenSearch on local Docker Desktop; dhe-marketplace bundles OpenSearch inside the OpenMetadata Helm release as a workaround. `infra/cloud/stackit/terraform/modules/opensearch/main.tf` is a 7-line stub with no provider resources.

Issue #248 requires first-class implementation of the opensearch module on both lanes so that `infra-opensearch-apply` provisions a real OpenSearch service endpoint on both `local-*` and `stackit-*` profiles, with identical output shapes.

## Decision

### STACKIT lane
Implement `infra/cloud/stackit/terraform/modules/opensearch/main.tf` as a standalone Terraform module using the `stackit_opensearch_instance` resource (confirmed available in the STACKIT Terraform provider) and `stackit_opensearch_credential`. Expose all 8 outputs declared in `blueprint/modules/opensearch/module.contract.yaml`. Use `lifecycle { create_before_destroy = true }` to prevent silent destroy-recreate on version changes. The foundation layer continues to manage inline resources; the module is additive.

### Local lane
Add `infra/local/helm/opensearch/values.yaml` using the `bitnami/opensearch` chart. Pin version in `scripts/lib/infra/versions.sh` alongside existing module chart pins. Configure single-node, dev-sized (≤1 GB RAM, persistence disabled). Update `scripts/lib/infra/module_execution.sh` opensearch local cases from `noop` to `helm` driver. Update `scripts/lib/infra/opensearch.sh` to resolve host/port/scheme/credentials from the Helm release for local profile.

### Make target naming (Q-1 — resolved 2026-05-06)
Follow existing blueprint convention (Option A): `infra-opensearch-{plan,apply,smoke,destroy}` with internal profile-based routing. Consistent with postgres/rabbitmq/object-storage patterns. A comment will be posted on issue #248 explaining the deviation. Dual-lane naming deferred to a cross-cutting blueprint work item.

### Admin credentials (Q-2 — resolved 2026-05-06)
Proceed with `stackit_opensearch_credential` (Option A). Maintainer authorised the assumption that admin-level credentials are available. Stop condition applies if assumption fails during implementation.

## Alternatives Considered

**Option B — Explicit dual-lane make targets:** Add `infra-opensearch-local-apply` and `infra-opensearch-stackit-apply` as separate targets per issue #248's stated requirement. This would require updating `module_execution.sh`, `makefile` template, module contract YAML, and existing tests referencing `infra-opensearch-plan`. Rejected as the primary option because it creates an inconsistent make target namespace vs postgres/rabbitmq/object-storage (which all use the single-target pattern), breaks the `test_optional_module_make_targets_materialize_only_when_enabled` test, and introduces cross-cutting complexity best addressed in a separate work item for all modules.

**Option C — Refactor foundation to use Terraform module:** Have the foundation call `module "opensearch" { source = "../modules/opensearch" }` instead of inline resources. Rejected for this work item due to Terraform state migration risk; the module is implemented as a standalone library first.

## Consequences

- `infra/cloud/stackit/terraform/modules/opensearch/main.tf`: new, fully implemented standalone module.
- `infra/local/helm/opensearch/values.yaml`: new, single-node dev chart.
- `scripts/lib/infra/module_execution.sh`: opensearch local cases updated from `noop` to `helm`.
- `scripts/lib/infra/opensearch.sh`: local lane resolution functions added.
- `scripts/lib/infra/versions.sh`: `OPENSEARCH_HELM_CHART_VERSION_PIN` and image pins added.
- `scripts/bin/infra/opensearch_smoke.sh`: implemented (was stub).
- `tests/infra/modules/opensearch/test_contract.py`: new contract test.
- `docs/platform/modules/opensearch/README.md`: updated with dual-lane documentation.
- No breaking changes to existing `infra-opensearch-*` make target names.
- No Terraform state migration required (foundation inline resources unchanged).

## Open Questions

None — all questions resolved 2026-05-06.
