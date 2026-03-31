#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"

workflows_default_display_name() {
  local profile_slug raw sanitized
  profile_slug="$(printf '%s' "${BLUEPRINT_PROFILE:-stackit-dev}" | tr '[:upper:]' '[:lower:]')"
  raw="bpwf-${profile_slug}"
  sanitized="$(printf '%s' "$raw" | tr -cd 'a-z0-9-')"
  sanitized="$(printf '%s' "$sanitized" | sed -E 's/-+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "$sanitized" ]]; then
    sanitized="bpwf-dev"
  fi
  printf '%s' "${sanitized:0:16}"
}

workflows_init_env() {
  if ! is_stackit_profile; then
    log_fatal "STACKIT Workflows module requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
  fi

  keycloak_seed_env_defaults
  set_default_env STACKIT_WORKFLOWS_API_BASE_URL "https://workflows.api.stackit.cloud/v1alpha"
  set_default_env STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS "30"
  set_default_env STACKIT_WORKFLOWS_ACCESS_TOKEN ""
  set_default_env STACKIT_WORKFLOWS_API_TOKEN "$STACKIT_WORKFLOWS_ACCESS_TOKEN"
  set_default_env STACKIT_WORKFLOWS_VERSION "workflows-2.3-airflow-2.11"
  set_default_env STACKIT_WORKFLOWS_INSTANCE_DISPLAY_NAME "$(workflows_default_display_name)"
  set_default_env STACKIT_WORKFLOWS_OIDC_CLIENT_ID "stackit-workflows"
  set_default_env STACKIT_WORKFLOWS_ADMIN_USERNAME "workflows-admin"
  set_default_env STACKIT_WORKFLOWS_ADMIN_PASSWORD "$STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET"
  set_default_env STACKIT_WORKFLOWS_RECONCILE_EXISTING_ONLY "false"
  set_default_env STACKIT_WORKFLOWS_REQUIRE_SINGLE_ACTIVE_INSTANCE "true"

  require_env_vars \
    STACKIT_PROJECT_ID \
    STACKIT_REGION \
    STACKIT_WORKFLOWS_DAGS_REPO_URL \
    STACKIT_WORKFLOWS_DAGS_REPO_BRANCH \
    STACKIT_WORKFLOWS_DAGS_REPO_USERNAME \
    STACKIT_WORKFLOWS_DAGS_REPO_TOKEN \
    STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL \
    STACKIT_WORKFLOWS_OIDC_CLIENT_ID \
    STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET \
    STACKIT_OBSERVABILITY_INSTANCE_ID \
    STACKIT_WORKFLOWS_API_BASE_URL

  if [[ ! "$STACKIT_WORKFLOWS_DAGS_REPO_URL" =~ \.git$ ]]; then
    log_fatal "STACKIT_WORKFLOWS_DAGS_REPO_URL must end with .git"
  fi
}

workflows_compute_instance_id() {
  local display_name hash
  display_name="${1:-$STACKIT_WORKFLOWS_INSTANCE_DISPLAY_NAME}"
  hash="$(printf '%s' "${STACKIT_PROJECT_ID}:${STACKIT_REGION}:${display_name}" | shasum -a 256 | awk '{print $1}')"
  printf '%s' "${hash:0:8}"
}

workflows_compute_instance_name() {
  printf '%s' "$STACKIT_WORKFLOWS_INSTANCE_DISPLAY_NAME"
}

workflows_compute_instance_fqdn() {
  local instance_name instance_id
  instance_name="${1:-$(workflows_compute_instance_name)}"
  instance_id="${2:-$(workflows_compute_instance_id "$instance_name")}"
  printf '%s' "${instance_name}-${instance_id}.workflows.${STACKIT_REGION}.stackit.cloud"
}

workflows_payload_json() {
  local display_name
  display_name="$(workflows_compute_instance_name)"
  cat <<EOF
{
  "displayName": "${display_name}",
  "version": "${STACKIT_WORKFLOWS_VERSION}",
  "description": "Managed STACKIT Workflows instance for ${BLUEPRINT_PROFILE}.",
  "dagsRepository": {
    "branch": "${STACKIT_WORKFLOWS_DAGS_REPO_BRANCH}",
    "url": "${STACKIT_WORKFLOWS_DAGS_REPO_URL}",
    "auth": {
      "type": "basic",
      "username": "${STACKIT_WORKFLOWS_DAGS_REPO_USERNAME}",
      "password": "${STACKIT_WORKFLOWS_DAGS_REPO_TOKEN}"
    }
  },
  "identityProvider": {
    "name": "keycloak",
    "clientId": "${STACKIT_WORKFLOWS_OIDC_CLIENT_ID}",
    "clientSecret": "${STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET}",
    "scope": "openid profile email",
    "discoveryEndpoint": "${STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL}",
    "type": "oauth2"
  },
  "observabilityId": "${STACKIT_OBSERVABILITY_INSTANCE_ID}"
}
EOF
}
