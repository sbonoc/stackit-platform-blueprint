#!/usr/bin/env bash
set -euo pipefail

workflows_api_init_env() {
  set_default_env STACKIT_WORKFLOWS_API_BASE_URL "https://workflows.api.stackit.cloud/v1alpha"
  set_default_env STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS "30"
  set_default_env STACKIT_WORKFLOWS_API_TOKEN "${STACKIT_WORKFLOWS_ACCESS_TOKEN:-}"

  if ! [[ "$STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS" =~ ^[0-9]+$ ]]; then
    log_fatal "STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS must be numeric"
  fi

  if tooling_is_execution_enabled; then
    require_command curl
    require_env_vars STACKIT_WORKFLOWS_API_TOKEN
  fi
}

workflows_api_endpoint() {
  local path="$1"
  printf '%s%s' "${STACKIT_WORKFLOWS_API_BASE_URL%/}" "$path"
}

workflows_api_request() {
  local method="$1"
  local path="$2"
  local payload_file="$3"
  local response_file="$4"
  local allowed_codes_csv="${5:-200,201}"

  local url
  url="$(workflows_api_endpoint "$path")"

  local curl_args=(
    -sS
    --connect-timeout "$STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS"
    --max-time "$STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS"
    -X "$method"
    -H "Accept: application/json"
    -H "Authorization: Bearer $STACKIT_WORKFLOWS_API_TOKEN"
    -w "%{http_code}"
    -o "$response_file"
  )

  if [[ -n "$payload_file" ]]; then
    curl_args+=(
      -H "Content-Type: application/json"
      --data-binary "@$payload_file"
    )
  fi

  local http_code
  if ! http_code="$(curl "${curl_args[@]}" "$url")"; then
    log_error "workflows API transport error method=$method url=$url"
    return 1
  fi

  if [[ ",${allowed_codes_csv}," != *",${http_code},"* ]]; then
    local body_excerpt
    body_excerpt="$(tr '\n' ' ' <"$response_file" | sed -E 's/[[:space:]]+/ /g' | cut -c1-320)"
    log_error "workflows API request failed method=$method url=$url status=$http_code body=$body_excerpt"
    return 1
  fi

  log_metric "workflows_api_request_total" 1 "method=$method status=$http_code"
  printf '%s' "$http_code"
}

workflows_api_json_pick() {
  local json_file="$1"
  local default_value="$2"
  shift 2 || true

  python3 - "$json_file" "$default_value" "$@" <<'PY'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
default = sys.argv[2]
keys = sys.argv[3:]

try:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
except Exception:
    print(default)
    raise SystemExit(0)


def pick_key(value, dotted):
    current = value
    for part in dotted.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return None
            idx = int(part)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
            continue
        return None
    return current

for key in keys:
    value = pick_key(payload, key)
    if value is None:
        continue
    if isinstance(value, str):
        if value.strip() == "":
            continue
        print(value)
        raise SystemExit(0)
    if isinstance(value, (int, float, bool)):
        print(str(value))
        raise SystemExit(0)

print(default)
PY
}

workflows_api_count_instances_with_status() {
  local json_file="$1"
  local expected_status="$2"

  python3 - "$json_file" "$expected_status" <<'PY'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
expected = sys.argv[2].strip().lower()

try:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
except Exception:
    print("0")
    raise SystemExit(0)

if isinstance(payload, list):
    items = payload
elif isinstance(payload, dict):
    items = payload.get("items") or payload.get("instances") or payload.get("data") or []
else:
    items = []

count = 0
for item in items:
    if not isinstance(item, dict):
        continue
    status = item.get("status")
    if status is None and isinstance(item.get("state"), str):
        status = item.get("state")
    if not isinstance(status, str):
        continue
    if status.strip().lower() == expected:
        count += 1

print(str(count))
PY
}

workflows_api_find_instance_id_by_display_name() {
  local json_file="$1"
  local display_name="$2"

  python3 - "$json_file" "$display_name" <<'PY'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
expected_name = sys.argv[2]

try:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
except Exception:
    print("")
    raise SystemExit(0)

if isinstance(payload, list):
    items = payload
elif isinstance(payload, dict):
    items = payload.get("items") or payload.get("instances") or payload.get("data") or []
else:
    items = []

for item in items:
    if not isinstance(item, dict):
        continue
    actual_name = item.get("displayName") or item.get("name") or item.get("instanceName")
    if actual_name != expected_name:
        continue
    for key in ("id", "instanceId", "instance_id"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            print(value)
            raise SystemExit(0)

print("")
PY
}
