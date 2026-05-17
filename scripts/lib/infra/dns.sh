#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"

dns_init_env() {
  set_default_env DNS_ZONE_FQDNS ""
  set_default_env DNS_NAMING_PREFIX "marketplace"
  set_default_env DNS_RECORD_TTL "300"

  require_env_vars DNS_ZONE_FQDNS DNS_NAMING_PREFIX
}

dns_naming_prefix_with_stack() {
  printf '%s-%s' "$DNS_NAMING_PREFIX" "$(active_stack)"
}

dns_zone_ids() {
  local ids=""
  for fqdn in $DNS_ZONE_FQDNS; do
    local id
    if is_stackit_profile; then
      id="$(stackit_foundation_output_map_value_or_default "dns_zone_ids" "$fqdn" "${DNS_NAMING_PREFIX}-local-${fqdn%%.*}")"
    else
      id="${DNS_NAMING_PREFIX}-local-${fqdn%%.*}"
    fi
    ids="${ids:+$ids }$id"
  done
  printf '%s' "$ids"
}

dns_zone_count() {
  local count=0
  for _ in $DNS_ZONE_FQDNS; do count=$((count + 1)); done
  printf '%d' "$count"
}

dns_primary_name_servers() {
  local servers=""
  for fqdn in $DNS_ZONE_FQDNS; do
    local server
    if is_stackit_profile; then
      server="$(stackit_foundation_output_map_value_or_default "dns_primary_name_servers" "$fqdn" "ns.dns.stackit.cloud.")"
    else
      server="ns.dns.local."
    fi
    servers="${servers:+$servers }$server"
  done
  printf '%s' "$servers"
}
