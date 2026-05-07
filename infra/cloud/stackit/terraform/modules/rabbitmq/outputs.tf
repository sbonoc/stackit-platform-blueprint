output "rabbitmq_instance_id" {
  description = "Provisioned RabbitMQ instance identifier."
  value       = stackit_rabbitmq_instance.rabbitmq.instance_id
}

output "rabbitmq_host" {
  description = "Provisioned RabbitMQ broker host."
  value       = stackit_rabbitmq_credential.rabbitmq.host
}

output "rabbitmq_port" {
  description = "Provisioned RabbitMQ broker port."
  value       = stackit_rabbitmq_credential.rabbitmq.port
}

output "rabbitmq_username" {
  description = "Provisioned RabbitMQ runtime username."
  value       = stackit_rabbitmq_credential.rabbitmq.username
}

output "rabbitmq_password" {
  description = "Provisioned RabbitMQ runtime password."
  sensitive   = true
  value       = stackit_rabbitmq_credential.rabbitmq.password
}

output "rabbitmq_uri" {
  description = "Provisioned RabbitMQ runtime URI."
  sensitive   = true
  value       = stackit_rabbitmq_credential.rabbitmq.uri
}

output "rabbitmq_management_url" {
  description = "Provisioned RabbitMQ management dashboard URL."
  value       = stackit_rabbitmq_credential.rabbitmq.management
}
