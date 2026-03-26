terraform {
  required_version = ">= 1.13.0"
}

locals {
  blueprint_environment = "stackit"
  deprecation_notice    = "Use infra/cloud/stackit/terraform/foundation instead."
}
