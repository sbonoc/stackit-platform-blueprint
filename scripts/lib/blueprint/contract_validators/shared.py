from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class ContractValidationHelpers:
    """Reusable helper callables injected from validate_contract.py.

    The validator modules stay focused on contract-specific rules while reusing
    canonical parsing/path helper behavior from the main validator entrypoint.
    """

    validate_required_files: Callable[[Path, list[str]], list[str]]
    validate_required_paths: Callable[[Path, list[str]], list[str]]
    mapping_or_error: Callable[[object, str, list[str]], dict[str, object]]
    list_of_str_or_error: Callable[[object, str, list[str]], list[str]]
    string_or_error: Callable[[object, str, list[str]], str]
    bool_or_error: Callable[[object, str, list[str]], bool | None]
    int_or_error: Callable[[object, str, list[str]], int | None]
    is_optional_contract_enabled: Callable[[dict[str, object], dict[str, object]], bool]
    kustomization_resources: Callable[[Path], set[str]]
    manifest_kinds_under_path: Callable[[Path], set[str]]
    make_targets: Callable[[Path], set[str]]
    manifest_sync_policy_has_automated: Callable[[str], bool]
    validate_argocd_https_repo_url_contract: Callable[[Path], list[str]]
    load_runtime_identity_contract: Callable[[Path], Any]
    render_eso_external_secrets_manifest: Callable[[Any], str]
    runtime_dependency_edges: tuple[tuple[str, str], ...]
