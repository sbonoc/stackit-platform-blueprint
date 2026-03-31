from __future__ import annotations


import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_module_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_MANAGED_RESTORE_TEMPLATE_PATHS = (
    "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml",
    "scripts/templates/blueprint/bootstrap/blueprint/runtime_identity_contract.yaml",
    "blueprint/runtime_identity_contract.yaml",
    "scripts/templates/blueprint/bootstrap/docs/docusaurus.config.js",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/root/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/dev/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/stage/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/prod/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/application-platform-local.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/stage.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/prod.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/dev.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/stage.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/prod.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/stage.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/prod.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/stage.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/prod.hcl",
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _copy_repo_text_path(tmp_root: Path, rel_path: str) -> None:
    target_path = tmp_root / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(_read(rel_path), encoding="utf-8")


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_yaml_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _extract_yaml_section(lines: list[str], marker: str) -> list[str]:
    marker_index = -1
    marker_indent = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"{marker}:":
            marker_index = idx
            marker_indent = _line_indent(line)
            break

    if marker_index == -1:
        return []

    section: list[str] = []
    for line in lines[marker_index + 1 :]:
        if not line.strip():
            continue
        if _line_indent(line) <= marker_indent:
            break
        section.append(line)
    return section


def _extract_yaml_scalar(lines: list[str], key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return _strip_yaml_scalar(match.group(1))
    return ""


def _extract_yaml_list(lines: list[str], marker: str) -> list[str]:
    section = _extract_yaml_section(lines, marker)
    values: list[str] = []
    for line in section:
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(_strip_yaml_scalar(stripped[2:]))
    return values


def _make_targets() -> set[str]:
    targets: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    makefiles = [REPO_ROOT / "Makefile"]
    make_root = REPO_ROOT / "make"
    if make_root.is_dir():
        makefiles.extend(sorted(path for path in make_root.rglob("*.mk") if path.is_file()))
    for makefile in makefiles:
        for line in makefile.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            target = match.group(1)
            if target == ".PHONY":
                continue
            targets.add(target)
    return targets




class RefactorContractBase(unittest.TestCase):
    def _contract_lines(self) -> list[str]:
        return _read("blueprint/contract.yaml").splitlines()


__all__ = [
    "INIT_MANAGED_RESTORE_TEMPLATE_PATHS",
    "REPO_ROOT",
    "RefactorContractBase",
    "_copy_repo_text_path",
    "_extract_yaml_list",
    "_extract_yaml_scalar",
    "_extract_yaml_section",
    "_line_indent",
    "_make_targets",
    "_read",
    "_strip_yaml_scalar",
    "load_module_contract",
    "os",
    "Path",
    "re",
    "subprocess",
    "sys",
    "tempfile",
]
