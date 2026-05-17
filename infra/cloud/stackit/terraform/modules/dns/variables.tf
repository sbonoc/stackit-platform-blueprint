variable "stackit_project_id" {
  type        = string
  description = "STACKIT project ID."
}

variable "stackit_region" {
  type        = string
  description = "STACKIT region."
  default     = "eu01"
}

variable "dns_zone_name" {
  type        = string
  description = "Display name for the DNS zone."
}

variable "dns_zone_fqdn" {
  type        = string
  description = "Fully qualified domain name for the DNS zone (trailing dot included)."
}

variable "dns_record_ttl" {
  type        = number
  description = "Default TTL in seconds for records in the DNS zone."
  default     = 300
}
