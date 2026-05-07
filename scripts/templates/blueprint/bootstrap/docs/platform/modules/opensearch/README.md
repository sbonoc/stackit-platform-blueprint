# OpenSearch Module (Optional)

<!-- BEGIN GENERATED MODULE CONTRACT SUMMARY -->
## Contract Summary
- Purpose: Provision managed OpenSearch and expose canonical endpoint/credentials for runtime consumers.
- Enable flag: `OPENSEARCH_ENABLED` (default: `false`)
- Required inputs:
  - `OPENSEARCH_INSTANCE_NAME`
  - `OPENSEARCH_VERSION`
  - `OPENSEARCH_PLAN_NAME`
- Make targets:
  - `infra-opensearch-plan`
  - `infra-opensearch-apply`
  - `infra-opensearch-smoke`
  - `infra-opensearch-destroy`
- Outputs:
  - `OPENSEARCH_HOST`
  - `OPENSEARCH_HOSTS`
  - `OPENSEARCH_PORT`
  - `OPENSEARCH_SCHEME`
  - `OPENSEARCH_URI`
  - `OPENSEARCH_DASHBOARD_URL`
  - `OPENSEARCH_USERNAME`
  - `OPENSEARCH_PASSWORD`
<!-- END GENERATED MODULE CONTRACT SUMMARY -->

## Stack Execution Model
- Optional module Make targets are materialized by `make blueprint-render-makefile` (or `make blueprint-bootstrap`) when `OPENSEARCH_ENABLED=true`.
- Scaffolding paths are materialized by `make infra-bootstrap` only when `OPENSEARCH_ENABLED=true`.
- `stackit-*` profiles: STACKIT foundation provisions a managed OpenSearch instance through `stackit_opensearch_instance` plus `stackit_opensearch_credential`, and wrappers read terraform outputs into the runtime contract.
- `local-*` profiles: Helm chart (`bitnami/opensearch`) runs from a rendered values artifact derived from the scaffold contract in `infra/local/helm/opensearch/values.yaml`.
  - OpenSearch managed-service version family: `2.17` (matching `OPENSEARCH_VERSION` default; image pinned in `scripts/lib/infra/versions.sh`).
  - Local chart pin: `1.6.3` (Bitnami chart series 1.x, OpenSearch app version `2.19.1`). Chart 2.x targets OpenSearch 3.x and is incompatible with the 2.17/2.19 image line.
  - Local image pin: `docker.io/bitnamilegacy/opensearch:2.19.1-debian-12-r4` — closest stable Bitnami tag to the STACKIT 2.17 family that the chart 1.6.3 templates support; multi-arch for amd64 CI nodes and arm64 Docker Desktop clusters.

## Local lane

```bash
OPENSEARCH_ENABLED=true \
OPENSEARCH_INSTANCE_NAME=marketplace-opensearch \
OPENSEARCH_VERSION=2.17 \
OPENSEARCH_PLAN_NAME=stackit-opensearch-single \
make infra-opensearch-plan infra-opensearch-apply infra-opensearch-smoke
```

- Provisions `blueprint-opensearch` Helm release in the `search` namespace.
- Writes `artifacts/infra/opensearch_runtime.env` with all 8 contract outputs.
- Local service is reachable at `http://blueprint-opensearch.search.svc.cluster.local:9200` (the chart's client-facing Service, selector → coordinating-only pods).

### Local topology (minimal 2-pod)

The Bitnami chart's defaults deploy 8 pods (master×2 + data×2 + ingest×2 + coordinating×2). For local dev we explicitly trim to 2 pods to stay within ~1.5 GB memory:

| Node group | replicaCount | Notes |
|---|---|---|
| `master` | 1 | `masterOnly: false` — master also serves data role |
| `data` | 0 | disabled |
| `ingest` | 0 (`enabled: false`) | disabled |
| `coordinating` | 1 | preserves the chart's client-facing Service selector |
| `dashboards` | 0 (`enabled: false`) | dev does not deploy Dashboards; `OPENSEARCH_DASHBOARD_URL` is intentionally empty on local |

Total local memory limit: 1 Gi (master) + 512 Mi (coordinating) ≈ 1.5 Gi.

## STACKIT lane

```bash
OPENSEARCH_ENABLED=true \
OPENSEARCH_INSTANCE_NAME=marketplace-opensearch \
OPENSEARCH_VERSION=2.17 \
OPENSEARCH_PLAN_NAME=stackit-opensearch-single \
make infra-opensearch-plan infra-opensearch-apply infra-opensearch-smoke
```

- `stackit-*` profile routes to `foundation_contract` driver — applies terraform foundation with `OPENSEARCH_ENABLED=true`.
- `OPENSEARCH_HOST`, `OPENSEARCH_URI`, `OPENSEARCH_USERNAME`, and `OPENSEARCH_PASSWORD` are resolved from terraform outputs after apply.
- `OPENSEARCH_DASHBOARD_URL` is resolved from `stackit_opensearch_instance.dashboard_url`.
- In dry-run mode (before foundation apply), wrappers emit `.stackit.invalid` placeholders.

## Prerequisites
- `OPENSEARCH_ENABLED=true` set in the calling environment.
- `OPENSEARCH_INSTANCE_NAME`, `OPENSEARCH_VERSION`, `OPENSEARCH_PLAN_NAME` required for both lanes.
- Local lane: Docker Desktop Kubernetes running with at least 2 GB allocated to Kubernetes; `kubectl` context pointing to local cluster; Helm `bitnami` repo added (`helm repo add bitnami https://charts.bitnami.com/bitnami`).
  - Pin versions: `OPENSEARCH_HELM_CHART_VERSION_PIN=1.6.3`, `OPENSEARCH_LOCAL_IMAGE_TAG=2.19.1-debian-12-r4` declared in `scripts/lib/infra/versions.sh`.
- STACKIT lane: `STACKIT_PROJECT_ID`, `STACKIT_SERVICE_ACCOUNT_TOKEN` set in the environment; STACKIT terraform provider `0.88.0`.

## Env-var reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENSEARCH_ENABLED` | no | `false` | Enable the module |
| `OPENSEARCH_INSTANCE_NAME` | yes | `marketplace-opensearch` | Instance / Helm release name |
| `OPENSEARCH_VERSION` | yes | `2.17` | Managed service / image family version |
| `OPENSEARCH_PLAN_NAME` | yes | `stackit-opensearch-single` | STACKIT service plan (ignored for local) |
| `OPENSEARCH_NAMESPACE` | no | `search` | Kubernetes namespace (local lane only) |
| `OPENSEARCH_HELM_RELEASE` | no | `blueprint-opensearch` | Helm release name (local lane only) |
| `OPENSEARCH_HELM_CHART` | no | `bitnami/opensearch` | Helm chart reference (local lane only) |
| `OPENSEARCH_HELM_CHART_VERSION` | no | from `OPENSEARCH_HELM_CHART_VERSION_PIN` | Helm chart version (local lane only) |
| `OPENSEARCH_IMAGE_REGISTRY` | no | `docker.io` | Container image registry (local lane only) |
| `OPENSEARCH_IMAGE_REPOSITORY` | no | `bitnamilegacy/opensearch` | Container image repository (local lane only) |
| `OPENSEARCH_IMAGE_TAG` | no | `2.19.1-debian-12-r4` | Container image tag (local lane only) |
| `OPENSEARCH_PASSWORD` | no | `admin` | Admin password (local lane only). Reconciled into K8s Secret `blueprint-opensearch-auth` (key `opensearch-password`) on every apply; never embedded in checked-in values. STACKIT lane: provider-generated. |

`OPENSEARCH_USERNAME` is intentionally **not** an override on the local lane: the Bitnami chart hard-codes `admin` as the OpenSearch admin user, and any extraEnvVars override produces a duplicate env entry with undefined precedence. The state file always reports `username=admin` for local.

## Smoke
Run after apply to validate the runtime contract:

```bash
make infra-opensearch-smoke
```

Checks:
- `artifacts/infra/opensearch_runtime.env` exists.
- `uri` value matches `^https?://` (accepts both local `http://` and STACKIT `https://`).
- `dashboard_url` value matches `^https?://` OR is empty (intentionally empty on local lane where the dashboards subchart is disabled).
- Writes `artifacts/infra/opensearch_smoke.env` on success.

## Credentials

- **Local lane**: password is reconciled into Kubernetes Secret `blueprint-opensearch-auth` (key `opensearch-password`) on every apply via `apply_optional_module_secret_from_literals`; the chart consumes it via `security.existingSecret`. The plaintext password is never embedded in the rendered Helm values file. Default value is `admin` for development; override via `OPENSEARCH_PASSWORD`. Username is locked to `admin` (chart constraint).
- **STACKIT lane**: credentials are provider-generated via `stackit_opensearch_credential` (admin-level). Credentials are emitted to the runtime state file and masked in logs (NFR-SEC-001).

## Security

- Local password is reconciled out-of-band into a Kubernetes Secret rather than embedded in `values.yaml` — the rendered `artifacts/infra/rendered/opensearch.values.yaml` contains only the Secret name reference, not the password value.
- The runtime state file `artifacts/infra/opensearch_runtime.env` does contain the password in plaintext (matches the rabbitmq/postgres pattern); `artifacts/` is gitignored.
- STACKIT credential resource (`stackit_opensearch_credential`) produces admin-level access; rotate by re-applying the foundation terraform layer.

## State

Runtime state file written to `artifacts/infra/opensearch_runtime.env` by `infra-opensearch-apply`. Schema:

```
profile=<BLUEPRINT_PROFILE>
stack=<active_stack>
provision_driver=<helm|foundation_contract>
provision_path=<rendered values path or terraform dir>
host=<OpenSearch host>
hosts=<comma-separated hosts>
port=<port>
scheme=<http|https>
uri=<full URI>
dashboard_url=<dashboard URL — empty on local lane>
username=<username — always "admin" on local>
password=<password>
timestamp_utc=<ISO8601>
```

## Version migration

- STACKIT lane: `stackit_opensearch_instance` has `lifecycle { create_before_destroy = true }` — version upgrades trigger replacement with zero downtime.
- Local lane: run `helm upgrade` by bumping `OPENSEARCH_HELM_CHART_VERSION_PIN` in `versions.sh` (stay within the 1.x line for OpenSearch 2.x compatibility) and re-applying.
- Pin source of truth: `scripts/lib/infra/versions.sh` (`OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_TAG`).

## Destroy

```bash
# Local lane (OPENSEARCH_ENABLED=true must be set so the destroy target is rendered into the Makefile)
OPENSEARCH_ENABLED=true make infra-opensearch-destroy
# Runs: helm uninstall blueprint-opensearch -n search (idempotent --ignore-not-found),
# then deletes the K8s Secret blueprint-opensearch-auth.

# STACKIT lane
OPENSEARCH_ENABLED=true make infra-opensearch-destroy
# Routes to the foundation reconcile destroy path for the managed instance.
```

Rollback: if `infra-opensearch-apply` fails mid-way, re-run `infra-opensearch-apply` (idempotent for Helm) or run `infra-opensearch-destroy` to remove the partial state.
