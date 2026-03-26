locals {
  normalized_tenant   = lower(replace(trimspace(var.tenant_slug), "_", "-"))
  normalized_platform = lower(replace(trimspace(var.platform_slug), "_", "-"))
  naming_prefix       = "${local.normalized_tenant}-${local.normalized_platform}-${var.environment}"
  state_key           = "${var.state_key_prefix}/${var.environment}/foundation.tfstate"
}

resource "terraform_data" "bootstrap_contract" {
  input = {
    environment      = var.environment
    stackit_project  = var.stackit_project_id
    stackit_region   = var.stackit_region
    naming_prefix    = local.naming_prefix
    foundation_state = local.state_key
  }
}
