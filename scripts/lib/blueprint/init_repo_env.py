"""Environment-file synthesis helpers for blueprint init-repo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex

from scripts.lib.blueprint.cli_support import ChangeSummary
from scripts.lib.blueprint.contract_schema import load_module_contract
from scripts.lib.blueprint.init_repo_contract import load_blueprint_contract_for_init
from scripts.lib.blueprint.init_repo_io import apply_file_update

CORE_SENSITIVE_ENV_NAMES = {
    "STACKIT_SERVICE_ACCOUNT_KEY",
    "STACKIT_SERVICE_ACCOUNT_TOKEN",
    "STACKIT_TFSTATE_ACCESS_KEY_ID",
    "STACKIT_TFSTATE_SECRET_ACCESS_KEY",
}

# Keep generated-consumer first-run deterministic when optional modules are
# enabled: required module env vars should be pre-seeded with safe defaults or
# placeholders, not left empty.
MODULE_REQUIRED_ENV_DEFAULTS = {
    "DNS_ZONE_NAME": "marketplace-dev",
    "DNS_ZONE_FQDN": "marketplace.local.",
    "IAP_UPSTREAM_URL": "http://catalog.apps.svc.cluster.local:8080",
    "IAP_COOKIE_SECRET": "0123456789abcdef0123456789abcdef",
    "KEYCLOAK_ISSUER_URL": "https://keycloak.example/realms/platform",
    "KEYCLOAK_CLIENT_ID": "blueprint-client",
    "KEYCLOAK_CLIENT_SECRET": "blueprint-client-secret",
    "KMS_KEY_RING_NAME": "marketplace-ring",
    "KMS_KEY_NAME": "marketplace-key",
    "LANGFUSE_PUBLIC_DOMAIN": "langfuse.example.com",
    "LANGFUSE_OIDC_ISSUER_URL": "https://keycloak.example/realms/platform",
    "LANGFUSE_OIDC_CLIENT_ID": "langfuse-client",
    "LANGFUSE_OIDC_CLIENT_SECRET": "langfuse-client-secret",
    "LANGFUSE_DATABASE_URL": "postgresql://langfuse:langfuse-password@postgres.internal:5432/langfuse",
    "LANGFUSE_SALT": "langfuse-salt-0123456789",
    "LANGFUSE_ENCRYPTION_KEY": "langfuse-encryption-key-0123456789",
    "LANGFUSE_NEXTAUTH_SECRET": "langfuse-nextauth-secret",
    "NEO4J_AUTH_USERNAME": "neo4j",
    "NEO4J_AUTH_PASSWORD": "neo4j-password",
    "OBJECT_STORAGE_BUCKET_NAME": "marketplace-assets",
    "POSTGRES_INSTANCE_NAME": "blueprint-postgres",
    "POSTGRES_DB_NAME": "platform",
    "POSTGRES_USER": "platform",
    "POSTGRES_PASSWORD": "platform-password",
    "PUBLIC_ENDPOINTS_BASE_DOMAIN": "apps.local",
    "RABBITMQ_INSTANCE_NAME": "marketplace-rabbitmq",
    "SECRETS_MANAGER_INSTANCE_NAME": "marketplace-secrets",
    "STACKIT_WORKFLOWS_DAGS_REPO_URL": "https://github.com/example-org/example-repo.git",
    "STACKIT_WORKFLOWS_DAGS_REPO_BRANCH": "main",
    "STACKIT_WORKFLOWS_DAGS_REPO_USERNAME": "workflows-user",
    "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN": "workflows-token",
    "STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL": "https://keycloak.example/realms/platform/.well-known/openid-configuration",
    "STACKIT_WORKFLOWS_OIDC_CLIENT_ID": "workflows-client",
    "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET": "workflows-client-secret",
    "STACKIT_OBSERVABILITY_INSTANCE_ID": "obs-dev",
}

MODULE_REQUIRED_SENSITIVE_ENV_NAMES = {
    "POSTGRES_PASSWORD",
    "NEO4J_AUTH_PASSWORD",
    "IAP_COOKIE_SECRET",
    "KEYCLOAK_CLIENT_SECRET",
    "LANGFUSE_OIDC_CLIENT_SECRET",
    "LANGFUSE_DATABASE_URL",
    "LANGFUSE_SALT",
    "LANGFUSE_ENCRYPTION_KEY",
    "LANGFUSE_NEXTAUTH_SECRET",
    "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN",
    "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET",
}


def shell_assignment(name: str, value: str) -> str:
    if not value:
        return f"{name}=\n"
    return f"{name}={shlex.quote(value)}\n"


def defaults_env_identity_specs(args: argparse.Namespace) -> list[tuple[str, str]]:
    return [
        ("BLUEPRINT_REPO_NAME", args.repo_name),
        ("BLUEPRINT_GITHUB_ORG", args.github_org),
        ("BLUEPRINT_GITHUB_REPO", args.github_repo),
        ("BLUEPRINT_DEFAULT_BRANCH", args.default_branch),
        ("BLUEPRINT_DOCS_TITLE", args.docs_title),
        ("BLUEPRINT_DOCS_TAGLINE", args.docs_tagline),
        ("BLUEPRINT_STACKIT_REGION", args.stackit_region),
        ("BLUEPRINT_STACKIT_TENANT_SLUG", args.stackit_tenant_slug),
        ("BLUEPRINT_STACKIT_PLATFORM_SLUG", args.stackit_platform_slug),
        ("BLUEPRINT_STACKIT_PROJECT_ID", args.stackit_project_id),
        ("BLUEPRINT_STACKIT_TFSTATE_BUCKET", args.stackit_tfstate_bucket),
        ("BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX", args.stackit_tfstate_key_prefix),
    ]


def defaults_env_module_flag_specs(
    repo_root: Path,
    module_enablement: dict[str, bool],
) -> list[tuple[str, str]]:
    contract = load_blueprint_contract_for_init(repo_root)
    specs: list[tuple[str, str]] = []
    for module in contract.optional_modules.modules.values():
        specs.append((module.enable_flag, str(module_enablement[module.module_id]).lower()))
    return specs


def _module_required_env_value(name: str) -> str:
    explicit_value = os.environ.get(name)
    if explicit_value:
        return explicit_value
    return MODULE_REQUIRED_ENV_DEFAULTS.get(name, "")


def _is_sensitive_module_required_env(name: str) -> bool:
    if name in MODULE_REQUIRED_SENSITIVE_ENV_NAMES:
        return True
    return any(marker in name for marker in ("_PASSWORD", "_SECRET", "_TOKEN"))


def enabled_module_required_env_specs(
    repo_root: Path,
    module_enablement: dict[str, bool],
) -> list[tuple[str, str]]:
    contract = load_blueprint_contract_for_init(repo_root)
    specs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for module in contract.optional_modules.modules.values():
        if not module_enablement[module.module_id]:
            continue
        module_contract = load_module_contract(repo_root / module.paths["contract_path"], repo_root)
        for env_name in module_contract.required_env:
            if env_name in seen:
                continue
            seen.add(env_name)
            specs.append((env_name, _module_required_env_value(env_name)))
    return specs


def render_defaults_env_file_content(
    identity_specs: list[tuple[str, str]],
    module_flag_specs: list[tuple[str, str]],
    module_required_specs: list[tuple[str, str]],
) -> str:
    lines = [
        "# Repository defaults tracked in Git for this generated consumer.\n",
        "# Auto-loaded by blueprint-init-repo, blueprint-check-placeholders, and infra-bootstrap when present.\n",
        "# Explicit shell environment variables override values from this file.\n",
        "# Keep this file non-sensitive; use blueprint/repo.init.secrets.env for tokens/passwords.\n",
        "\n",
        "# Repository identity\n",
    ]
    lines.extend(shell_assignment(name, value) for name, value in identity_specs)
    lines.extend(
        [
            "\n",
            "# Operating defaults\n",
            shell_assignment("BLUEPRINT_PROFILE", os.environ.get("BLUEPRINT_PROFILE", "local-full")),
            "\n",
            "# Optional modules\n",
        ]
    )
    lines.extend(shell_assignment(name, value) for name, value in module_flag_specs)
    if module_required_specs:
        lines.extend(["\n", "# Required non-sensitive module inputs for currently enabled optional modules\n"])
        lines.extend(shell_assignment(name, value) for name, value in module_required_specs)
    return "".join(lines)


def core_sensitive_env_specs() -> list[tuple[str, str]]:
    return [
        ("STACKIT_SERVICE_ACCOUNT_KEY", os.environ.get("STACKIT_SERVICE_ACCOUNT_KEY", "")),
        ("STACKIT_SERVICE_ACCOUNT_TOKEN", os.environ.get("STACKIT_SERVICE_ACCOUNT_TOKEN", "")),
        ("STACKIT_TFSTATE_ACCESS_KEY_ID", os.environ.get("STACKIT_TFSTATE_ACCESS_KEY_ID", "")),
        ("STACKIT_TFSTATE_SECRET_ACCESS_KEY", os.environ.get("STACKIT_TFSTATE_SECRET_ACCESS_KEY", "")),
    ]


def non_sensitive_module_required_env_specs(
    repo_root: Path,
    module_enablement: dict[str, bool],
) -> list[tuple[str, str]]:
    return [
        (name, value)
        for name, value in enabled_module_required_env_specs(repo_root, module_enablement)
        if not _is_sensitive_module_required_env(name)
    ]


def sensitive_module_required_env_specs(
    repo_root: Path,
    module_enablement: dict[str, bool],
) -> list[tuple[str, str]]:
    return [
        (name, value)
        for name, value in enabled_module_required_env_specs(repo_root, module_enablement)
        if _is_sensitive_module_required_env(name)
    ]


def sensitive_env_specs(
    repo_root: Path,
    module_enablement: dict[str, bool],
) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, value in [*core_sensitive_env_specs(), *sensitive_module_required_env_specs(repo_root, module_enablement)]:
        if name in seen:
            continue
        seen.add(name)
        specs.append((name, value))
    return specs


def render_secrets_example_env_file_content(
    sensitive_specs: list[tuple[str, str]],
) -> str:
    lines = [
        "# Copy to blueprint/repo.init.secrets.env for local execution.\n",
        "# Keep this file non-sensitive and placeholder-only.\n",
        "# blueprint-check-placeholders and infra targets load blueprint/repo.init.secrets.env when present.\n",
        "\n",
        "# Core STACKIT credentials (required for live STACKIT execution)\n",
        "STACKIT_SERVICE_ACCOUNT_KEY=\n",
        "STACKIT_SERVICE_ACCOUNT_TOKEN=\n",
        "STACKIT_TFSTATE_ACCESS_KEY_ID=\n",
        "STACKIT_TFSTATE_SECRET_ACCESS_KEY=\n",
    ]
    # Tracked example files must stay placeholder-only even when the caller has
    # live secrets exported in the shell.
    module_specs = [
        (name, MODULE_REQUIRED_ENV_DEFAULTS.get(name, ""))
        for name, _ in sensitive_specs
        if name not in CORE_SENSITIVE_ENV_NAMES
    ]
    if module_specs:
        lines.extend(["\n", "# Module inputs for currently enabled optional modules\n"])
        lines.extend(shell_assignment(name, value) for name, value in module_specs)
    return "".join(lines)


def render_local_secrets_env_file_content(
    sensitive_specs: list[tuple[str, str]],
) -> str:
    lines = [
        "# Local sensitive defaults for this generated consumer.\n",
        "# This file is gitignored and loaded after blueprint/repo.init.env.\n",
        "# Explicit shell environment variables still take precedence.\n",
        "\n",
        "# Core STACKIT credentials (required for live STACKIT execution)\n",
    ]
    lines.extend(shell_assignment(name, value) for name, value in core_sensitive_env_specs())
    module_specs = [(name, value) for name, value in sensitive_specs if name not in CORE_SENSITIVE_ENV_NAMES]
    if module_specs:
        lines.extend(["\n", "# Module inputs for currently enabled optional modules\n"])
        lines.extend(shell_assignment(name, value) for name, value in module_specs)
    return "".join(lines)


def _replace_env_assignment(content: str, name: str, value: str) -> tuple[str, bool]:
    assignment = shell_assignment(name, value).rstrip("\n")
    pattern = re.compile(rf"^(?:export\s+)?{re.escape(name)}=.*$", flags=re.MULTILINE)
    updated, count = pattern.subn(assignment, content, count=1)
    return updated, count == 1


def _declared_env_names(content: str) -> set[str]:
    return set(re.findall(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=.*$", content, flags=re.MULTILINE))


def ensure_defaults_env_file(
    repo_root: Path,
    args: argparse.Namespace,
    dry_run: bool,
    summary: ChangeSummary,
    module_enablement: dict[str, bool],
) -> None:
    contract = load_blueprint_contract_for_init(repo_root)
    defaults_env_path = repo_root / contract.repository.template_bootstrap.defaults_env_file
    identity_specs = defaults_env_identity_specs(args)
    module_flag_specs = defaults_env_module_flag_specs(repo_root, module_enablement)
    module_required_specs = non_sensitive_module_required_env_specs(repo_root, module_enablement)
    profile_spec = ("BLUEPRINT_PROFILE", os.environ.get("BLUEPRINT_PROFILE", "local-full"))

    if not defaults_env_path.exists():
        updated = render_defaults_env_file_content(identity_specs, module_flag_specs, module_required_specs)
        apply_file_update(defaults_env_path, None, updated, dry_run, summary)
        return

    original = defaults_env_path.read_text(encoding="utf-8")
    updated = original
    for name, value in [*identity_specs, profile_spec, *module_flag_specs]:
        updated, _ = _replace_env_assignment(updated, name, value)

    declared_names = _declared_env_names(updated)
    missing_specs = [
        (name, value)
        for name, value in [
            *identity_specs,
            profile_spec,
            *module_flag_specs,
            *module_required_specs,
        ]
        if name not in declared_names
    ]
    if missing_specs:
        if updated and not updated.endswith("\n"):
            updated += "\n"
        updated += "\n# Added by blueprint-init-repo to keep repository defaults complete.\n"
        updated += "".join(shell_assignment(name, value) for name, value in missing_specs)

    apply_file_update(defaults_env_path, original, updated, dry_run, summary)


def ensure_secrets_example_env_file(
    repo_root: Path,
    dry_run: bool,
    summary: ChangeSummary,
    module_enablement: dict[str, bool],
) -> None:
    contract = load_blueprint_contract_for_init(repo_root)
    secrets_example_path = repo_root / contract.repository.template_bootstrap.secrets_example_env_file
    sensitive_specs = sensitive_env_specs(repo_root, module_enablement)
    original = secrets_example_path.read_text(encoding="utf-8") if secrets_example_path.exists() else None
    updated = render_secrets_example_env_file_content(sensitive_specs)
    apply_file_update(secrets_example_path, original, updated, dry_run, summary)


def ensure_local_secrets_env_file(
    repo_root: Path,
    dry_run: bool,
    summary: ChangeSummary,
    module_enablement: dict[str, bool],
) -> None:
    contract = load_blueprint_contract_for_init(repo_root)
    secrets_env_path = repo_root / contract.repository.template_bootstrap.secrets_env_file
    sensitive_specs = sensitive_env_specs(repo_root, module_enablement)

    if not secrets_env_path.exists():
        updated = render_local_secrets_env_file_content(sensitive_specs)
        apply_file_update(secrets_env_path, None, updated, dry_run, summary)
        return

    original = secrets_env_path.read_text(encoding="utf-8")
    updated = original
    declared_names = _declared_env_names(updated)
    missing_specs = [(name, value) for name, value in sensitive_specs if name not in declared_names]
    if missing_specs:
        if updated and not updated.endswith("\n"):
            updated += "\n"
        updated += "\n# Added by blueprint-init-repo to keep sensitive local defaults complete.\n"
        updated += "".join(shell_assignment(name, value) for name, value in missing_specs)
    apply_file_update(secrets_env_path, original, updated, dry_run, summary)
