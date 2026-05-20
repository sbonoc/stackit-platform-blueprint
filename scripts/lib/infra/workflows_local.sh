#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/versions.sh"

workflows_local_init_env() {
  set_default_env WORKFLOWS_LOCAL_NAMESPACE "data"
  set_default_env WORKFLOWS_LOCAL_HELM_RELEASE "blueprint-airflow"
  set_default_env WORKFLOWS_LOCAL_HELM_CHART "apache-airflow/airflow"
  set_default_env WORKFLOWS_LOCAL_HELM_CHART_VERSION "$WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN"
  set_default_env WORKFLOWS_LOCAL_DAGS_REPO_BRANCH "main"
  set_default_env WORKFLOWS_LOCAL_DAGS_REPO_SUBPATH "/dags"
  set_default_env WORKFLOWS_LOCAL_AIRFLOW_HOST "localhost"
  set_default_env WORKFLOWS_LOCAL_AIRFLOW_PORT "8080"

  require_env_vars \
    WORKFLOWS_LOCAL_DAGS_REPO_URL \
    WORKFLOWS_LOCAL_DAGS_REPO_TOKEN \
    WORKFLOWS_LOCAL_OIDC_ISSUER_URL \
    WORKFLOWS_LOCAL_OIDC_CLIENT_ID \
    WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET

  if [[ "$WORKFLOWS_LOCAL_DAGS_REPO_URL" != *.git ]]; then
    log_fatal "WORKFLOWS_LOCAL_DAGS_REPO_URL must end with .git; got: $WORKFLOWS_LOCAL_DAGS_REPO_URL"
  fi
}

workflows_local_public_url() {
  printf 'http://%s:%s' "$WORKFLOWS_LOCAL_AIRFLOW_HOST" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"
}

workflows_local_chart_version() {
  printf '%s' "$WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN"
}
