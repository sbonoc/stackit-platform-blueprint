terraform {
  required_version = ">= 1.13.0, < 2.0.0"

  required_providers {
    stackit = {
      source  = "stackitcloud/stackit"
      version = "= 0.88.0"
    }
  }

  backend "s3" {}
}
