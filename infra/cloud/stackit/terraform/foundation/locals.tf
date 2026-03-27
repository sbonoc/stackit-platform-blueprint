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

  dns_zone_fqdns = sort(distinct(var.dns_zone_fqdns))

  module_enablement = {
    observability        = var.observability_enabled
    workflows            = var.workflows_enabled
    langfuse             = var.langfuse_enabled
    postgres             = var.postgres_enabled
    neo4j                = var.neo4j_enabled
    object-storage       = var.object_storage_enabled
    rabbitmq             = var.rabbitmq_enabled
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
      fallback_strategy          = "manage ingress/gateway endpoints from runtime manifests"
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
