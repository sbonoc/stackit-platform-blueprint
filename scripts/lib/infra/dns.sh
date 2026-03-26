#!/usr/bin/env bash
set -euo pipefail

dns_init_env() {
  set_default_env DNS_ZONE_NAME "marketplace-dev"
  set_default_env DNS_ZONE_FQDN "marketplace.local."
  set_default_env DNS_RECORD_TTL "300"

  require_env_vars DNS_ZONE_NAME DNS_ZONE_FQDN
}

dns_zone_id() {
  printf '%s-%s' "$DNS_ZONE_NAME" "${STACKIT_REGION:-local}"
}
