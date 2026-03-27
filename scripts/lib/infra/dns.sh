#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"

dns_init_env() {
  set_default_env DNS_ZONE_NAME "marketplace-dev"
  set_default_env DNS_ZONE_FQDN "marketplace.local."
  set_default_env DNS_RECORD_TTL "300"

  require_env_vars DNS_ZONE_NAME DNS_ZONE_FQDN
}

dns_zone_id() {
  if is_stackit_profile; then
    stackit_foundation_output_map_value_or_default "dns_zone_ids" "$DNS_ZONE_FQDN" "$(dns_zone_name)"
    return 0
  fi
  dns_zone_name
}

dns_zone_name() {
  printf '%s-%s' "$DNS_ZONE_NAME" "${STACKIT_REGION:-local}"
}
