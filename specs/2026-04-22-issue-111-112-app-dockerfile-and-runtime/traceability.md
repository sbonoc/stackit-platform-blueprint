# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-001, SDD-C-002 | backend scaffold Dockerfile | `apps/backend/Dockerfile` | `AppDockerfileAndRuntimeTests::test_backend_dockerfile_multi_stage` | `architecture.md` | Dockerfile present at expected path |
| FR-002 | SDD-C-001, SDD-C-002 | touchpoints scaffold Dockerfile | `apps/touchpoints/Dockerfile` | `AppDockerfileAndRuntimeTests::test_touchpoints_dockerfile_multi_stage` | `architecture.md` | Dockerfile present at expected path |
| FR-003 | SDD-C-001, SDD-C-002 | backend deployment GHCR image | `infra/gitops/platform/base/apps/backend-api-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_backend_deployment_ghcr_image` | `architecture.md` | image field references GHCR path |
| FR-004 | SDD-C-001, SDD-C-002 | touchpoints deployment GHCR image | `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_touchpoints_deployment_ghcr_image` | `architecture.md` | image field references GHCR path |
| FR-005 | SDD-C-005 | bootstrap template drift sync | `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/` | `make infra-validate` | `architecture.md` | infra-validate passes |
| NFR-SEC-001 | SDD-C-001, SDD-C-002 | no secrets in Dockerfiles | `apps/backend/Dockerfile`, `apps/touchpoints/Dockerfile` | `AppDockerfileAndRuntimeTests::test_backend_dockerfile_multi_stage`, `AppDockerfileAndRuntimeTests::test_touchpoints_dockerfile_multi_stage` | `hardening_review.md` | Dockerfiles contain no credentials |
| NFR-OPS-001 | SDD-C-005 | imagePullPolicy unchanged | `infra/gitops/platform/base/apps/backend-api-deployment.yaml`, `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_backend_deployment_ghcr_image`, `AppDockerfileAndRuntimeTests::test_touchpoints_deployment_ghcr_image` | `hardening_review.md` | imagePullPolicy: IfNotPresent preserved |
| AC-001 | SDD-C-012 | backend Dockerfile multi-stage build | `apps/backend/Dockerfile` | `AppDockerfileAndRuntimeTests::test_backend_dockerfile_multi_stage` | `traceability.md` | FROM ... AS builder and FROM ... AS runtime |
| AC-002 | SDD-C-012 | backend Dockerfile EXPOSE 8080 and CMD | `apps/backend/Dockerfile` | `AppDockerfileAndRuntimeTests::test_backend_dockerfile_multi_stage` | `traceability.md` | EXPOSE 8080; CMD present |
| AC-003 | SDD-C-012 | touchpoints Dockerfile multi-stage build | `apps/touchpoints/Dockerfile` | `AppDockerfileAndRuntimeTests::test_touchpoints_dockerfile_multi_stage` | `traceability.md` | Node.js builder + nginx runtime |
| AC-004 | SDD-C-012 | touchpoints Dockerfile EXPOSE 80 | `apps/touchpoints/Dockerfile` | `AppDockerfileAndRuntimeTests::test_touchpoints_dockerfile_multi_stage` | `traceability.md` | EXPOSE 80 present |
| AC-005 | SDD-C-012 | backend deployment GHCR image reference | `infra/gitops/platform/base/apps/backend-api-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_backend_deployment_ghcr_image` | `traceability.md` | image field matches ghcr.io/ prefix (default scaffold: platform-blueprint-backend:0.1.0-dev) |
| AC-006 | SDD-C-012 | backend deployment no command override | `infra/gitops/platform/base/apps/backend-api-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_backend_deployment_ghcr_image` | `traceability.md` | no command: key in container spec (YAML-parsed) |
| AC-007 | SDD-C-012 | touchpoints deployment GHCR image reference | `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml` | `AppDockerfileAndRuntimeTests::test_touchpoints_deployment_ghcr_image` | `traceability.md` | image field matches ghcr.io/ prefix (default scaffold: platform-blueprint-touchpoints:0.1.0-dev) |
| AC-008 | SDD-C-012 | structural contract test class | `tests/infra/test_tooling_contracts.py` | `AppDockerfileAndRuntimeTests` | `traceability.md` | test class present and passing |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005
  - NFR-SEC-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make quality-hardening-review`, `make infra-contract-test-fast`
- Result summary: all gates green; contract tests pass with new AppDockerfileAndRuntimeTests class
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consumers must build and push to their GHCR registry before images are pullable in a real cluster (scaffold Dockerfiles alone do not make a cluster fully operational without a running registry).
