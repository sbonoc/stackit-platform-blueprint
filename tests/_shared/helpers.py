from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_CACHE_DIR = REPO_ROOT / "artifacts" / "tests" / "fixture-cache"


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
