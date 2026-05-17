variable "stackit_project_id" {
  type        = string
  description = "STACKIT project ID."
}

variable "stackit_region" {
  type        = string
  description = "STACKIT region (declared for API consistency; not forwarded to stackit_dns_zone)."
  default     = "eu01"
}

variable "dns_zone_fqdns" {
  type        = list(string)
  description = "Fully qualified domain names for the DNS zones to provision (trailing dot included)."
}

variable "dns_naming_prefix" {
  type        = string
  description = "Naming prefix for zone display names, constructed by the shell layer as {DNS_NAMING_PREFIX}-{active_stack} (e.g. myapp-dev). Zone name: {dns_naming_prefix}-dns-{sha1(fqdn)[0:8]}."
}

variable "dns_record_ttl" {
  type        = number
  description = "Default TTL in seconds for records in the DNS zones."
  default     = 300
}
