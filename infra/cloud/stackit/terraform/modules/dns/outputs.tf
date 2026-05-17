output "zone_id" {
  description = "The ID of the provisioned DNS zone."
  value       = stackit_dns_zone.this.zone_id
}

output "dns_name" {
  description = "The DNS name of the provisioned zone (without trailing dot)."
  value       = stackit_dns_zone.this.dns_name
}

output "primary_name_server" {
  description = "The primary name server FQDN assigned to the DNS zone by STACKIT."
  value       = stackit_dns_zone.this.primary_name_server
}
