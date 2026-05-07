variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "stackit_region" {
  description = "STACKIT region for the object storage resources."
  type        = string
  default     = "eu01"
}

variable "bucket_name" {
  description = "Canonical object storage bucket name."
  type        = string
}

variable "credentials_group_name" {
  description = "Canonical credentials group name for the bucket."
  type        = string
}

variable "expiration_timestamp" {
  description = "Optional credential expiration timestamp in RFC3339 format."
  type        = string
  default     = null
}
