terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_secretsmanager_instance" "this" {
  project_id = var.stackit_project_id
  name       = var.secrets_manager_instance_name
  acls       = length(var.secrets_manager_acl) > 0 ? var.secrets_manager_acl : null

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_secretsmanager_user" "this" {
  project_id    = var.stackit_project_id
  instance_id   = stackit_secretsmanager_instance.this.instance_id
  description   = var.secrets_manager_user_description
  write_enabled = var.secrets_manager_user_write_enabled
}
