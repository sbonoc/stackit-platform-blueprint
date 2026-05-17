terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

# NFR-REL-001: zone recreation requires registrar re-delegation — no lifecycle recreation guard.
resource "stackit_dns_zone" "this" {
  for_each = toset(var.dns_zone_fqdns)

  project_id  = var.stackit_project_id
  name        = substr("${var.dns_naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}", 0, 63)
  dns_name    = trimsuffix(each.value, ".")
  default_ttl = var.dns_record_ttl
}
