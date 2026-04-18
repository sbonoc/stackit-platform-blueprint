#!/usr/bin/env python3
"""Shared repo-mode resolution helpers for docs sync scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract


REPO_MODE_TEMPLATE_SOURCE: Final[str] = "template-source"
REPO_MODE_GENERATED_CONSUMER: Final[str] = "generated-consumer"
_SUPPORTED_REPO_MODES: Final[set[str]] = {
    REPO_MODE_TEMPLATE_SOURCE,
    REPO_MODE_GENERATED_CONSUMER,
}


@dataclass(frozen=True)
class DocsRepoContext:
    contract: BlueprintContract
    repo_mode: str

    @property
    def template_sync_enabled(self) -> bool:
        return self.repo_mode == REPO_MODE_TEMPLATE_SOURCE


def resolve_docs_repo_context(repo_root: Path) -> DocsRepoContext:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    repo_mode = contract.repository.repo_mode.strip()
    if not repo_mode:
        raise ValueError("spec.repository.repo_mode must be set in blueprint/contract.yaml")

    allowed_modes = set(contract.repository.allowed_repo_modes)
    if allowed_modes and repo_mode not in allowed_modes:
        allowed_display = ", ".join(sorted(allowed_modes))
        raise ValueError(
            "spec.repository.repo_mode must be one of "
            f"spec.repository.allowed_repo_modes [{allowed_display}]; got: {repo_mode}"
        )
    if repo_mode not in _SUPPORTED_REPO_MODES:
        raise ValueError(f"unsupported repository repo_mode for docs sync: {repo_mode}")

    return DocsRepoContext(contract=contract, repo_mode=repo_mode)


def resolve_docs_paths_for_context(
    *,
    context: DocsRepoContext,
    source_path: Path,
    template_path: Path,
) -> tuple[Path, ...]:
    if context.repo_mode == REPO_MODE_GENERATED_CONSUMER:
        return (source_path,)
    if context.repo_mode == REPO_MODE_TEMPLATE_SOURCE:
        return (source_path, template_path)
    raise ValueError(f"unsupported repository repo_mode for docs sync: {context.repo_mode}")
