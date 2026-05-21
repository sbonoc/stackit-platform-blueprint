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
  - `infra-local-workflows-dags-venv`
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
| `infra-local-workflows-dags-venv` | Create `.venv-dags` (Python 3.12) for DAG development; skipped if `WORKFLOWS_LOCAL_ENABLED=false` |

## Provisioning Lifecycle

```bash
export WORKFLOWS_LOCAL_ENABLED=true
export WORKFLOWS_LOCAL_DAGS_REPO_URL=https://github.com/your-org/your-dags-repo.git
export WORKFLOWS_LOCAL_DAGS_REPO_TOKEN=<token>
export WORKFLOWS_LOCAL_OIDC_ISSUER_URL=http://localhost:8081/realms/platform
export WORKFLOWS_LOCAL_OIDC_CLIENT_ID=airflow-local
export WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET=<secret>

# Step 1: set repo URL in Helm values (one-time per environment)
# Edit infra/local/helm/workflows/airflow.values.yaml and set dags.gitSync.repo

# Step 2: create Kubernetes secrets (one-time per cluster)
kubectl create secret generic airflow-git-credentials \
  --namespace data \
  --from-literal=username=git \
  --from-literal=password="$WORKFLOWS_LOCAL_DAGS_REPO_TOKEN"

kubectl create secret generic airflow-oidc-credentials \
  --namespace data \
  --from-literal=WORKFLOWS_LOCAL_OIDC_ISSUER_URL="$WORKFLOWS_LOCAL_OIDC_ISSUER_URL" \
  --from-literal=WORKFLOWS_LOCAL_OIDC_CLIENT_ID="$WORKFLOWS_LOCAL_OIDC_CLIENT_ID" \
  --from-literal=WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET="$WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET"

make infra-local-workflows-plan
make infra-local-workflows-apply
make infra-local-workflows-deploy
make infra-local-workflows-smoke
```

## DAG Git-Sync Setup

The local lane mounts DAGs via the git-sync sidecar. Before deploying, you must do two things:

**1. Set the repo URL (and optionally branch/subpath) in `infra/local/helm/workflows/airflow.values.yaml`:**

```yaml
dags:
  gitSync:
    repo: "https://github.com/your-org/your-dags-repo.git"  # set this
    branch: "main"      # update if WORKFLOWS_LOCAL_DAGS_REPO_BRANCH differs
    subPath: "/dags"    # update if WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH differs
```

The git-sync sidecar reads `branch` and `subPath` directly from the Helm values file. `WORKFLOWS_LOCAL_DAGS_REPO_BRANCH` and `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH` are used only for plan-phase validation; if you override their defaults, update the values file to match.

**2. Create the `airflow-git-credentials` Kubernetes secret:**

```bash
kubectl create secret generic airflow-git-credentials \
  --namespace data \
  --from-literal=username=git \
  --from-literal=password="$WORKFLOWS_LOCAL_DAGS_REPO_TOKEN"
```

The `WORKFLOWS_LOCAL_DAGS_REPO_URL` env var is used only for plan-phase validation. The git-sync sidecar reads its repo URL directly from the Helm values file.

## Keycloak OIDC Wiring

The `webserverConfig.py` override in `airflow.values.yaml` configures Flask-AppBuilder OIDC via `AUTH_OAUTH`. The OIDC env vars (`WORKFLOWS_LOCAL_OIDC_CLIENT_ID`, `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET`, `WORKFLOWS_LOCAL_OIDC_ISSUER_URL`) are injected into the webserver pod from a Kubernetes secret named `airflow-oidc-credentials` via `webserver.extraEnvFrom`.

Create the secret before deploying:

```bash
kubectl create secret generic airflow-oidc-credentials \
  --namespace data \
  --from-literal=WORKFLOWS_LOCAL_OIDC_ISSUER_URL="$WORKFLOWS_LOCAL_OIDC_ISSUER_URL" \
  --from-literal=WORKFLOWS_LOCAL_OIDC_CLIENT_ID="$WORKFLOWS_LOCAL_OIDC_CLIENT_ID" \
  --from-literal=WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET="$WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET"
```

## Teardown

```bash
make infra-local-workflows-destroy
```

This deletes the ArgoCD Application and removes all `local_workflows_*` state artifacts. The Helm release is pruned automatically by ArgoCD's automated sync policy.

## DAG Development Setup

### Python Version

Blueprint tooling requires Python ≥ 3.13 on the host (see `pyproject.toml`). Apache Airflow 3.1.8 ships Python 3.12 inside the container. DAG code developed locally must target Python 3.12 — the Airflow runtime version — not the blueprint tooling version.

Create a dedicated virtual environment for DAG development:

```bash
# Install Python 3.12 via uv if not already available
uv python install 3.12

# Create the DAG development venv:
make infra-local-workflows-dags-venv
```

Configure your IDE to use `.venv-dags` as the Python interpreter for DAG files. The `.venv-dags/` directory is gitignored.

### Repository Structure

Store DAG files in a `/dags/` directory at the root of your DAG repository. The git-sync sidecar mounts the subpath configured in `infra/local/helm/workflows/airflow.values.yaml` (`dags.gitSync.subPath`, default: `/dags`). Keep `WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH` and `dags.gitSync.subPath` in sync — if you override either, update both.

Typical layout:

```
your-dags-repo/
├── dags/
│   ├── my_dag.py
│   └── utils/
├── .venv-dags/       # Python 3.12 DAG dev venv (gitignored)
└── pyproject.toml    # or requirements.txt
```

**For coding agents:** target the `.venv-dags` venv when generating or editing DAG files. Run `uv pip install --python .venv-dags/bin/python apache-airflow==3.1.8` inside `.venv-dags` for accurate import resolution.

## Security

- `WORKFLOWS_LOCAL_DAGS_REPO_TOKEN` — used for git-sync sidecar authentication; never written to any state file or logged.
- `WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET` — used for Keycloak OIDC; never written to any state file or logged.
- Both secrets must be supplied via environment variables at runtime; do not commit them to version control.
