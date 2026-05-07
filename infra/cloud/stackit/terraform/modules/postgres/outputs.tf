output "postgres_instance_id" {
  description = "Provisioned PostgreSQL Flex instance identifier."
  value       = stackit_postgresflex_instance.postgres.instance_id
}

output "postgres_host" {
  description = "Provisioned PostgreSQL Flex host."
  value       = stackit_postgresflex_user.postgres.host
}

output "postgres_port" {
  description = "Provisioned PostgreSQL Flex port."
  value       = stackit_postgresflex_user.postgres.port
}

output "postgres_username" {
  description = "Provisioned PostgreSQL Flex runtime username."
  value       = stackit_postgresflex_user.postgres.username
}

output "postgres_password" {
  description = "Provisioned PostgreSQL Flex runtime password."
  sensitive   = true
  value       = stackit_postgresflex_user.postgres.password
}

output "postgres_database" {
  description = "Provisioned PostgreSQL Flex database name."
  value       = stackit_postgresflex_database.postgres.name
}
