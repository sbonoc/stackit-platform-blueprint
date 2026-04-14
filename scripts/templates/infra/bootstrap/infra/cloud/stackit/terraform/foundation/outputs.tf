output "foundation_provider_coverage" {
  description = "Provider coverage contract for optional modules in STACKIT foundation."
  value       = local.foundation_provider_coverage
}

output "module_contracts" {
  description = "Per-module execution contracts (disabled, stackit-provider, fallback)."
  value       = local.module_contracts
}

output "ske_cluster_name" {
  description = "Provisioned SKE cluster name."
  value       = var.ske_enabled ? stackit_ske_cluster.foundation[0].name : null
}

output "ske_egress_address_ranges" {
  description = "Provisioned SKE egress CIDR ranges."
  value       = var.ske_enabled ? stackit_ske_cluster.foundation[0].egress_address_ranges : []
}

output "ske_kubeconfig" {
  description = "Provisioned SKE kubeconfig used by runtime deployment wrappers."
  sensitive   = true
  value       = var.ske_enabled ? stackit_ske_kubeconfig.foundation[0].kube_config : null
}

output "dns_zone_ids" {
  description = "Provisioned DNS zone identifiers keyed by FQDN."
  value       = { for zone, resource in stackit_dns_zone.foundation : zone => resource.zone_id }
}

output "postgres_instance_id" {
  description = "Provisioned PostgreSQL Flex instance identifier."
  value       = var.postgres_enabled ? stackit_postgresflex_instance.foundation[0].instance_id : null
}

output "postgres_host" {
  description = "Provisioned PostgreSQL Flex host."
  value       = var.postgres_enabled ? stackit_postgresflex_user.foundation[0].host : null
}

output "postgres_port" {
  description = "Provisioned PostgreSQL Flex port."
  value       = var.postgres_enabled ? stackit_postgresflex_user.foundation[0].port : null
}

output "postgres_username" {
  description = "Provisioned PostgreSQL Flex runtime username."
  value       = var.postgres_enabled ? stackit_postgresflex_user.foundation[0].username : null
}

output "postgres_password" {
  description = "Provisioned PostgreSQL Flex runtime password."
  sensitive   = true
  value       = var.postgres_enabled ? stackit_postgresflex_user.foundation[0].password : null
}

output "postgres_database" {
  description = "Provisioned PostgreSQL Flex database name."
  value       = var.postgres_enabled ? stackit_postgresflex_database.foundation[0].name : null
}

output "keycloak_postgres_instance_id" {
  description = "Provisioned dedicated PostgreSQL Flex instance identifier for Keycloak."
  value       = stackit_postgresflex_instance.keycloak.instance_id
}

output "keycloak_postgres_host" {
  description = "Provisioned dedicated PostgreSQL Flex host for Keycloak."
  value       = stackit_postgresflex_user.keycloak.host
}

output "keycloak_postgres_port" {
  description = "Provisioned dedicated PostgreSQL Flex port for Keycloak."
  value       = stackit_postgresflex_user.keycloak.port
}

output "keycloak_postgres_username" {
  description = "Provisioned dedicated PostgreSQL Flex username for Keycloak."
  value       = stackit_postgresflex_user.keycloak.username
}

output "keycloak_postgres_password" {
  description = "Provisioned dedicated PostgreSQL Flex password for Keycloak."
  sensitive   = true
  value       = stackit_postgresflex_user.keycloak.password
}

output "keycloak_postgres_database" {
  description = "Provisioned dedicated PostgreSQL Flex database name for Keycloak."
  value       = stackit_postgresflex_database.keycloak.name
}

output "object_storage_bucket_name" {
  description = "Provisioned Object Storage bucket name."
  value       = var.object_storage_enabled ? stackit_objectstorage_bucket.foundation[0].name : null
}

output "object_storage_access_key" {
  description = "Provisioned Object Storage access key."
  sensitive   = true
  value       = var.object_storage_enabled ? stackit_objectstorage_credential.foundation[0].access_key : null
}

output "object_storage_secret_access_key" {
  description = "Provisioned Object Storage secret access key."
  sensitive   = true
  value       = var.object_storage_enabled ? stackit_objectstorage_credential.foundation[0].secret_access_key : null
}

output "rabbitmq_instance_id" {
  description = "Provisioned RabbitMQ instance identifier."
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_instance.foundation[0].instance_id : null
}

output "rabbitmq_host" {
  description = "Provisioned RabbitMQ broker host."
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_credential.foundation[0].host : null
}

output "rabbitmq_port" {
  description = "Provisioned RabbitMQ broker port."
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_credential.foundation[0].port : null
}

output "rabbitmq_username" {
  description = "Provisioned RabbitMQ runtime username."
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_credential.foundation[0].username : null
}

output "rabbitmq_password" {
  description = "Provisioned RabbitMQ runtime password."
  sensitive   = true
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_credential.foundation[0].password : null
}

output "rabbitmq_uri" {
  description = "Provisioned RabbitMQ runtime URI."
  sensitive   = true
  value       = var.rabbitmq_enabled ? stackit_rabbitmq_credential.foundation[0].uri : null
}

output "opensearch_instance_id" {
  description = "Provisioned OpenSearch instance identifier."
  value       = var.opensearch_enabled ? stackit_opensearch_instance.foundation[0].instance_id : null
}

output "opensearch_dashboard_url" {
  description = "Provisioned OpenSearch dashboard URL."
  value       = var.opensearch_enabled ? stackit_opensearch_instance.foundation[0].dashboard_url : null
}

output "opensearch_host" {
  description = "Provisioned OpenSearch endpoint host."
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].host : null
}

output "opensearch_hosts" {
  description = "Provisioned OpenSearch endpoint hosts list."
  value       = var.opensearch_enabled ? join(",", stackit_opensearch_credential.foundation[0].hosts) : null
}

output "opensearch_port" {
  description = "Provisioned OpenSearch endpoint port."
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].port : null
}

output "opensearch_scheme" {
  description = "Provisioned OpenSearch endpoint scheme."
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].scheme : null
}

output "opensearch_uri" {
  description = "Provisioned OpenSearch endpoint URI."
  sensitive   = true
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].uri : null
}

output "opensearch_username" {
  description = "Provisioned OpenSearch runtime username."
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].username : null
}

output "opensearch_password" {
  description = "Provisioned OpenSearch runtime password."
  sensitive   = true
  value       = var.opensearch_enabled ? stackit_opensearch_credential.foundation[0].password : null
}

output "secrets_manager_instance_id" {
  description = "Provisioned Secrets Manager instance identifier."
  value       = var.secrets_manager_enabled ? stackit_secretsmanager_instance.foundation[0].instance_id : null
}

output "secrets_manager_username" {
  description = "Provisioned Secrets Manager runtime username."
  sensitive   = true
  value       = var.secrets_manager_enabled ? stackit_secretsmanager_user.foundation[0].username : null
}

output "secrets_manager_password" {
  description = "Provisioned Secrets Manager runtime password."
  sensitive   = true
  value       = var.secrets_manager_enabled ? stackit_secretsmanager_user.foundation[0].password : null
}

output "observability_instance_id" {
  description = "Provisioned Observability instance identifier."
  value       = var.observability_enabled ? stackit_observability_instance.foundation[0].instance_id : null
}

output "observability_grafana_url" {
  description = "Provisioned Observability Grafana URL."
  value       = var.observability_enabled ? stackit_observability_instance.foundation[0].grafana_url : null
}

output "observability_credential_username" {
  description = "Provisioned Observability runtime credential username."
  sensitive   = true
  value       = var.observability_enabled ? stackit_observability_credential.foundation[0].username : null
}

output "observability_credential_password" {
  description = "Provisioned Observability runtime credential password."
  sensitive   = true
  value       = var.observability_enabled ? stackit_observability_credential.foundation[0].password : null
}

output "kms_key_ring_name" {
  description = "Provisioned KMS keyring display name."
  value       = var.kms_enabled ? var.kms_key_ring_name : null
}

output "kms_key_name" {
  description = "Provisioned KMS key display name."
  value       = var.kms_enabled ? var.kms_key_name : null
}

output "kms_key_ring_id" {
  description = "Provisioned KMS keyring identifier."
  value       = var.kms_enabled ? stackit_kms_keyring.foundation[0].keyring_id : null
}

output "kms_key_id" {
  description = "Provisioned KMS key identifier."
  value       = var.kms_enabled ? stackit_kms_key.foundation[0].key_id : null
}
