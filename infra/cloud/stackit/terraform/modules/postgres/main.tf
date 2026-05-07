terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_postgresflex_instance" "postgres" {
  project_id      = var.stackit_project_id
  region          = var.stackit_region
  name            = var.postgres_instance_name
  version         = var.postgres_version
  replicas        = var.postgres_replicas
  acl             = var.postgres_acl
  backup_schedule = var.postgres_backup_schedule

  flavor = {
    cpu = var.postgres_flavor_cpu
    ram = var.postgres_flavor_ram
  }

  storage = {
    class = var.postgres_storage_class
    size  = var.postgres_storage_size_gb
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_postgresflex_user" "postgres" {
  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_postgresflex_instance.postgres.instance_id
  username    = var.postgres_username
  roles       = var.postgres_user_roles
}

resource "stackit_postgresflex_database" "postgres" {
  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_postgresflex_instance.postgres.instance_id
  name        = var.postgres_db_name
  owner       = var.postgres_username

  depends_on = [stackit_postgresflex_user.postgres]
}
