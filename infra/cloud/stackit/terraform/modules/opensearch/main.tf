terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_opensearch_instance" "opensearch" {
  project_id = var.stackit_project_id
  name       = var.opensearch_instance_name
  version    = var.opensearch_version
  plan_name  = var.opensearch_plan_name

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_opensearch_credential" "opensearch" {
  project_id  = var.stackit_project_id
  instance_id = stackit_opensearch_instance.opensearch.instance_id
}
