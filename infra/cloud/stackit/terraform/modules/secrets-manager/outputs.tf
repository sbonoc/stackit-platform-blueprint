output "instance_id" {
  description = "Provisioned Secrets Manager instance identifier."
  value       = stackit_secretsmanager_instance.this.instance_id
}

output "username" {
  description = "Provisioned Secrets Manager user credential username."
  value       = stackit_secretsmanager_user.this.username
}

output "password" {
  description = "Provisioned Secrets Manager user credential password."
  sensitive   = true
  value       = stackit_secretsmanager_user.this.password
}
