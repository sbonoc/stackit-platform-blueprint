output "opensearch_instance_id" {
  description = "Provisioned OpenSearch instance identifier."
  value       = stackit_opensearch_instance.opensearch.instance_id
}

output "opensearch_dashboard_url" {
  description = "Provisioned OpenSearch dashboard URL."
  value       = stackit_opensearch_instance.opensearch.dashboard_url
}

output "opensearch_host" {
  description = "Provisioned OpenSearch host."
  value       = stackit_opensearch_credential.opensearch.host
}

output "opensearch_hosts" {
  description = "Comma-separated list of provisioned OpenSearch hosts."
  value       = join(",", stackit_opensearch_credential.opensearch.hosts)
}

output "opensearch_port" {
  description = "Provisioned OpenSearch port."
  value       = stackit_opensearch_credential.opensearch.port
}

output "opensearch_scheme" {
  description = "Provisioned OpenSearch connection scheme."
  value       = stackit_opensearch_credential.opensearch.scheme
}

output "opensearch_uri" {
  description = "Provisioned OpenSearch connection URI."
  value       = stackit_opensearch_credential.opensearch.uri
}

output "opensearch_username" {
  description = "Provisioned OpenSearch runtime username."
  value       = stackit_opensearch_credential.opensearch.username
}

output "opensearch_password" {
  description = "Provisioned OpenSearch runtime password."
  sensitive   = true
  value       = stackit_opensearch_credential.opensearch.password
}
