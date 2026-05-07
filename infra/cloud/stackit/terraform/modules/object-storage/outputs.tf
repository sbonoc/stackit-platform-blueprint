output "bucket_name" {
  description = "Provisioned object storage bucket name."
  value       = stackit_objectstorage_bucket.object_storage.name
}

output "endpoint_url" {
  description = "S3-compatible endpoint URL for the provisioned bucket region."
  value       = "https://object-storage.${var.stackit_region}.onstackit.cloud"
}

output "access_key" {
  description = "Provisioned object storage access key."
  sensitive   = true
  value       = stackit_objectstorage_credential.object_storage.access_key
}

output "secret_access_key" {
  description = "Provisioned object storage secret access key."
  sensitive   = true
  value       = stackit_objectstorage_credential.object_storage.secret_access_key
}

output "region" {
  description = "STACKIT region where the object storage bucket is provisioned."
  value       = var.stackit_region
}
