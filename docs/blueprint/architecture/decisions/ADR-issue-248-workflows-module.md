# ADR — Workflows Module: REST API Contract Pattern (no Terraform provider resource)

- **Status:** approved
- **ADR technical decision sign-off:** approved
- **Work item:** issue-248-workflows-module
- **Date:** 2026-05-20
- **Author:** sbonoc

## Context

The blueprint STACKIT Workflows module (managed Apache Airflow) is designed to provision a STACKIT Workflows instance, reconcile a Keycloak OIDC confidential client, deploy DAGs from a git repository, and smoke-validate the deployment. The module's shell layer (`scripts/bin/infra/stackit_workflows_*.sh`, `scripts/lib/infra/workflows.sh`, `scripts/lib/infra/workflows_api.sh`) is fully implemented.

The blueprint's standard provisioning path for STACKIT resources uses the STACKIT Terraform provider (`stackit/*`) via the foundation TF layer. However, no `stackit_workflows_instance` Terraform provider resource exists in any version of the STACKIT Terraform provider, including the latest release (v0.96.0, verified 2026-05-20 by checking provider changelog across v0.88.0–v0.96.0). The STACKIT Workflows REST API at `https://workflows.api.stackit.cloud/v1alpha` is the only available provisioning interface.

The issue #248 backlog note ("Continue migrating workflows to provider-backed STACKIT execution when official resources become available") confirms that the REST API approach is intentional as a bridge pattern.

Additionally, there are zero automated tests for the workflows module (`tests/infra/modules/workflows/` contains only a README), and the module README is a generated contract summary stub. This work item adds the missing test coverage and documentation.

## Decision

**Option A (selected): REST API contract pattern with `provision_driver=api_contract`.**

- `stackit_workflows_plan.sh` generates the API request payload JSON and writes a plan state file with `provision_driver=api_contract`. This mirrors the semantics of a Terraform plan step for auditability without requiring TF.
- `stackit_workflows_apply.sh` POSTs to `https://workflows.api.stackit.cloud/v1alpha/projects/{projectId}/regions/{region}/instances` via `workflows_api_request()`, handles HTTP 409 idempotently (existing instance looked up by display name), and writes the instance state file.
- `infra/cloud/stackit/terraform/modules/workflows/main.tf` is intentionally an empty stub with a comment explaining that no TF provider resource exists yet.
- The SDD-C-014 (local-first runtime baseline) exception is documented in `spec.md` and here: no local lane is provided because STACKIT Workflows is a cloud-only managed Airflow service with no viable local equivalent at this time. This is an explicit scope decision per issue #248 requirements table.

**Option B (rejected): Block implementation until a Terraform provider resource is available.**

- Blocks the entire module with no timeline guarantee — no provider resource exists as of v0.96.0.
- The REST API approach is already validated in production by existing consumers.
- Waiting provides no value; the REST API is stable enough for a bridge implementation.

**Option C (rejected): Deploy a self-managed Airflow Helm chart as a local lane substitute.**

- Adds significant scope and maintenance burden without delivering the STACKIT-managed Airflow integration.
- Local lane Airflow (optional, consumer-toggled) is a separate future work item — explicitly out of scope here.

## Consequences

- `stackit_workflows_plan.sh` produces `artifacts/infra/workflows_plan.env` with `provision_driver=api_contract`, `payload_file`, `display_name`.
- `stackit_workflows_apply.sh` produces `artifacts/infra/workflows_instance.env` with `instance_id`, `instance_name`, `instance_fqdn`, `web_url`, `health_status`.
- `STACKIT_WORKFLOWS_DAGS_REPO_TOKEN` and `STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET` MUST NOT appear in any state file (consumed at runtime only).
- The REST API is at `v1alpha` — API breaking changes would require updating `workflows_api.sh`. Mitigated by explicit HTTP code validation and deterministic `jq` field paths that fail fast.
- When (if) a Terraform provider resource for `stackit_workflows_instance` is released, the REST API client layer can be replaced with a TF module stub and `provision_driver=terraform_foundation`. This is the intended migration path per the issue #248 backlog note.

## Open Questions

- **Q-1 (deferred):** STACKIT Terraform provider is pinned at v0.88.0; latest available is v0.96.0. Should the provider version be upgraded as part of this work item? **Recommendation: No — defer to a separate work item.** Workflows uses REST API, not TF, so there is zero functional benefit for this PR. The upgrade is a cross-cutting concern affecting all foundation TF resources and requires its own validation cycle.
