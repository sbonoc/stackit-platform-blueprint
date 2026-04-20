from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from scripts.lib.blueprint.init_repo_contract import (
    load_blueprint_contract_for_init,
    normalize_bool,
)
from scripts.lib.blueprint.init_repo_env import enabled_module_required_env_specs
from tests._shared.exec import DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS, run_command


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CACHE_DIR = REPO_ROOT / "artifacts" / "tests" / "fixture-cache"


@lru_cache(maxsize=1)
def _optional_module_enable_flags() -> dict[str, str]:
    contract = load_blueprint_contract_for_init(REPO_ROOT)
    return {
        module.module_id: module.enable_flag
        for module in contract.optional_modules.modules.values()
    }


def _is_enabled(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return normalize_bool(str(value))


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
    opensearch: str = "false",
    dns: str = "false",
    public_endpoints: str = "false",
    secrets_manager: str = "false",
    kms: str = "false",
    identity_aware_proxy: str = "false",
    hydrate_module_required_env: str | bool = "true",
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
        "OPENSEARCH_ENABLED": opensearch,
        "DNS_ENABLED": dns,
        "PUBLIC_ENDPOINTS_ENABLED": public_endpoints,
        "SECRETS_MANAGER_ENABLED": secrets_manager,
        "KMS_ENABLED": kms,
        "IDENTITY_AWARE_PROXY_ENABLED": identity_aware_proxy,
    }

    if _is_enabled(hydrate_module_required_env):
        module_enablement = {
            module_id: _is_enabled(env.get(enable_flag, "false"))
            for module_id, enable_flag in _optional_module_enable_flags().items()
        }
        for env_name, env_value in enabled_module_required_env_specs(REPO_ROOT, module_enablement):
            if env_value:
                env.setdefault(env_name, env_value)

    return env


def run(
    cmd: list[str],
    env_overrides: dict[str, str] | None = None,
    *,
    cwd: Path | None = None,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        cmd,
        cwd=cwd or REPO_ROOT,
        env=env_overrides,
        timeout_seconds=timeout_seconds or DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS,
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


def _bootstrap_fixture_cache_key(env_overrides: dict[str, str], cache_namespace: str) -> str:
    contract_digest = hashlib.sha256((REPO_ROOT / "blueprint" / "contract.yaml").read_bytes()).hexdigest()[:16]
    runtime_identity_contract_path = REPO_ROOT / "blueprint" / "runtime_identity_contract.yaml"
    runtime_identity_digest = ""
    if runtime_identity_contract_path.is_file():
        runtime_identity_digest = hashlib.sha256(runtime_identity_contract_path.read_bytes()).hexdigest()[:16]
    payload = {
        "cache_namespace": cache_namespace,
        "contract_digest": contract_digest,
        "runtime_identity_digest": runtime_identity_digest,
        "env": {key: env_overrides[key] for key in sorted(env_overrides)},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def run_blueprint_and_infra_bootstrap_cached(
    env_overrides: dict[str, str],
    *,
    cache_namespace: str = "default",
) -> subprocess.CompletedProcess[str]:
    cache_key = _bootstrap_fixture_cache_key(env_overrides, cache_namespace)
    marker_path = FIXTURE_CACHE_DIR / f"{cache_key}.ok"
    if marker_path.exists():
        return subprocess.CompletedProcess(
            args=["cached-bootstrap"],
            returncode=0,
            stdout=f"bootstrap fixture cache hit: {marker_path}\n",
            stderr="",
        )

    bootstrap = run_blueprint_and_infra_bootstrap(env_overrides)
    if bootstrap.returncode == 0:
        FIXTURE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("ok\n", encoding="utf-8")
    return bootstrap


def restore_default_generated_state() -> subprocess.CompletedProcess[str]:
    if FIXTURE_CACHE_DIR.exists():
        shutil.rmtree(FIXTURE_CACHE_DIR)
    reset_env = module_flags_env()
    render = run_make("blueprint-render-makefile", reset_env)
    if render.returncode != 0:
        return render
    return run_make("apps-bootstrap", reset_env)
