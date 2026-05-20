# Local Workflows Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Deploy Apache Airflow on local Docker Desktop Kubernetes for DAG development without STACKIT cloud access.
- Enable flag: `WORKFLOWS_LOCAL_ENABLED` (default: `false`)
- Required inputs:
  - `WORKFLOWS_LOCAL_DAGS_REPO_URL`
  - `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN`
  - `WORKFLOWS_LOCAL_OIDC_ISSUER_URL`
  - `WORKFLOWS_LOCAL_OIDC_CLIENT_ID`
  - `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET`
- Make targets:
  - `infra-local-workflows-plan`
  - `infra-local-workflows-apply`
  - `infra-local-workflows-deploy`
  - `infra-local-workflows-smoke`
  - `infra-local-workflows-destroy`
- Outputs:
  - `WORKFLOWS_LOCAL_PUBLIC_URL`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Overview

The `local-workflows` module deploys Apache Airflow on Docker Desktop Kubernetes for DAG development without STACKIT cloud access. It mirrors the `langfuse` and `neo4j` local lane pattern using the `argocd_optional_manifest` provision driver with Helm chart `apache-airflow/airflow@1.20.0` (Airflow 3.1.8).

See also: [Workflows Module (STACKIT lane)](../workflows/README.md) for the production STACKIT-managed Airflow configuration.

## Prerequisites

- Docker Desktop Kubernetes running and ArgoCD installed (`make infra-bootstrap`)
- Keycloak running locally (`KEYCLOAK_ENABLED=true`)
- A Git repository containing your DAGs, with a deploy token

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `WORKFLOWS_LOCAL_ENABLED` | No | `false` | Enable the local Airflow lane |
| `WORKFLOWS_LOCAL_DAGS_REPO_URL` | Yes | — | Git URL (must end with `.git`) |
| `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` | Yes | — | Git deploy token (never written to state) |
| `WORKFLOWS_LOCAL_DAGS_REPO_BRANCH` | No | `main` | Branch to sync |
| `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH` | No | `/dags` | Subpath within repo for DAG files |
| `WORKFLOWS_LOCAL_OIDC_ISSUER_URL` | Yes | — | Keycloak realm URL |
| `WORKFLOWS_LOCAL_OIDC_CLIENT_ID` | Yes | — | OIDC client ID |
| `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` | Yes | — | OIDC client secret (never written to state) |
| `WORKFLOWS_LOCAL_AIRFLOW_HOST` | No | `localhost` | Airflow host for public URL |
| `WORKFLOWS_LOCAL_AIRFLOW_PORT` | No | `8080` | Airflow port for public URL |

## Make Targets

| Target | Description |
|---|---|
| `infra-local-workflows-plan` | Validate env vars; write plan state with `provision_driver`, `public_url`, `chart_version` |
| `infra-local-workflows-apply` | Defer ArgoCD manifest apply to deploy phase; write apply state with `provision_status=deferred_to_deploy` |
| `infra-local-workflows-deploy` | Apply ArgoCD Application manifest; write deploy state with `provision_status=deployed` |
| `infra-local-workflows-smoke` | Check Airflow `/health` endpoint; write smoke state with `status=passed` |
| `infra-local-workflows-destroy` | Delete ArgoCD Application; remove all `local_workflows_*` state files |

## Provisioning Lifecycle

```bash
export WORKFLOWS_LOCAL_ENABLED=true
export WORKFLOWS_LOCAL_DAGS_REPO_URL=https://github.com/your-org/your-dags-repo.git
export WORKFLOWS_LOCAL_DAGS_REPO_TOKEN=<token>
export WORKFLOWS_LOCAL_OIDC_ISSUER_URL=http://localhost:8081/realms/platform
export WORKFLOWS_LOCAL_OIDC_CLIENT_ID=airflow-local
export WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET=<secret>

make infra-local-workflows-plan
make infra-local-workflows-apply
make infra-local-workflows-deploy

# Port-forward to access Airflow UI
kubectl port-forward -n data svc/blueprint-airflow-webserver 8080:8080 &

make infra-local-workflows-smoke
```

## DAG Git-Sync Setup

The local lane mounts DAGs via the git-sync sidecar. The sidecar syncs from `WORKFLOWS_LOCAL_DAGS_REPO_URL` using a Kubernetes secret named `airflow-git-credentials`. Create the secret before deploying:

```bash
kubectl create secret generic airflow-git-credentials \
  --namespace data \
  --from-literal=username=git \
  --from-literal=password="$WORKFLOWS_LOCAL_DAGS_REPO_TOKEN"
```

## Keycloak OIDC Wiring

The `webserverConfig.py` override in `airflow.values.yaml` configures Flask-AppBuilder OIDC via `AUTH_OAUTH`. The client reads `WORKFLOWS_LOCAL_OIDC_CLIENT_ID`, `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET`, and `WORKFLOWS_LOCAL_OIDC_ISSUER_URL` from the pod environment. Wire these as Kubernetes secrets via External Secrets Operator using the existing `eso-plus-argocd-plus-keycloak` runtime identity baseline.

## Teardown

```bash
make infra-local-workflows-destroy
```

This deletes the ArgoCD Application and removes all `local_workflows_*` state artifacts. The Helm release is pruned automatically by ArgoCD's automated sync policy.

## Security

- `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` — used for git-sync sidecar authentication; never written to any state file or logged.
- `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` — used for Keycloak OIDC; never written to any state file or logged.
- Both secrets must be supplied via environment variables at runtime; do not commit them to version control.
