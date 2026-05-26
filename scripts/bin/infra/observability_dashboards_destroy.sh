#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"

start_script_metric_trap "infra_observability_dashboards_destroy"

_namespace="${OBSERVABILITY_NAMESPACE:-observability}"
_configmap="${OBSERVABILITY_DASHBOARDS_NAME:-grafana-dashboards}"

log_info "deleting dashboard ConfigMap $_configmap in namespace $_namespace"

kubectl delete configmap "$_configmap" \
  --namespace "$_namespace" \
  --ignore-not-found=true

log_info "dashboard ConfigMap $_configmap deleted (or was not found)"
