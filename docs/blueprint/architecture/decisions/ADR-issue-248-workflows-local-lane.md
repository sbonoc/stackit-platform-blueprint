# ADR — Workflows Local Lane: ArgoCD + Helm Pattern (apache-airflow chart)

- **Status:** proposed
- **ADR technical decision sign-off:** pending
- **Work item:** issue-248-workflows-local-lane
- **Date:** 2026-05-20
- **Author:** sbonoc

## Context

PR #314 (STACKIT Workflows module) recorded a SDD-C-014 exception: no local lane was provided because STACKIT Workflows is a cloud-only managed service with no viable local equivalent at the time. The backlog proposal "Local lane Airflow support" (on-scope: workflows) specifies deploying Apache Airflow on Docker Desktop Kubernetes to allow DAG development without a STACKIT account.

The blueprint already has two established patterns for deploying optional modules on the local lane:

1. **`argocd_optional_manifest` pattern** (neo4j, langfuse): `module_execution.sh` dispatches to a ConfigMap-or-Application manifest under `infra/gitops/argocd/optional/local/`; ArgoCD syncs the Helm chart from an approved chart repo listed in `appproject.yaml`.

2. **Helm values file in `infra/local/helm/<module>/values.yaml`**: Static values file checked into the repository, referenced by the ArgoCD Application manifest.

The existing `infra/gitops/argocd/optional/local/workflows.yaml` is a ConfigMap stub (deployed as part of PR #307); no actual Airflow deployment exists.

Three key decisions must be made:

**Decision 1**: Which dispatch pattern — `module_execution.sh` integration (argocd_optional_manifest) or standalone scripts bypassing dispatch?

**Decision 2**: Which DAG sync approach — git-sync sidecar (parity with STACKIT lane) or hostPath volume mount (simpler)?

**Decision 3**: Which Airflow executor — `LocalExecutor` (no extra dependencies) or `CeleryExecutor` (Redis required)?

## Decision

### Decision 1: `module_execution.sh` integration — OPTION_A selected

**Option A (selected):** Add `local-workflows:plan | local-workflows:apply | local-workflows:deploy | local-workflows:destroy` to `module_execution.sh` returning `argocd_optional_manifest`. New scripts `local_workflows_*.sh` source `workflows_local.sh` lib and route through dispatch.

**Option B (rejected):** Standalone `local_workflows_*.sh` scripts bypass `module_execution.sh` entirely, mirroring how `stackit_workflows_*.sh` bypasses dispatch for the STACKIT lane.

**Rationale for A:** The STACKIT lane bypasses dispatch because `api_contract` has no equivalent in the dispatch table. The local lane has a direct analogue (`argocd_optional_manifest`). Using centralized dispatch provides consistent profile-aware routing and allows future profiles to override the driver without changing the scripts. neo4j and langfuse both use this pattern; diverging from it adds unnecessary asymmetry.

### Decision 2: git-sync sidecar — OPTION_A selected

**Option A (selected):** Enable `dags.gitSync` in `airflow.values.yaml`. The git-sync sidecar polls the DAG repository and syncs new DAGs without restarting the Airflow pod.

**Option B (rejected):** `hostPath` volume mount of a local directory. Simpler for fully offline development, but requires the developer to manage the local directory and restart pods on DAG changes. Does not support remote DAG repositories.

**Rationale for A:** git-sync sidecar provides parity with the STACKIT lane (which uses a DAG repository URL + token). Engineers can develop locally against the same repository, reducing friction when promoting DAGs to the STACKIT environment.

### Decision 3: `LocalExecutor` — OPTION_A selected

**Option A (selected):** `executor: LocalExecutor`. Tasks run in subprocesses of the Airflow scheduler pod. No additional components required.

**Option B (rejected):** `CeleryExecutor`. Requires Redis for the Celery broker, adding a Redis dependency to Docker Desktop Kubernetes. Appropriate for production scale, not for local development.

**Rationale for A:** `LocalExecutor` is sufficient for local DAG development and testing. Eliminates Redis dependency and reduces resource pressure on Docker Desktop Kubernetes. The STACKIT lane uses a fully managed executor; local lane fidelity is DAG-level, not executor-level.

## Consequences

- The existing ConfigMap stub at `infra/gitops/argocd/optional/local/workflows.yaml` is replaced with an ArgoCD `Application` manifest.
- `infra/gitops/argocd/overlays/local/appproject.yaml` gains `https://airflow.apache.org` in `sourceRepos`.
- `scripts/lib/infra/module_execution.sh` gains a `local-workflows:*` dispatch case.
- `scripts/lib/infra/workflows_local.sh` is created (separate from `workflows.sh` to keep STACKIT and local concerns isolated).
- `scripts/bin/blueprint/render_makefile.sh` gains a `local-workflows` section with five make targets.
- `WORKFLOWS_LOCAL_ENABLED` is the new feature toggle (distinct from `WORKFLOWS_ENABLED` for STACKIT).
- The SDD-C-014 exception recorded in `specs/2026-05-20-issue-248-workflows-module/spec.md` is resolved by this work item.
- Four open questions (Q-1 through Q-4 in spec.md) require resolution before `SPEC_READY=true`.
