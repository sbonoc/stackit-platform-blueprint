locals {
  _sm_vault_address = var.secrets_manager_enabled ? (
    "https://secrets.${var.stackit_region}.onstackit.cloud/${local.secrets_manager_instance_name}"
  ) : "https://127.0.0.1:8200"
  _sm_vault_token = try(stackit_secretsmanager_user.foundation[0].password, "UNUSED_SM_DISABLED")
}

provider "vault" {
  address         = local._sm_vault_address
  token           = local._sm_vault_token
  skip_tls_verify = !var.secrets_manager_enabled
}

resource "vault_kv_secret_v2" "observability_credentials" {
  count = (var.secrets_manager_enabled && var.observability_enabled) ? 1 : 0

  mount = "secret"
  name  = "observability/otel-credentials"

  data_json = jsonencode({
    username         = stackit_observability_credential.foundation[0].username
    password         = stackit_observability_credential.foundation[0].password
    METRICS_PUSH_URL = stackit_observability_instance.foundation[0].metrics_push_url
    LOGS_PUSH_URL    = stackit_observability_instance.foundation[0].logs_push_url
    TRACES_PUSH_URL  = stackit_observability_instance.foundation[0].otlp_grpc_traces_url
  })

  depends_on = [
    stackit_secretsmanager_instance.foundation,
    stackit_secretsmanager_user.foundation,
    stackit_observability_instance.foundation,
    stackit_observability_credential.foundation,
  ]
}
