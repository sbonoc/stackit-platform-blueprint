resource "stackit_ske_cluster" "foundation" {
  count = var.ske_enabled ? 1 : 0

  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = local.ske_cluster_name

  extensions = {
    dns = merge(
      {
        enabled = var.dns_enabled && length(local.dns_zone_fqdns) > 0
      },
      var.dns_enabled && length(local.dns_zone_fqdns) > 0 ? {
        zones = local.dns_zone_fqdns
      } : {}
    )
  }

  node_pools = [
    {
      name               = var.ske_default_node_pool_name
      machine_type       = var.ske_default_node_pool_machine_type
      minimum            = var.ske_default_node_pool_min
      maximum            = var.ske_default_node_pool_max
      availability_zones = var.ske_default_node_pool_availability_zones
    },
  ]
}

resource "stackit_ske_kubeconfig" "foundation" {
  count = var.ske_enabled ? 1 : 0

  project_id   = var.stackit_project_id
  region       = var.stackit_region
  cluster_name = local.ske_cluster_name
  depends_on   = [stackit_ske_cluster.foundation]
}

resource "stackit_dns_zone" "foundation" {
  for_each = var.dns_enabled ? {
    for zone in local.dns_zone_fqdns : zone => zone
  } : {}

  project_id = var.stackit_project_id
  name       = substr("${local.naming_prefix}-dns-${substr(sha1(each.value), 0, 8)}", 0, 63)
  dns_name   = each.value
}

resource "stackit_postgresflex_instance" "foundation" {
  count = var.postgres_enabled ? 1 : 0

  project_id      = var.stackit_project_id
  region          = var.stackit_region
  name            = "${local.naming_prefix}-${var.postgres_instance_name_suffix}"
  version         = var.postgres_version
  replicas        = var.postgres_replicas
  acl             = var.postgres_acl
  backup_schedule = var.postgres_backup_schedule

  flavor = {
    cpu = var.postgres_flavor_cpu
    ram = var.postgres_flavor_ram
  }

  storage = {
    class = var.postgres_storage_class
    size  = var.postgres_storage_size_gb
  }
}

resource "stackit_postgresflex_user" "foundation" {
  count = var.postgres_enabled ? 1 : 0

  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_postgresflex_instance.foundation[0].instance_id
  username    = var.postgres_username
  roles       = var.postgres_user_roles
}

resource "stackit_postgresflex_database" "foundation" {
  count = var.postgres_enabled ? 1 : 0

  project_id  = var.stackit_project_id
  region      = var.stackit_region
  instance_id = stackit_postgresflex_instance.foundation[0].instance_id
  name        = var.postgres_db_name
  owner       = var.postgres_username

  depends_on = [stackit_postgresflex_user.foundation]
}

resource "stackit_objectstorage_bucket" "foundation" {
  count = var.object_storage_enabled ? 1 : 0

  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = "${local.naming_prefix}-${var.object_storage_bucket_name_suffix}"
}

resource "stackit_objectstorage_credentials_group" "foundation" {
  count = var.object_storage_enabled ? 1 : 0

  project_id = var.stackit_project_id
  region     = var.stackit_region
  name       = "${local.naming_prefix}-${var.object_storage_credentials_group_name_suffix}"
}

resource "stackit_objectstorage_credential" "foundation" {
  count = var.object_storage_enabled ? 1 : 0

  project_id           = var.stackit_project_id
  region               = var.stackit_region
  credentials_group_id = stackit_objectstorage_credentials_group.foundation[0].credentials_group_id
  expiration_timestamp = var.object_storage_credential_expiration_timestamp
}

resource "stackit_secretsmanager_instance" "foundation" {
  count = var.secrets_manager_enabled ? 1 : 0

  project_id = var.stackit_project_id
  name       = "${local.naming_prefix}-${var.secrets_manager_instance_name_suffix}"
  acls       = length(var.secrets_manager_acl) > 0 ? var.secrets_manager_acl : null
}

resource "stackit_secretsmanager_user" "foundation" {
  count = var.secrets_manager_enabled ? 1 : 0

  project_id    = var.stackit_project_id
  instance_id   = stackit_secretsmanager_instance.foundation[0].instance_id
  description   = var.secrets_manager_user_description
  write_enabled = var.secrets_manager_user_write_enabled
}

resource "stackit_observability_instance" "foundation" {
  count = var.observability_enabled ? 1 : 0

  project_id                             = var.stackit_project_id
  name                                   = "${local.naming_prefix}-${var.observability_instance_name_suffix}"
  plan_name                              = var.observability_plan_name
  acl                                    = length(var.observability_acl) > 0 ? var.observability_acl : null
  grafana_admin_enabled                  = var.observability_grafana_admin_enabled
  logs_retention_days                    = var.observability_logs_retention_days
  metrics_retention_days                 = var.observability_metrics_retention_days
  metrics_retention_days_5m_downsampling = var.observability_metrics_retention_days_5m_downsampling
  metrics_retention_days_1h_downsampling = var.observability_metrics_retention_days_1h_downsampling
  traces_retention_days                  = var.observability_traces_retention_days
}

resource "stackit_observability_credential" "foundation" {
  count = var.observability_enabled ? 1 : 0

  project_id  = var.stackit_project_id
  instance_id = stackit_observability_instance.foundation[0].instance_id
  description = "Runtime credential managed by Terraform foundation."
}
