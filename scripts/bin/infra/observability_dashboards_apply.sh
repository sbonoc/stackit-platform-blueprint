#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"

start_script_metric_trap "infra_observability_dashboards_apply"

_namespace="${OBSERVABILITY_NAMESPACE:-observability}"
_configmap="${OBSERVABILITY_DASHBOARDS_NAME:-grafana-dashboards}"
_dashboards_dir="$ROOT_DIR/infra/observability/dashboards"

if [[ ! -d "$_dashboards_dir" ]]; then
  log_fatal "dashboards directory not found: $_dashboards_dir"
fi

log_info "applying dashboard ConfigMap $_configmap in namespace $_namespace"

kubectl create configmap "$_configmap" \
  --namespace "$_namespace" \
  --from-file="$_dashboards_dir" \
  --dry-run=client \
  -o yaml \
  | kubectl apply -f -

kubectl label configmap "$_configmap" \
  --namespace "$_namespace" \
  grafana_dashboard="1" \
  --overwrite

log_info "dashboard ConfigMap $_configmap applied with label grafana_dashboard=1"
