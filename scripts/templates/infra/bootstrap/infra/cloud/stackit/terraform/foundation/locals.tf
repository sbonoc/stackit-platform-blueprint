locals {
  normalized_tenant   = lower(replace(trimspace(var.tenant_slug), "_", "-"))
  normalized_platform = lower(replace(trimspace(var.platform_slug), "_", "-"))
  naming_prefix       = "${local.normalized_tenant}-${local.normalized_platform}-${var.environment}"

  tags = {
    env       = var.environment
    platform  = local.normalized_platform
    tenant    = local.normalized_tenant
    managedBy = "terraform"
    scope     = "foundation"
  }

  # STACKIT SKE currently enforces a short cluster-name limit (<=11 chars).
  ske_cluster_name = "k${substr(sha1(local.naming_prefix), 0, 10)}"
  # Optional naming overrides default to null, so try() is safer than coalesce()
  # when disabled modules leave the variables unset during plan/apply.
  postgres_instance_name_override = try(trimspace(var.postgres_instance_name), "")
  postgres_instance_name = (
    local.postgres_instance_name_override != ""
    ? local.postgres_instance_name_override
    : "${local.naming_prefix}-${var.postgres_instance_name_suffix}"
  )
  postgres_acl_effective = (
    var.postgres_enabled
    ? distinct(concat(
      var.ske_enabled ? stackit_ske_cluster.foundation[0].egress_address_ranges : [],
      var.postgres_acl,
    ))
    : []
  )
  keycloak_postgres_instance_name = "${local.naming_prefix}-keycloak-postgres"
  keycloak_postgres_acl_effective = distinct(concat(
    var.ske_enabled ? stackit_ske_cluster.foundation[0].egress_address_ranges : [],
    var.postgres_acl,
  ))
  object_storage_bucket_name_override = try(trimspace(var.object_storage_bucket_name), "")
  object_storage_bucket_name = (
    local.object_storage_bucket_name_override != ""
    ? local.object_storage_bucket_name_override
    : "${local.naming_prefix}-${var.object_storage_bucket_name_suffix}"
  )
  object_storage_credentials_group_name = "${substr(local.normalized_platform, 0, 8)}-${var.environment}-creds-${substr(sha1("${local.naming_prefix}-${var.object_storage_credentials_group_name_suffix}"), 0, 6)}"
  secrets_manager_instance_name_override = try(trimspace(var.secrets_manager_instance_name), "")
  secrets_manager_instance_name = (
    local.secrets_manager_instance_name_override != ""
    ? local.secrets_manager_instance_name_override
    : "${local.naming_prefix}-${var.secrets_manager_instance_name_suffix}"
  )
  opensearch_instance_name_override = try(trimspace(var.opensearch_instance_name), "")
  opensearch_instance_name = (
    local.opensearch_instance_name_override != ""
    ? local.opensearch_instance_name_override
    : "${local.naming_prefix}-${var.opensearch_instance_name_suffix}"
  )

  dns_zone_fqdns = sort(distinct(var.dns_zone_fqdns))
  dns_zone_dns_names = {
    for zone in local.dns_zone_fqdns : zone => trimsuffix(zone, ".")
  }

  module_enablement = {
    observability        = var.observability_enabled
    workflows            = var.workflows_enabled
    langfuse             = var.langfuse_enabled
    postgres             = var.postgres_enabled
    neo4j                = var.neo4j_enabled
    object-storage       = var.object_storage_enabled
    rabbitmq             = var.rabbitmq_enabled
    opensearch           = var.opensearch_enabled
    dns                  = var.dns_enabled
    public-endpoints     = var.public_endpoints_enabled
    secrets-manager      = var.secrets_manager_enabled
    kms                  = var.kms_enabled
    identity-aware-proxy = var.identity_aware_proxy_enabled
  }

  foundation_provider_coverage = {
    observability = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_observability_instance",
        "stackit_observability_credential",
      ]
      fallback_strategy = "none"
    }
    workflows = {
      stackit_provider_supported = false
      stackit_resource_types     = []
      fallback_strategy          = "use managed Workflows API + ArgoCD runtime integration until provider resource support is available"
    }
    langfuse = {
      stackit_provider_supported = false
      stackit_resource_types     = []
      fallback_strategy          = "deploy Langfuse on SKE via ArgoCD and wire managed STACKIT dependencies"
    }
    postgres = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_postgresflex_instance",
        "stackit_postgresflex_database",
        "stackit_postgresflex_user",
      ]
      fallback_strategy = "none"
    }
    neo4j = {
      stackit_provider_supported = false
      stackit_resource_types     = []
      fallback_strategy          = "deploy Neo4j on SKE via ArgoCD"
    }
    object-storage = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_objectstorage_bucket",
        "stackit_objectstorage_credential",
        "stackit_objectstorage_credentials_group",
      ]
      fallback_strategy = "none"
    }
    rabbitmq = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_rabbitmq_instance",
        "stackit_rabbitmq_credential",
      ]
      fallback_strategy = "none"
    }
    opensearch = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_opensearch_instance",
        "stackit_opensearch_credential",
      ]
      fallback_strategy = "none"
    }
    dns = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_dns_zone",
      ]
      fallback_strategy = "none"
    }
    public-endpoints = {
      stackit_provider_supported = false
      stackit_resource_types     = []
      fallback_strategy          = "manage shared Gateway API edge from runtime manifests"
    }
    secrets-manager = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_secretsmanager_instance",
        "stackit_secretsmanager_user",
      ]
      fallback_strategy = "none"
    }
    kms = {
      stackit_provider_supported = true
      stackit_resource_types = [
        "stackit_kms_keyring",
        "stackit_kms_key",
      ]
      fallback_strategy = "none"
    }
    identity-aware-proxy = {
      stackit_provider_supported = false
      stackit_resource_types     = []
      fallback_strategy          = "deploy IAP on SKE and wire OIDC with Keycloak"
    }
  }

  module_contracts = {
    for module_name, enabled in local.module_enablement :
    module_name => {
      enabled            = enabled
      provider_supported = local.foundation_provider_coverage[module_name].stackit_provider_supported
      effective_mode = (
        enabled ? (
          local.foundation_provider_coverage[module_name].stackit_provider_supported ? "stackit-provider" : "fallback"
        ) : "disabled"
      )
      fallback_strategy = local.foundation_provider_coverage[module_name].fallback_strategy
    }
  }
}
