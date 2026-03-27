#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/versions.sh"

neo4j_init_env() {
  set_default_env NEO4J_EDITION "community"
  set_default_env NEO4J_BOLT_PORT "7687"
  set_default_env NEO4J_HTTP_PORT "7474"
  set_default_env NEO4J_DATABASE "neo4j"
  set_default_env NEO4J_NAMESPACE "data"
  set_default_env NEO4J_HELM_RELEASE "blueprint-neo4j"
  set_default_env NEO4J_HELM_CHART "neo4j/neo4j"
  set_default_env NEO4J_HELM_CHART_VERSION "$NEO4J_HELM_CHART_VERSION_PIN"

  require_env_vars NEO4J_AUTH_USERNAME NEO4J_AUTH_PASSWORD
}

neo4j_service_host() {
  printf '%s.%s.svc.cluster.local' "$NEO4J_HELM_RELEASE" "$NEO4J_NAMESPACE"
}

neo4j_uri() {
  local host
  host="$(neo4j_service_host)"
  printf 'bolt://%s:%s' "$host" "$NEO4J_BOLT_PORT"
}
