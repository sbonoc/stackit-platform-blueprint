bucket       = "{{STACKIT_TFSTATE_BUCKET}}"
key          = "{{STACKIT_TFSTATE_KEY_PREFIX}}/prod/foundation.tfstate"
region       = "{{STACKIT_REGION}}"
use_lockfile = true

endpoints = {
  s3 = "https://object.storage.{{STACKIT_REGION}}.onstackit.cloud"
}

skip_credentials_validation = true
skip_metadata_api_check     = true
skip_region_validation      = true
skip_requesting_account_id  = true
use_path_style              = true
