#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "apps_publish_ghcr"
set_state_namespace apps

usage() {
  cat <<'USAGE'
Usage: publish_ghcr.sh

Builds and publishes backend/touchpoints images to GHCR.
Default mode is dry-run unless DRY_RUN=false.

Optional environment variables:
  APPS_GHCR_REGISTRY           Registry hostname (default: ghcr.io)
  APPS_GHCR_OWNER              Registry owner/org (default: BLUEPRINT_GITHUB_ORG or example-org)
  APPS_GHCR_IMAGE_PREFIX       Image name prefix (default: platform-blueprint)
  APPS_GHCR_TAG                Image tag override (default: APP_VERSION[-APP_BUILD_ID])
  APPS_BACKEND_DOCKERFILE      Backend Dockerfile path (default: apps/backend/Dockerfile)
  APPS_BACKEND_BUILD_CONTEXT   Backend build context (default: apps/backend)
  APPS_TOUCHPOINTS_DOCKERFILE  Touchpoints Dockerfile path (default: apps/touchpoints/Dockerfile)
  APPS_TOUCHPOINTS_BUILD_CONTEXT Touchpoints build context (default: apps/touchpoints)

Authentication (execute mode):
  GHCR_USERNAME + GHCR_TOKEN, or GITHUB_ACTOR + GITHUB_TOKEN.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_warn "apps-publish-ghcr is primarily intended for stackit-* profiles; continuing with profile=$BLUEPRINT_PROFILE"
fi

set_default_env APP_VERSION "0.1.0"
set_default_env APP_BUILD_ID "dev"
set_default_env APP_RELEASE "0"
set_default_env APPS_GHCR_REGISTRY "ghcr.io"
set_default_env APPS_GHCR_OWNER "${BLUEPRINT_GITHUB_ORG:-example-org}"
set_default_env APPS_GHCR_IMAGE_PREFIX "platform-blueprint"
set_default_env APPS_BACKEND_DOCKERFILE "apps/backend/Dockerfile"
set_default_env APPS_BACKEND_BUILD_CONTEXT "apps/backend"
set_default_env APPS_TOUCHPOINTS_DOCKERFILE "apps/touchpoints/Dockerfile"
set_default_env APPS_TOUCHPOINTS_BUILD_CONTEXT "apps/touchpoints"

release_tag="$APP_VERSION"
if [[ "$APP_RELEASE" != "1" ]]; then
  release_tag="$APP_VERSION-$APP_BUILD_ID"
fi
set_default_env APPS_GHCR_TAG "$release_tag"

resolve_repo_path() {
  local path_value="$1"
  if [[ "$path_value" == /* ]]; then
    echo "$path_value"
    return 0
  fi
  echo "$ROOT_DIR/$path_value"
}

backend_dockerfile="$(resolve_repo_path "$APPS_BACKEND_DOCKERFILE")"
backend_context="$(resolve_repo_path "$APPS_BACKEND_BUILD_CONTEXT")"
touchpoints_dockerfile="$(resolve_repo_path "$APPS_TOUCHPOINTS_DOCKERFILE")"
touchpoints_context="$(resolve_repo_path "$APPS_TOUCHPOINTS_BUILD_CONTEXT")"

backend_image="$APPS_GHCR_REGISTRY/$APPS_GHCR_OWNER/$APPS_GHCR_IMAGE_PREFIX-backend:$APPS_GHCR_TAG"
touchpoints_image="$APPS_GHCR_REGISTRY/$APPS_GHCR_OWNER/$APPS_GHCR_IMAGE_PREFIX-touchpoints:$APPS_GHCR_TAG"

candidate_count=0
published_count=0

publish_candidate() {
  local label="$1"
  local dockerfile_path="$2"
  local build_context="$3"
  local image_ref="$4"

  if [[ ! -f "$dockerfile_path" ]]; then
    log_warn "$label Dockerfile missing; skipping publish candidate dockerfile=$dockerfile_path"
    return 0
  fi
  if [[ ! -d "$build_context" ]]; then
    log_warn "$label build context missing; skipping publish candidate context=$build_context"
    return 0
  fi

  candidate_count=$((candidate_count + 1))

  if tooling_is_execution_enabled; then
    run_cmd docker build -f "$dockerfile_path" -t "$image_ref" "$build_context"
    run_cmd docker push "$image_ref"
    published_count=$((published_count + 1))
    return 0
  fi

  log_info "dry-run docker build -f $dockerfile_path -t $image_ref $build_context"
  log_info "dry-run docker push $image_ref"
}

if tooling_is_execution_enabled; then
  require_command docker
  if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
    printf '%s' "$GHCR_TOKEN" | run_cmd docker login "$APPS_GHCR_REGISTRY" --username "$GHCR_USERNAME" --password-stdin
  elif [[ -n "${GITHUB_ACTOR:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
    printf '%s' "$GITHUB_TOKEN" | run_cmd docker login "$APPS_GHCR_REGISTRY" --username "$GITHUB_ACTOR" --password-stdin
  else
    log_warn "no GHCR credentials provided (GHCR_USERNAME/GHCR_TOKEN or GITHUB_ACTOR/GITHUB_TOKEN); relying on existing docker auth"
  fi
fi

publish_candidate "backend" "$backend_dockerfile" "$backend_context" "$backend_image"
publish_candidate "touchpoints" "$touchpoints_dockerfile" "$touchpoints_context" "$touchpoints_image"

log_metric "apps_publish_ghcr_candidates" "$candidate_count" "profile=$BLUEPRINT_PROFILE"
log_metric "apps_publish_ghcr_published" "$published_count" "mode=$(tooling_execution_mode)"

state_file="$(
  write_state_file "apps_publish_ghcr" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "registry=$APPS_GHCR_REGISTRY" \
    "owner=$APPS_GHCR_OWNER" \
    "image_prefix=$APPS_GHCR_IMAGE_PREFIX" \
    "image_tag=$APPS_GHCR_TAG" \
    "backend_image=$backend_image" \
    "touchpoints_image=$touchpoints_image" \
    "candidate_count=$candidate_count" \
    "published_count=$published_count" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "apps publish ghcr state written to $state_file"
