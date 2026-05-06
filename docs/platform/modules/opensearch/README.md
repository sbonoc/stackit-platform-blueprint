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
  - Local chart/image pins stay on the latest stable Bitnami chart and image line matching the managed-service family.
  - The pinned fallback image uses `docker.io/bitnamilegacy/opensearch`; the pinned tag stays on the latest stable supported image line while remaining multi-arch for both amd64 CI nodes and arm64 Docker Desktop clusters.

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
- Local service is reachable at `http://blueprint-opensearch.search.svc.cluster.local:9200`.
- OpenSearch Dashboards (if chart includes it) at `http://blueprint-opensearch.search.svc.cluster.local:5601`.

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
- In dry-run mode (before foundation apply), wrappers emit `.stackit.invalid` placeholders.

## Prerequisites
- `OPENSEARCH_ENABLED=true` set in the calling environment.
- `OPENSEARCH_INSTANCE_NAME`, `OPENSEARCH_VERSION`, `OPENSEARCH_PLAN_NAME` required for both lanes.
- Local lane: Docker Desktop Kubernetes running, `kubectl` context pointing to local cluster, Helm `bitnami` repo added.
  - Pin versions: `OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_TAG` declared in `scripts/lib/infra/versions.sh`.
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
| `OPENSEARCH_USERNAME` | no | `admin` | Admin username (local lane only; STACKIT uses provider-generated) |
| `OPENSEARCH_PASSWORD` | no | `admin` | Admin password (local lane only; STACKIT uses provider-generated) |

## Smoke
Run after apply to validate the runtime contract:

```bash
make infra-opensearch-smoke
```

Checks:
- `artifacts/infra/opensearch_runtime.env` exists.
- `uri` value matches `^https?://` (accepts both local `http://` and STACKIT `https://`).
- `dashboard_url` value matches `^https?://`.
- Writes `artifacts/infra/opensearch_smoke.env` on success.

## Credentials

- **Local lane**: username and password are set to `admin`/`admin` by default. Override via `OPENSEARCH_USERNAME` and `OPENSEARCH_PASSWORD` env vars.
- **STACKIT lane**: credentials are provider-generated via `stackit_opensearch_credential` (admin-level). Credentials are emitted to the runtime state file and masked in logs (NFR-SEC-001).

## Security

- `OPENSEARCH_PASSWORD` is never logged in plain text (bash `set +x` semantics apply in opensearch.sh; value written to state file only, not stdout).
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
dashboard_url=<dashboard URL>
username=<username>
password=<password>
timestamp_utc=<ISO8601>
```

## Version migration

- STACKIT lane: `stackit_opensearch_instance` has `lifecycle { create_before_destroy = true }` — version upgrades trigger replacement with zero downtime.
- Local lane: run `helm upgrade` by bumping `OPENSEARCH_HELM_CHART_VERSION_PIN` in `versions.sh` and re-applying.
- Pin source of truth: `scripts/lib/infra/versions.sh` (`OPENSEARCH_HELM_CHART_VERSION_PIN`, `OPENSEARCH_LOCAL_IMAGE_TAG`).

## Destroy

```bash
# Local lane
make infra-opensearch-destroy
# Equivalent: helm uninstall blueprint-opensearch -n search

# STACKIT lane
OPENSEARCH_ENABLED=false make infra-opensearch-destroy
# Runs foundation reconcile with OPENSEARCH_ENABLED=false to remove the managed instance.
```

Rollback: if `infra-opensearch-apply` fails mid-way, re-run `infra-opensearch-apply` (idempotent for Helm) or run `infra-opensearch-destroy` to remove the partial state.
