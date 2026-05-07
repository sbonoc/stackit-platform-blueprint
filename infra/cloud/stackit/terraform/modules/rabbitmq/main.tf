terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_rabbitmq_instance" "rabbitmq" {
  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = var.rabbitmq_instance_name
  version    = var.rabbitmq_version
  plan_name  = var.rabbitmq_plan_name

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_rabbitmq_credential" "rabbitmq" {
  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_rabbitmq_instance.rabbitmq.instance_id
}
