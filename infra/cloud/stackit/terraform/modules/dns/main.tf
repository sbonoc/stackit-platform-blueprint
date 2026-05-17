terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

# NFR-REL-001: zone recreation requires registrar re-delegation — no lifecycle recreation guard.
resource "stackit_dns_zone" "this" {
  project_id = var.stackit_project_id
  name       = var.dns_zone_name
  dns_name   = trimsuffix(var.dns_zone_fqdn, ".")
  default_ttl = var.dns_record_ttl
}
