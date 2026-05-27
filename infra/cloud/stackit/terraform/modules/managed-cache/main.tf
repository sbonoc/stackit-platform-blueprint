terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_redis_instance" "managed_cache" {
  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = var.managed_cache_instance_name
  version    = var.managed_cache_version
  plan_name  = var.managed_cache_plan_name

  parameters = {
    sgw_acl = var.managed_cache_sgw_acl
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_redis_credential" "managed_cache" {
  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_redis_instance.managed_cache.instance_id
}
