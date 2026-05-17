output "zone_ids" {
  description = "Map of FQDN to provisioned DNS zone ID."
  value       = { for fqdn, zone in stackit_dns_zone.this : fqdn => zone.zone_id }
}

output "dns_names" {
  description = "List of DNS names (without trailing dot) for provisioned zones."
  value       = [for zone in stackit_dns_zone.this : zone.dns_name]
}

output "primary_name_servers" {
  description = "Map of FQDN to primary name server FQDN assigned by STACKIT."
  value       = { for fqdn, zone in stackit_dns_zone.this : fqdn => zone.primary_name_server }
}
