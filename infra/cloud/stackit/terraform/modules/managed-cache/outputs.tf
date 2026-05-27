output "managed_cache_instance_id" {
  description = "Provisioned Redis instance identifier."
  value       = stackit_redis_instance.managed_cache.instance_id
}

output "managed_cache_host" {
  description = "Provisioned Redis host."
  value       = stackit_redis_credential.managed_cache.host
}

output "managed_cache_port" {
  description = "Provisioned Redis port."
  value       = stackit_redis_credential.managed_cache.port
}

output "managed_cache_username" {
  description = "Provisioned Redis runtime username."
  value       = stackit_redis_credential.managed_cache.username
}

output "managed_cache_password" {
  description = "Provisioned Redis runtime password."
  sensitive   = true
  value       = stackit_redis_credential.managed_cache.password
}

output "managed_cache_uri" {
  description = "Provisioned Redis runtime URI."
  sensitive   = true
  value       = stackit_redis_credential.managed_cache.uri
}
