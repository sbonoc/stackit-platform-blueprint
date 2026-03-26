from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]


OPTIONAL_SCAFFOLD_DIRS = [
    "dags",
    "infra/cloud/stackit/terraform/modules/workflows",
    "infra/cloud/stackit/terraform/modules/langfuse",
    "infra/cloud/stackit/terraform/modules/postgres",
    "infra/cloud/stackit/terraform/modules/neo4j",
    "infra/local/helm/langfuse",
    "infra/local/helm/postgres",
    "infra/local/helm/neo4j",
    "tests/infra/modules/workflows",
    "tests/infra/modules/langfuse",
    "tests/infra/modules/postgres",
    "tests/infra/modules/neo4j",
]

OPTIONAL_SCAFFOLD_FILES = [
    "infra/gitops/argocd/optional/local/workflows.yaml",
    "infra/gitops/argocd/optional/dev/workflows.yaml",
    "infra/gitops/argocd/optional/stage/workflows.yaml",
    "infra/gitops/argocd/optional/prod/workflows.yaml",
    "infra/gitops/argocd/optional/local/langfuse.yaml",
    "infra/gitops/argocd/optional/dev/langfuse.yaml",
    "infra/gitops/argocd/optional/stage/langfuse.yaml",
    "infra/gitops/argocd/optional/prod/langfuse.yaml",
    "infra/gitops/argocd/optional/local/neo4j.yaml",
    "infra/gitops/argocd/optional/dev/neo4j.yaml",
    "infra/gitops/argocd/optional/stage/neo4j.yaml",
    "infra/gitops/argocd/optional/prod/neo4j.yaml",
]


def module_flags_env(
    *,
    profile: str = "local-full",
    observability: str = "false",
    workflows: str = "false",
    langfuse: str = "false",
    postgres: str = "false",
    neo4j: str = "false",
) -> dict[str, str]:
    return {
        "BLUEPRINT_PROFILE": profile,
        "OBSERVABILITY_ENABLED": observability,
        "WORKFLOWS_ENABLED": workflows,
        "LANGFUSE_ENABLED": langfuse,
        "POSTGRES_ENABLED": postgres,
        "NEO4J_ENABLED": neo4j,
    }


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


def prune_optional_scaffolding() -> None:
    for relative in OPTIONAL_SCAFFOLD_FILES:
        path = REPO_ROOT / relative
        if path.exists():
            path.unlink()

    for relative in OPTIONAL_SCAFFOLD_DIRS:
        path = REPO_ROOT / relative
        if path.exists():
            shutil.rmtree(path)
