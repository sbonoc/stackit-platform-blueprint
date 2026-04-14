#!/usr/bin/env python3
"""Render runtime contract secret env file from foundation Terraform outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ALLOWED_OUTPUTS: tuple[tuple[str, str], ...] = (
    ("ske_cluster_name", "ske_cluster_name"),
    ("postgres_host", "postgres_host"),
    ("postgres_port", "postgres_port"),
    ("postgres_username", "postgres_username"),
    ("postgres_password", "postgres_password"),
    ("postgres_database", "postgres_database"),
    ("keycloak_postgres_host", "KEYCLOAK_DATABASE_HOST"),
    ("keycloak_postgres_port", "KEYCLOAK_DATABASE_PORT"),
    ("keycloak_postgres_username", "KEYCLOAK_DATABASE_USERNAME"),
    ("keycloak_postgres_password", "KEYCLOAK_DATABASE_PASSWORD"),
    ("keycloak_postgres_database", "KEYCLOAK_DATABASE_NAME"),
    ("object_storage_bucket_name", "object_storage_bucket_name"),
    ("object_storage_access_key", "object_storage_access_key"),
    ("object_storage_secret_access_key", "object_storage_secret_access_key"),
    ("rabbitmq_instance_id", "rabbitmq_instance_id"),
    ("rabbitmq_host", "rabbitmq_host"),
    ("rabbitmq_port", "rabbitmq_port"),
    ("rabbitmq_username", "rabbitmq_username"),
    ("rabbitmq_password", "rabbitmq_password"),
    ("rabbitmq_uri", "rabbitmq_uri"),
    ("opensearch_instance_id", "opensearch_instance_id"),
    ("opensearch_dashboard_url", "opensearch_dashboard_url"),
    ("opensearch_host", "opensearch_host"),
    ("opensearch_hosts", "opensearch_hosts"),
    ("opensearch_port", "opensearch_port"),
    ("opensearch_scheme", "opensearch_scheme"),
    ("opensearch_uri", "opensearch_uri"),
    ("opensearch_username", "opensearch_username"),
    ("opensearch_password", "opensearch_password"),
    ("secrets_manager_instance_id", "secrets_manager_instance_id"),
    ("secrets_manager_username", "secrets_manager_username"),
    ("secrets_manager_password", "secrets_manager_password"),
    ("observability_instance_id", "observability_instance_id"),
    ("observability_grafana_url", "observability_grafana_url"),
    ("observability_credential_username", "observability_credential_username"),
    ("observability_credential_password", "observability_credential_password"),
    ("kms_key_ring_name", "kms_key_ring_name"),
    ("kms_key_name", "kms_key_name"),
    ("kms_key_ring_id", "kms_key_ring_id"),
    ("kms_key_id", "kms_key_id"),
)


def _render_scalar(value: object) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return None


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: stackit_runtime_secret_env.py <outputs_json_file> <output_env_file>", file=sys.stderr)
        return 2

    outputs_json_file = Path(sys.argv[1])
    output_env_file = Path(sys.argv[2])
    payload = json.loads(outputs_json_file.read_text(encoding="utf-8"))

    lines: list[str] = []
    for output_name, secret_key in ALLOWED_OUTPUTS:
        entry = payload.get(output_name)
        if not isinstance(entry, dict):
            continue
        if "value" not in entry:
            continue
        rendered = _render_scalar(entry.get("value"))
        if rendered is None or rendered == "" or "\n" in rendered:
            continue
        lines.append(f"{secret_key}={rendered}")

    keycloak_admin_password = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "")
    if keycloak_admin_password and "\n" not in keycloak_admin_password:
        lines.append(f"KEYCLOAK_ADMIN_PASSWORD={keycloak_admin_password}")

    output_env_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
