terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

resource "stackit_objectstorage_bucket" "object_storage" {
  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = var.bucket_name
}

resource "stackit_objectstorage_credentials_group" "object_storage" {
  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = var.credentials_group_name
}

resource "stackit_objectstorage_credential" "object_storage" {
  project_id           = var.stackit_project_id
  region               = var.stackit_region
  credentials_group_id = stackit_objectstorage_credentials_group.object_storage.credentials_group_id
  expiration_timestamp = var.expiration_timestamp
}
