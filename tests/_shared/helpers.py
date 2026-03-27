from __future__ import annotations

import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


def module_flags_env(
    *,
    profile: str = "local-full",
    observability: str = "false",
    workflows: str = "false",
    langfuse: str = "false",
    postgres: str = "false",
    neo4j: str = "false",
    object_storage: str = "false",
    rabbitmq: str = "false",
    dns: str = "false",
    public_endpoints: str = "false",
    secrets_manager: str = "false",
    kms: str = "false",
    identity_aware_proxy: str = "false",
) -> dict[str, str]:
    env = {
        "BLUEPRINT_PROFILE": profile,
        "OBSERVABILITY_ENABLED": observability,
        "WORKFLOWS_ENABLED": workflows,
        "LANGFUSE_ENABLED": langfuse,
        "POSTGRES_ENABLED": postgres,
        "NEO4J_ENABLED": neo4j,
        "OBJECT_STORAGE_ENABLED": object_storage,
        "RABBITMQ_ENABLED": rabbitmq,
        "DNS_ENABLED": dns,
        "PUBLIC_ENDPOINTS_ENABLED": public_endpoints,
        "SECRETS_MANAGER_ENABLED": secrets_manager,
        "KMS_ENABLED": kms,
        "IDENTITY_AWARE_PROXY_ENABLED": identity_aware_proxy,
    }

    # Tests that enable provider-backed Postgres need stable contract inputs so
    # `infra-bootstrap` can render the local/STACKIT scaffolding deterministically.
    if postgres == "true":
        env.setdefault("POSTGRES_INSTANCE_NAME", "blueprint-postgres")
        env.setdefault("POSTGRES_DB_NAME", "platform")
        env.setdefault("POSTGRES_USER", "platform")
        env.setdefault("POSTGRES_PASSWORD", "platform-password")

    return env


def run(
    cmd: list[str],
    env_overrides: dict[str, str] | None = None,
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def run_make(
    target: str,
    env_overrides: dict[str, str] | None = None,
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(["make", target], env_overrides, cwd=cwd)


def run_blueprint_and_infra_bootstrap(env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    blueprint_bootstrap = run_make("blueprint-bootstrap", env_overrides)
    if blueprint_bootstrap.returncode != 0:
        return blueprint_bootstrap
    return run_make("infra-bootstrap", env_overrides)


def run_render_and_infra_bootstrap(env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    render = run_make("blueprint-render-makefile", env_overrides)
    if render.returncode != 0:
        return render
    return run_make("infra-bootstrap", env_overrides)


def restore_default_generated_state() -> subprocess.CompletedProcess[str]:
    reset_env = module_flags_env()
    render = run_make("blueprint-render-makefile", reset_env)
    if render.returncode != 0:
        return render
    return run_make("apps-bootstrap", reset_env)
