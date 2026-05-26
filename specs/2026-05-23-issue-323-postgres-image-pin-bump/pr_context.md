# PR Context

## Summary
- Work item: 2026-05-23-issue-323-postgres-image-pin-bump
- Objective: Restore local provisioning broken by `bitnamilegacy/postgresql:16.x` tag retirement on Docker Hub; align blueprint PostgreSQL version default with STACKIT's latest supported major version (17).
- Scope boundaries: `versions.baseline.sh`, `versions.sh`, `infra/local/helm/postgres/values.yaml`, `scripts/lib/infra/postgres.sh`, `infra/cloud/stackit/terraform/modules/postgres/variables.tf`, `infra/cloud/stackit/terraform/foundation/variables.tf`, postgres module README (live + bootstrap mirror). No runtime logic, API surface, or check scripts changed.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004
- Acceptance criteria covered: AC-001, AC-002
- Contract surfaces changed: `POSTGRES_VERSION` environment variable default bumped from `16` to `17`; consumers that pin POSTGRES_VERSION explicitly are unaffected.

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/versions.baseline.sh` — local image tag bump
  - `scripts/lib/infra/postgres.sh` — POSTGRES_VERSION default 16 → 17
  - `infra/cloud/stackit/terraform/modules/postgres/variables.tf` — standalone module Terraform default 16 → 17
  - `infra/cloud/stackit/terraform/foundation/variables.tf` — foundation layer Terraform default 16 → 17
- Supporting files:
  - `scripts/lib/infra/versions.sh` — local image tag bump + bump policy comment
  - `infra/local/helm/postgres/values.yaml` — Helm chart image tag
  - `docs/platform/modules/postgres/README.md` — version references + bump policy docs
  - `scripts/templates/blueprint/bootstrap/docs/platform/modules/postgres/README.md` — bootstrap mirror

## Validation Evidence
- Required commands executed: make infra-audit-version (passed); docker manifest inspect docker.io/bitnamilegacy/postgresql:17.6.0-debian-12-r4 (resolved)
  - `docker manifest inspect docker.io/bitnamilegacy/postgresql:17.6.0-debian-12-r4` — manifest found (multi-arch)
  - `make infra-audit-version` — passed, `bitnamilegacy/postgresql:17.6.0-debian-12-r4` status=found
- Result summary: new pin resolves; audit passes.
- Artifact references: none

## Risk and Rollback
- Main risks: existing consumer STACKIT deployments running PostgreSQL 16 will not be automatically upgraded — Terraform only changes the default for new deployments or when consumers run `terraform apply` with `POSTGRES_VERSION` unset. Consumers with `POSTGRES_VERSION=16` explicitly set are fully unaffected.
- Rollback strategy: revert the commit; the previous pin `16.4.0-debian-12-r14` still resolves on Docker Hub today.

## Deferred Proposals
- Proposal 1 (not implemented): Add a scheduled GitHub Actions workflow that runs `infra-audit-version` daily to surface tag retirement before CI is triggered. Deferred — tracked in issue #323 detection gap note; separate scope.
