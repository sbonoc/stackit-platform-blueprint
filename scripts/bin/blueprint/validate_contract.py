#!/usr/bin/env python3
"""Validate repository conformance against blueprint/contract.yaml."""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import (  # noqa: E402
    BlueprintContract,
    load_blueprint_contract,
)
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402
from scripts.lib.infra.runtime_identity_contract import (  # noqa: E402
    load_runtime_identity_contract,
    render_eso_external_secrets_manifest,
)


def _resolve_repo_root() -> Path:
    return REPO_ROOT


def _normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _makefile_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    root_makefile = repo_root / "Makefile"
    if root_makefile.is_file():
        paths.append(root_makefile)

    make_dir = repo_root / "make"
    if make_dir.is_dir():
        paths.extend(sorted(path for path in make_dir.rglob("*.mk") if path.is_file()))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def _make_targets(repo_root: Path) -> set[str]:
    makefiles = _makefile_paths(repo_root)
    if not makefiles:
        return set()
    targets: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
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


def _validate_required_files(repo_root: Path, required_files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in required_files:
        if not (repo_root / relative_path).is_file():
            errors.append(f"missing file: {relative_path}")
    return errors


def _validate_absent_files(repo_root: Path, relative_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in relative_paths:
        if (repo_root / relative_path).exists():
            errors.append(f"file must be absent for current repo_mode: {relative_path}")
    return errors


def _validate_required_paths(repo_root: Path, required_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in required_paths:
        if not (repo_root / relative_path).exists():
            errors.append(f"missing path: {relative_path}")
    return errors


def _path_is_same_or_child(path: str, parent: str) -> bool:
    path_parts = PurePosixPath(path).parts
    parent_parts = PurePosixPath(parent).parts
    if not parent_parts:
        return False
    if len(path_parts) < len(parent_parts):
        return False
    return path_parts[: len(parent_parts)] == parent_parts


def _mapping_or_error(value: object, path: str, errors: list[str]) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): val for key, val in value.items()}
    errors.append(f"{path} must be a mapping")
    return {}


def _list_of_str_or_error(value: object, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    values: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{path}[{idx}] must be a string")
            continue
        values.append(item)
    return values


def _string_or_error(value: object, path: str, errors: list[str]) -> str:
    if isinstance(value, str):
        return value
    errors.append(f"{path} must be a string")
    return ""


def _bool_or_error(value: object, path: str, errors: list[str]) -> bool | None:
    if isinstance(value, bool):
        return value
    errors.append(f"{path} must be a boolean")
    return None


def _int_or_error(value: object, path: str, errors: list[str]) -> int | None:
    if isinstance(value, bool):
        errors.append(f"{path} must be an integer")
        return None
    if isinstance(value, int):
        return value
    errors.append(f"{path} must be an integer")
    return None


def _is_optional_contract_enabled(spec_raw: dict[str, object], contract_section: dict[str, object]) -> bool:
    enabled_by_default = bool(contract_section.get("enabled_by_default", False))
    enable_flag_raw = contract_section.get("enable_flag")
    enable_flag = enable_flag_raw if isinstance(enable_flag_raw, str) else ""
    if not enable_flag:
        return enabled_by_default
    env_value = os.environ.get(enable_flag)
    if env_value is None:
        return enabled_by_default
    return _normalize_bool(env_value)


def _kustomization_resources(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    resources: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip().strip('"').strip("'")
        if value:
            resources.add(value)
    return resources


def _validate_runtime_credentials_contract(repo_root: Path) -> list[str]:
    errors: list[str] = []

    required_security_files = (
        "blueprint/runtime_identity_contract.yaml",
        "docs/platform/consumer/runtime_credentials_eso.md",
        "infra/gitops/platform/base/extensions/kustomization.yaml",
        "infra/gitops/platform/base/security/kustomization.yaml",
        "infra/gitops/platform/base/security/runtime-source-store.yaml",
        "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
        "infra/gitops/argocd/core/local/keycloak.yaml",
        "infra/gitops/argocd/core/dev/keycloak.yaml",
        "infra/gitops/argocd/core/stage/keycloak.yaml",
        "infra/gitops/argocd/core/prod/keycloak.yaml",
        "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
        "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl",
        "scripts/templates/blueprint/bootstrap/blueprint/runtime_identity_contract.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
    )
    errors.extend(_validate_required_files(repo_root, list(required_security_files)))

    runtime_identity_contract_path = repo_root / "blueprint/runtime_identity_contract.yaml"
    if runtime_identity_contract_path.is_file():
        try:
            runtime_identity_contract = load_runtime_identity_contract(runtime_identity_contract_path)
            rendered_eso_manifest = render_eso_external_secrets_manifest(runtime_identity_contract)
        except Exception as exc:  # pragma: no cover - defensive guard for contract parsing
            errors.append(f"invalid runtime identity contract: {exc}")
            rendered_eso_manifest = ""

        if rendered_eso_manifest:
            for relative_path in (
                "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
                "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
            ):
                manifest_path = repo_root / relative_path
                if not manifest_path.is_file():
                    continue
                if manifest_path.read_text(encoding="utf-8") != rendered_eso_manifest:
                    errors.append(
                        f"{relative_path} is out of sync with blueprint/runtime_identity_contract.yaml; "
                        "run runtime_identity_contract.py render-eso-manifest"
                    )

    base_kustomization = repo_root / "infra/gitops/platform/base/kustomization.yaml"
    base_resources = _kustomization_resources(base_kustomization)
    required_base_resources = {"security", "extensions"}
    missing_base_resources = sorted(required_base_resources - base_resources)
    if missing_base_resources:
        errors.append(
            "infra/gitops/platform/base/kustomization.yaml missing required runtime credentials resources: "
            + ", ".join(missing_base_resources)
        )

    security_kustomization = repo_root / "infra/gitops/platform/base/security/kustomization.yaml"
    security_resources = _kustomization_resources(security_kustomization)
    required_security_resources = {"runtime-source-store.yaml", "runtime-external-secrets-core.yaml"}
    missing_security_resources = sorted(required_security_resources - security_resources)
    if missing_security_resources:
        errors.append(
            "infra/gitops/platform/base/security/kustomization.yaml missing required resources: "
            + ", ".join(missing_security_resources)
        )

    extensions_kustomization = repo_root / "infra/gitops/platform/base/extensions/kustomization.yaml"
    if extensions_kustomization.is_file():
        extensions_content = extensions_kustomization.read_text(encoding="utf-8")
        if "resources:" not in extensions_content:
            errors.append(
                "infra/gitops/platform/base/extensions/kustomization.yaml must define resources for drift-safe extensions"
            )

    required_keycloak_resources = {
        "local": "../../core/local/keycloak.yaml",
        "dev": "../../core/dev/keycloak.yaml",
        "stage": "../../core/stage/keycloak.yaml",
        "prod": "../../core/prod/keycloak.yaml",
    }
    for env_name, resource_path in required_keycloak_resources.items():
        overlay_path = repo_root / f"infra/gitops/argocd/overlays/{env_name}/kustomization.yaml"
        overlay_resources = _kustomization_resources(overlay_path)
        if resource_path not in overlay_resources:
            errors.append(
                f"infra/gitops/argocd/overlays/{env_name}/kustomization.yaml missing mandatory keycloak resource: "
                f"{resource_path}"
            )

    for consumer_path, dependency_path in RUNTIME_DEPENDENCY_EDGES:
        consumer_file = repo_root / consumer_path
        if not consumer_file.is_file():
            continue
        consumer_content = consumer_file.read_text(encoding="utf-8", errors="surrogateescape")
        if dependency_path not in consumer_content:
            continue
        if not (repo_root / dependency_path).is_file():
            errors.append(
                f"{consumer_path} references {dependency_path} but dependency file is missing; "
                "reconcile runtime identity artifacts before infra-smoke/upgrade validation"
            )

    return errors


def _validate_event_messaging_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    spec_raw = _mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("event_messaging_contract")
    if raw_contract_section is None:
        errors.append("spec.event_messaging_contract is required")
        return errors
    contract_section = _mapping_or_error(
        raw_contract_section,
        "spec.event_messaging_contract",
        errors,
    )

    enabled_by_default = _bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.event_messaging_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default:
        errors.append("spec.event_messaging_contract.enabled_by_default must be false")

    enable_flag = _string_or_error(
        contract_section.get("enable_flag"),
        "spec.event_messaging_contract.enable_flag",
        errors,
    )
    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict) and enable_flag and enable_flag not in toggles_raw:
        errors.append(
            "spec.event_messaging_contract.enable_flag must reference an existing toggle: "
            f"{enable_flag}"
        )

    envelope = _mapping_or_error(contract_section.get("envelope"), "spec.event_messaging_contract.envelope", errors)
    required_fields = _list_of_str_or_error(
        envelope.get("required_fields"),
        "spec.event_messaging_contract.envelope.required_fields",
        errors,
    )
    expected_required_fields = {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "producer_service",
        "correlation_id",
        "causation_id",
        "traceparent",
        "tenant_id",
        "organization_id",
        "payload",
    }
    missing_required_fields = sorted(expected_required_fields - set(required_fields))
    if missing_required_fields:
        errors.append(
            "spec.event_messaging_contract.envelope.required_fields missing canonical fields: "
            + ", ".join(missing_required_fields)
        )
    optional_fields = _list_of_str_or_error(
        envelope.get("optional_fields"),
        "spec.event_messaging_contract.envelope.optional_fields",
        errors,
    )
    if "metadata" not in optional_fields:
        errors.append(
            "spec.event_messaging_contract.envelope.optional_fields must include metadata"
        )

    versioning = _mapping_or_error(
        contract_section.get("versioning_policy"),
        "spec.event_messaging_contract.versioning_policy",
        errors,
    )
    _bool_or_error(
        versioning.get("additive_evolution_default"),
        "spec.event_messaging_contract.versioning_policy.additive_evolution_default",
        errors,
    )
    deprecation_window = _int_or_error(
        versioning.get("deprecation_window_releases"),
        "spec.event_messaging_contract.versioning_policy.deprecation_window_releases",
        errors,
    )
    if deprecation_window is not None and deprecation_window < 1:
        errors.append(
            "spec.event_messaging_contract.versioning_policy.deprecation_window_releases must be >= 1"
        )
    overlap_window = _int_or_error(
        versioning.get("overlap_window_releases"),
        "spec.event_messaging_contract.versioning_policy.overlap_window_releases",
        errors,
    )
    if overlap_window is not None and overlap_window < 1:
        errors.append(
            "spec.event_messaging_contract.versioning_policy.overlap_window_releases must be >= 1"
        )
    _bool_or_error(
        versioning.get("dual_publish_required_for_breaking"),
        "spec.event_messaging_contract.versioning_policy.dual_publish_required_for_breaking",
        errors,
    )
    _bool_or_error(
        versioning.get("dual_read_required_for_breaking"),
        "spec.event_messaging_contract.versioning_policy.dual_read_required_for_breaking",
        errors,
    )

    reliability = _mapping_or_error(
        contract_section.get("reliability"),
        "spec.event_messaging_contract.reliability",
        errors,
    )
    outbox = _mapping_or_error(
        reliability.get("outbox"),
        "spec.event_messaging_contract.reliability.outbox",
        errors,
    )
    _bool_or_error(
        outbox.get("contract_required"),
        "spec.event_messaging_contract.reliability.outbox.contract_required",
        errors,
    )
    inbox = _mapping_or_error(
        reliability.get("inbox"),
        "spec.event_messaging_contract.reliability.inbox",
        errors,
    )
    _bool_or_error(
        inbox.get("contract_required"),
        "spec.event_messaging_contract.reliability.inbox.contract_required",
        errors,
    )
    idempotency = _mapping_or_error(
        reliability.get("idempotency"),
        "spec.event_messaging_contract.reliability.idempotency",
        errors,
    )
    _bool_or_error(
        idempotency.get("contract_required"),
        "spec.event_messaging_contract.reliability.idempotency.contract_required",
        errors,
    )
    idempotency_key_fields = _list_of_str_or_error(
        idempotency.get("key_fields"),
        "spec.event_messaging_contract.reliability.idempotency.key_fields",
        errors,
    )
    for required_key in ("event_id", "consumer_name"):
        if required_key not in idempotency_key_fields:
            errors.append(
                "spec.event_messaging_contract.reliability.idempotency.key_fields must include "
                f"{required_key}"
            )
    retry = _mapping_or_error(
        reliability.get("retry"),
        "spec.event_messaging_contract.reliability.retry",
        errors,
    )
    retry_strategy = _string_or_error(
        retry.get("strategy"),
        "spec.event_messaging_contract.reliability.retry.strategy",
        errors,
    )
    if retry_strategy != "exponential-backoff-with-jitter":
        errors.append(
            "spec.event_messaging_contract.reliability.retry.strategy must be exponential-backoff-with-jitter"
        )
    dead_letter_queue = _mapping_or_error(
        reliability.get("dead_letter_queue"),
        "spec.event_messaging_contract.reliability.dead_letter_queue",
        errors,
    )
    _string_or_error(
        dead_letter_queue.get("naming_pattern"),
        "spec.event_messaging_contract.reliability.dead_letter_queue.naming_pattern",
        errors,
    )
    _bool_or_error(
        dead_letter_queue.get("replay_contract_required"),
        "spec.event_messaging_contract.reliability.dead_letter_queue.replay_contract_required",
        errors,
    )

    scaffolding_hooks = _mapping_or_error(
        contract_section.get("scaffolding_hooks"),
        "spec.event_messaging_contract.scaffolding_hooks",
        errors,
    )
    for path_key in (
        "producer_contract_dir",
        "consumer_contract_dir",
        "outbox_template_path",
        "inbox_template_path",
        "idempotency_template_path",
    ):
        path_value = _string_or_error(
            scaffolding_hooks.get(path_key),
            f"spec.event_messaging_contract.scaffolding_hooks.{path_key}",
            errors,
        )
        if not path_value:
            continue
        if not (repo_root / path_value).exists():
            errors.append(
                f"missing event messaging scaffolding hook path: {path_value}"
            )

    docs_path = repo_root / "docs/platform/consumer/event_messaging_baseline.md"
    if docs_path.is_file():
        docs_content = docs_path.read_text(encoding="utf-8")
        if "Python / FastAPI" not in docs_content:
            errors.append("docs/platform/consumer/event_messaging_baseline.md must include Python / FastAPI guidance")
        if "JS/TS runtime" not in docs_content:
            errors.append("docs/platform/consumer/event_messaging_baseline.md must include JS/TS runtime guidance")

    return errors


def _validate_zero_downtime_evolution_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    spec_raw = _mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("zero_downtime_evolution_contract")
    if raw_contract_section is None:
        errors.append("spec.zero_downtime_evolution_contract is required")
        return errors
    contract_section = _mapping_or_error(
        raw_contract_section,
        "spec.zero_downtime_evolution_contract",
        errors,
    )

    enabled_by_default = _bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.zero_downtime_evolution_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default:
        errors.append("spec.zero_downtime_evolution_contract.enabled_by_default must be false")

    enable_flag = _string_or_error(
        contract_section.get("enable_flag"),
        "spec.zero_downtime_evolution_contract.enable_flag",
        errors,
    )
    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict) and enable_flag and enable_flag not in toggles_raw:
        errors.append(
            "spec.zero_downtime_evolution_contract.enable_flag must reference an existing toggle: "
            f"{enable_flag}"
        )

    lifecycle = _mapping_or_error(
        contract_section.get("lifecycle"),
        "spec.zero_downtime_evolution_contract.lifecycle",
        errors,
    )
    phases = _list_of_str_or_error(
        lifecycle.get("phases"),
        "spec.zero_downtime_evolution_contract.lifecycle.phases",
        errors,
    )
    if phases != ["expand", "migrate", "contract"]:
        errors.append(
            "spec.zero_downtime_evolution_contract.lifecycle.phases must be [expand, migrate, contract]"
        )
    _bool_or_error(
        lifecycle.get("destructive_changes_only_in_contract_phase"),
        "spec.zero_downtime_evolution_contract.lifecycle.destructive_changes_only_in_contract_phase",
        errors,
    )
    minimum_release_windows = _int_or_error(
        lifecycle.get("minimum_stable_release_windows"),
        "spec.zero_downtime_evolution_contract.lifecycle.minimum_stable_release_windows",
        errors,
    )
    if minimum_release_windows is not None and minimum_release_windows < 1:
        errors.append(
            "spec.zero_downtime_evolution_contract.lifecycle.minimum_stable_release_windows must be >= 1"
        )

    for section_name, keys in (
        (
            "database_policy",
            (
                "backward_compatible_expand_first",
                "rollback_checkpoint_required",
                "destructive_migrations_require_feature_flag",
            ),
        ),
        (
            "api_policy",
            (
                "additive_changes_default",
                "mixed_version_compatibility_required",
            ),
        ),
        (
            "event_policy",
            (
                "additive_evolution_default",
                "dual_read_required_for_breaking",
            ),
        ),
    ):
        section_mapping = _mapping_or_error(
            contract_section.get(section_name),
            f"spec.zero_downtime_evolution_contract.{section_name}",
            errors,
        )
        for key in keys:
            _bool_or_error(
                section_mapping.get(key),
                f"spec.zero_downtime_evolution_contract.{section_name}.{key}",
                errors,
            )

    api_policy = _mapping_or_error(
        contract_section.get("api_policy"),
        "spec.zero_downtime_evolution_contract.api_policy",
        errors,
    )
    api_window = _int_or_error(
        api_policy.get("removal_deprecation_window_releases"),
        "spec.zero_downtime_evolution_contract.api_policy.removal_deprecation_window_releases",
        errors,
    )
    if api_window is not None and api_window < 1:
        errors.append(
            "spec.zero_downtime_evolution_contract.api_policy.removal_deprecation_window_releases must be >= 1"
        )

    event_policy = _mapping_or_error(
        contract_section.get("event_policy"),
        "spec.zero_downtime_evolution_contract.event_policy",
        errors,
    )
    overlap_releases = _int_or_error(
        event_policy.get("producer_consumer_overlap_releases"),
        "spec.zero_downtime_evolution_contract.event_policy.producer_consumer_overlap_releases",
        errors,
    )
    if overlap_releases is not None and overlap_releases < 1:
        errors.append(
            "spec.zero_downtime_evolution_contract.event_policy.producer_consumer_overlap_releases must be >= 1"
        )

    quality_checks = _mapping_or_error(
        contract_section.get("quality_checks"),
        "spec.zero_downtime_evolution_contract.quality_checks",
        errors,
    )
    for check_name in (
        "reject_drop_column_without_contract_marker",
        "reject_drop_table_without_contract_marker",
        "reject_event_version_overwrite_without_new_version",
    ):
        _bool_or_error(
            quality_checks.get(check_name),
            f"spec.zero_downtime_evolution_contract.quality_checks.{check_name}",
            errors,
        )

    docs_path = repo_root / "docs/platform/consumer/zero_downtime_evolution.md"
    if docs_path.is_file():
        docs_content = docs_path.read_text(encoding="utf-8")
        for phase in ("expand", "migrate", "contract"):
            if f"`{phase}`" not in docs_content:
                errors.append(
                    "docs/platform/consumer/zero_downtime_evolution.md must describe lifecycle phase: "
                    f"{phase}"
                )

    if _is_optional_contract_enabled(spec_raw, contract_section):
        for sql_path in sorted(repo_root.rglob("*.sql")):
            relative = sql_path.relative_to(repo_root).as_posix()
            if not any(marker in relative for marker in ("migration", "migrations/")):
                continue
            content_upper = sql_path.read_text(encoding="utf-8", errors="surrogateescape").upper()
            destructive = "DROP COLUMN" in content_upper or "DROP TABLE" in content_upper
            if not destructive:
                continue
            if "ZERO_DOWNTIME_CONTRACT_PHASE=CONTRACT" in content_upper:
                continue
            errors.append(
                f"{relative} contains destructive SQL without ZERO_DOWNTIME_CONTRACT_PHASE=contract marker"
            )

    return errors


def _validate_tenant_context_contract(contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    spec_raw = _mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("tenant_context_contract")
    if raw_contract_section is None:
        errors.append("spec.tenant_context_contract is required")
        return errors
    contract_section = _mapping_or_error(
        raw_contract_section,
        "spec.tenant_context_contract",
        errors,
    )

    enabled_by_default = _bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.tenant_context_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default:
        errors.append("spec.tenant_context_contract.enabled_by_default must be false")

    enable_flag = _string_or_error(
        contract_section.get("enable_flag"),
        "spec.tenant_context_contract.enable_flag",
        errors,
    )
    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict) and enable_flag and enable_flag not in toggles_raw:
        errors.append(
            "spec.tenant_context_contract.enable_flag must reference an existing toggle: "
            f"{enable_flag}"
        )

    _bool_or_error(
        contract_section.get("required_for_user_initiated_flows"),
        "spec.tenant_context_contract.required_for_user_initiated_flows",
        errors,
    )

    identity = _mapping_or_error(
        contract_section.get("identity"),
        "spec.tenant_context_contract.identity",
        errors,
    )
    required_claims = _list_of_str_or_error(
        identity.get("required_claims"),
        "spec.tenant_context_contract.identity.required_claims",
        errors,
    )
    for required_claim in ("tenant_id", "organization_id", "user_id"):
        if required_claim not in required_claims:
            errors.append(
                "spec.tenant_context_contract.identity.required_claims must include "
                f"{required_claim}"
            )
    _list_of_str_or_error(
        identity.get("optional_claims"),
        "spec.tenant_context_contract.identity.optional_claims",
        errors,
    )

    http_api = _mapping_or_error(
        contract_section.get("http_api"),
        "spec.tenant_context_contract.http_api",
        errors,
    )
    required_headers = _mapping_or_error(
        http_api.get("required_headers"),
        "spec.tenant_context_contract.http_api.required_headers",
        errors,
    )
    for header_key in ("tenant_id", "organization_id", "correlation_id"):
        header_value = required_headers.get(header_key)
        if not isinstance(header_value, str) or not header_value.strip():
            errors.append(
                "spec.tenant_context_contract.http_api.required_headers must define "
                f"a non-empty value for {header_key}"
            )
    missing_context_status = _int_or_error(
        http_api.get("missing_context_http_status"),
        "spec.tenant_context_contract.http_api.missing_context_http_status",
        errors,
    )
    if missing_context_status is not None and missing_context_status < 400:
        errors.append(
            "spec.tenant_context_contract.http_api.missing_context_http_status must be a client/server error status"
        )

    async_events = _mapping_or_error(
        contract_section.get("async_events"),
        "spec.tenant_context_contract.async_events",
        errors,
    )
    required_event_fields = _list_of_str_or_error(
        async_events.get("required_fields"),
        "spec.tenant_context_contract.async_events.required_fields",
        errors,
    )
    for event_field in ("tenant_id", "organization_id", "correlation_id", "causation_id"):
        if event_field not in required_event_fields:
            errors.append(
                "spec.tenant_context_contract.async_events.required_fields must include "
                f"{event_field}"
            )
    _bool_or_error(
        async_events.get("allow_empty_tenant_for_system_events"),
        "spec.tenant_context_contract.async_events.allow_empty_tenant_for_system_events",
        errors,
    )

    observability = _mapping_or_error(
        contract_section.get("observability"),
        "spec.tenant_context_contract.observability",
        errors,
    )
    log_fields = _list_of_str_or_error(
        observability.get("log_fields"),
        "spec.tenant_context_contract.observability.log_fields",
        errors,
    )
    for field in ("tenant_id", "organization_id", "correlation_id"):
        if field not in log_fields:
            errors.append(
                "spec.tenant_context_contract.observability.log_fields must include "
                f"{field}"
            )
    _list_of_str_or_error(
        observability.get("trace_attributes"),
        "spec.tenant_context_contract.observability.trace_attributes",
        errors,
    )
    _list_of_str_or_error(
        observability.get("audit_fields"),
        "spec.tenant_context_contract.observability.audit_fields",
        errors,
    )

    event_messaging_section = spec_raw.get("event_messaging_contract")
    if isinstance(event_messaging_section, dict):
        envelope = event_messaging_section.get("envelope")
        if isinstance(envelope, dict):
            event_required_fields_raw = envelope.get("required_fields")
            if isinstance(event_required_fields_raw, list):
                event_required_fields = {
                    str(field) for field in event_required_fields_raw if isinstance(field, str)
                }
                for field in ("tenant_id", "organization_id", "correlation_id", "causation_id"):
                    if field not in event_required_fields:
                        errors.append(
                            "spec.event_messaging_contract.envelope.required_fields must include "
                            f"{field} to match tenant context propagation contract"
                        )

    return errors


def _validate_template_bootstrap_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    template = contract.repository.template_bootstrap

    if template.model != "github-template":
        errors.append("repository.template_bootstrap.model must be github-template")

    template_version = template.template_version
    if not template_version:
        errors.append("repository.template_bootstrap.template_version is required")
    template_version_tuple = _parse_semver(template_version)
    if template_version and not template_version_tuple:
        errors.append("repository.template_bootstrap.template_version must be semver (MAJOR.MINOR.PATCH)")

    init_command = template.init_command
    if not init_command:
        errors.append("repository.template_bootstrap.init_command is required")

    targets = _make_targets(repo_root)
    for command_key, command_value in (("init_command", init_command),):
        if not command_value:
            continue
        if not command_value.startswith("make "):
            errors.append(f"repository.template_bootstrap.{command_key} must be a make target command")
            continue
        make_target = command_value.split(maxsplit=1)[1].strip()
        if not make_target:
            errors.append(f"repository.template_bootstrap.{command_key} must include a make target")
            continue
        if make_target not in targets:
            errors.append(
                f"repository.template_bootstrap.{command_key} references missing make target: {make_target}"
            )

    required_inputs = template.required_inputs
    if not required_inputs:
        errors.append("repository.template_bootstrap.required_inputs must define at least one variable")
    else:
        for variable in required_inputs:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable):
                errors.append(
                    f"repository.template_bootstrap.required_inputs contains invalid variable name: {variable}"
                )

    defaults_env_file = template.defaults_env_file
    if not defaults_env_file:
        errors.append("repository.template_bootstrap.defaults_env_file is required")
        return errors

    defaults_path = repo_root / defaults_env_file
    if not defaults_path.is_file():
        errors.append(f"missing template bootstrap defaults env file: {defaults_env_file}")
        return errors

    defaults_content = defaults_path.read_text(encoding="utf-8")
    for variable in required_inputs:
        if f"{variable}=" not in defaults_content:
            errors.append(
                "template bootstrap defaults env missing required input variable declaration: " f"{variable}"
            )

    secrets_example_env_file = template.secrets_example_env_file
    if not secrets_example_env_file:
        errors.append("repository.template_bootstrap.secrets_example_env_file is required")
    else:
        secrets_example_path = repo_root / secrets_example_env_file
        if not secrets_example_path.is_file():
            errors.append(
                "missing template bootstrap secrets example env file: "
                f"{secrets_example_env_file}"
            )

    secrets_env_file = template.secrets_env_file
    if not secrets_env_file:
        errors.append("repository.template_bootstrap.secrets_env_file is required")
    elif secrets_env_file in {defaults_env_file, secrets_example_env_file}:
        errors.append(
            "repository.template_bootstrap.secrets_env_file must differ from "
            "defaults_env_file and secrets_example_env_file"
        )

    force_env_var = template.force_env_var
    if not force_env_var:
        errors.append("repository.template_bootstrap.force_env_var is required")
    elif not re.fullmatch(r"[A-Z][A-Z0-9_]*", force_env_var):
        errors.append("repository.template_bootstrap.force_env_var must be a valid shell env variable name")

    gitignore_path = repo_root / ".gitignore"
    if gitignore_path.is_file():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        if secrets_env_file and secrets_env_file not in gitignore_content:
            errors.append(
                ".gitignore must ignore repository.template_bootstrap.secrets_env_file: "
                f"{secrets_env_file}"
            )
        if defaults_env_file and defaults_env_file in gitignore_content:
            errors.append(
                ".gitignore must not ignore repository.template_bootstrap.defaults_env_file: "
                f"{defaults_env_file}"
            )
    return errors


def _declared_runtime_env_vars(spec: dict[str, object]) -> tuple[set[str], str | None]:
    env_names: set[str] = set()

    toggles = spec.get("toggles")
    if isinstance(toggles, dict):
        for raw_name in toggles:
            candidate = str(raw_name).strip()
            if candidate:
                env_names.add(candidate)

    runtime_env_vars = spec.get("runtime_env_vars")
    if isinstance(runtime_env_vars, dict):
        for raw_name in runtime_env_vars:
            candidate = str(raw_name).strip()
            if candidate:
                env_names.add(candidate)
    elif isinstance(runtime_env_vars, list):
        for item in runtime_env_vars:
            if isinstance(item, str):
                candidate = item.strip()
                if candidate:
                    env_names.add(candidate)
                continue
            if not isinstance(item, dict):
                continue
            raw_name = item.get("name")
            if raw_name is None:
                continue
            candidate = str(raw_name).strip()
            if candidate:
                env_names.add(candidate)

    if env_names:
        return env_names, None

    return set(), "contract must define runtime env vars via spec.toggles or spec.runtime_env_vars"


def _validate_async_message_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    spec = contract.raw.get("spec")
    if not isinstance(spec, dict):
        return ["invalid contract raw payload: spec must be a mapping"]

    async_contract = spec.get("async_message_contracts")
    if not isinstance(async_contract, dict):
        return ["missing spec.async_message_contracts contract block"]

    runtime_env_vars, runtime_env_error = _declared_runtime_env_vars(spec)
    if runtime_env_error:
        return [runtime_env_error]

    provider = str(async_contract.get("provider", "")).strip()
    if provider != "pact":
        errors.append("spec.async_message_contracts.provider must be pact")

    enabled_env_var = str(async_contract.get("enabled_env_var", "")).strip()
    if not enabled_env_var:
        errors.append("spec.async_message_contracts.enabled_env_var is required")
    elif enabled_env_var not in runtime_env_vars:
        errors.append(
            "spec.async_message_contracts.enabled_env_var references missing declared env var: "
            f"{enabled_env_var}"
        )

    enabled_by_default_raw = async_contract.get("enabled_by_default")
    if isinstance(enabled_by_default_raw, bool):
        enabled_by_default = enabled_by_default_raw
    elif isinstance(enabled_by_default_raw, str):
        enabled_by_default = _normalize_bool(enabled_by_default_raw)
    else:
        enabled_by_default = False
    if enabled_by_default:
        errors.append("spec.async_message_contracts.enabled_by_default must be false (opt-in)")

    canonical_paths = async_contract.get("canonical_paths")
    if not isinstance(canonical_paths, dict):
        errors.append("spec.async_message_contracts.canonical_paths must be a mapping")
        canonical_paths = {}
    for key in ("producer_contracts_dir", "consumer_contracts_dir", "producer_seed_readme", "consumer_seed_readme"):
        raw_value = canonical_paths.get(key, "")
        path_value = str(raw_value).strip()
        if not path_value:
            errors.append(f"spec.async_message_contracts.canonical_paths.{key} is required")
            continue
        candidate = repo_root / path_value
        if key.endswith("_dir"):
            if not candidate.is_dir():
                errors.append(f"missing async message-contract directory: {path_value}")
        elif not candidate.is_file():
            errors.append(f"missing async message-contract file: {path_value}")

    wrappers = async_contract.get("wrappers")
    if not isinstance(wrappers, dict):
        errors.append("spec.async_message_contracts.wrappers must be a mapping")
        wrappers = {}
    for key in ("producer", "consumer", "all"):
        wrapper_path = str(wrappers.get(key, "")).strip()
        if not wrapper_path:
            errors.append(f"spec.async_message_contracts.wrappers.{key} is required")
            continue
        if not (repo_root / wrapper_path).is_file():
            errors.append(f"missing async message-contract wrapper: {wrapper_path}")

    make_targets_contract = async_contract.get("make_targets")
    if not isinstance(make_targets_contract, dict):
        errors.append("spec.async_message_contracts.make_targets must be a mapping")
        make_targets_contract = {}

    resolved_targets: dict[str, str] = {}
    for key in ("producer", "consumer", "all", "aggregate"):
        target_name = str(make_targets_contract.get(key, "")).strip()
        if not target_name:
            errors.append(f"spec.async_message_contracts.make_targets.{key} is required")
            continue
        resolved_targets[key] = target_name

    make_targets = _make_targets(repo_root)
    for key, target_name in resolved_targets.items():
        if target_name not in make_targets:
            errors.append(
                f"spec.async_message_contracts.make_targets.{key} references missing make target: {target_name}"
            )

    aggregate_target = resolved_targets.get("aggregate")
    async_all_target = resolved_targets.get("all")
    if aggregate_target and async_all_target and aggregate_target == async_all_target:
        errors.append("spec.async_message_contracts.make_targets.aggregate must differ from make_targets.all")

    generated_makefile = repo_root / contract.make_contract.ownership.blueprint_generated_file
    if aggregate_target and async_all_target and generated_makefile.is_file():
        content = generated_makefile.read_text(encoding="utf-8")
        dependency_pattern = re.compile(
            rf"^{re.escape(aggregate_target)}:\s+.*\b{re.escape(async_all_target)}\b",
            flags=re.MULTILINE,
        )
        if dependency_pattern.search(content) is None:
            errors.append(
                "make aggregate lane must depend on async lane in "
                f"{contract.make_contract.ownership.blueprint_generated_file}: "
                f"{aggregate_target} -> {async_all_target}"
            )

    optional_hooks = async_contract.get("optional_hooks")
    if not isinstance(optional_hooks, dict):
        errors.append("spec.async_message_contracts.optional_hooks must be a mapping")
        optional_hooks = {}
    for key in (
        "producer_verify_command_env_var",
        "consumer_verify_command_env_var",
        "producer_publish_command_env_var",
        "can_i_deploy_command_env_var",
    ):
        env_name = str(optional_hooks.get(key, "")).strip()
        if not env_name:
            errors.append(f"spec.async_message_contracts.optional_hooks.{key} is required")
            continue
        if env_name not in runtime_env_vars:
            errors.append(
                "spec.async_message_contracts.optional_hooks references missing declared env var: "
                f"{env_name}"
            )
    return errors


def _required_files_for_repo_mode(contract: BlueprintContract) -> list[str]:
    required_files = list(contract.repository.required_files)
    repository = contract.repository
    if repository.repo_mode != repository.consumer_init.mode_to:
        return required_files

    # Generated-consumer repos intentionally prune source-only paths. Keep the
    # required-files surface mode-aware so source-only files can still be
    # validated in template-source mode without breaking consumer validation.
    source_only_paths = repository.source_only_paths
    return [
        relative_path
        for relative_path in required_files
        if not any(_path_is_same_or_child(relative_path, source_only_path) for source_only_path in source_only_paths)
    ]


def _validate_repository_mode_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    repository = contract.repository
    consumer_init = repository.consumer_init
    source_only_paths = repository.source_only_paths
    consumer_seeded_paths = repository.consumer_seeded_paths
    init_managed_paths = repository.init_managed_paths
    conditional_scaffold_paths = repository.conditional_scaffold_paths

    if not repository.repo_mode:
        errors.append("repository.repo_mode is required")
    elif repository.repo_mode not in repository.allowed_repo_modes:
        errors.append(
            "repository.repo_mode must be one of configured allowed_repo_modes: "
            + ", ".join(repository.allowed_repo_modes)
        )

    if not repository.allowed_repo_modes:
        errors.append("repository.allowed_repo_modes must define at least one repo mode")

    if not consumer_seeded_paths:
        errors.append("repository.ownership_path_classes.consumer_seeded must define at least one path")
    if not init_managed_paths:
        errors.append("repository.ownership_path_classes.init_managed must define at least one path")
    if not conditional_scaffold_paths:
        errors.append("repository.ownership_path_classes.conditional_scaffold must define at least one path")

    if not consumer_init.template_root:
        errors.append("repository.consumer_init.template_root is required")
    elif not (repo_root / consumer_init.template_root).is_dir():
        errors.append(f"missing consumer init template root: {consumer_init.template_root}")

    if consumer_init.mode_from not in repository.allowed_repo_modes:
        errors.append("repository.consumer_init.mode_from must be listed in repository.allowed_repo_modes")
    if consumer_init.mode_to not in repository.allowed_repo_modes:
        errors.append("repository.consumer_init.mode_to must be listed in repository.allowed_repo_modes")
    if consumer_init.mode_from == consumer_init.mode_to:
        errors.append("repository.consumer_init.mode_from and mode_to must differ")

    for relative_path in consumer_seeded_paths:
        template_path = repo_root / consumer_init.template_root / f"{relative_path}.tmpl"
        if not template_path.is_file():
            errors.append(
                "missing consumer init template file for "
                f"{relative_path}: {template_path.relative_to(repo_root).as_posix()}"
            )
        if relative_path not in repository.required_files:
            errors.append(
                "repository.ownership_path_classes.consumer_seeded paths must also be included in "
                f"repository.required_files: {relative_path}"
            )

    overlap = set(source_only_paths) & set(repository.required_files)
    if overlap:
        errors.append(
            "repository.ownership_path_classes.source_only must not overlap with repository.required_files: "
            + ", ".join(sorted(overlap))
        )
    class_overlap = (
        (set(source_only_paths) & set(consumer_seeded_paths))
        | (set(source_only_paths) & set(init_managed_paths))
        | (set(consumer_seeded_paths) & set(init_managed_paths))
    )
    if class_overlap:
        errors.append(
            "repository ownership path classes must be disjoint across source_only, consumer_seeded, and init_managed: "
            + ", ".join(sorted(class_overlap))
        )

    errors.extend(_validate_required_files(repo_root, init_managed_paths))

    expected_conditional_scaffold = {
        module.paths[path_key]
        for module in contract.optional_modules.modules.values()
        if module.scaffolding_mode == "conditional"
        for path_key in module.paths_required_when_enabled
    }
    if set(conditional_scaffold_paths) != expected_conditional_scaffold:
        errors.append(
            "repository.ownership_path_classes.conditional_scaffold must match the union of "
            "optional_modules.*.paths_required_when_enabled"
        )

    if repository.repo_mode == consumer_init.mode_from:
        errors.extend(_validate_required_paths(repo_root, source_only_paths))
    if repository.repo_mode == consumer_init.mode_to:
        errors.extend(_validate_absent_files(repo_root, source_only_paths))

    return errors


def _resolve_branch_name() -> str:
    explicit = os.environ.get("BLUEPRINT_BRANCH_NAME", "").strip()
    if explicit:
        return explicit

    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=_resolve_repo_root(),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""

    if result.returncode != 0:
        return ""

    branch_name = result.stdout.strip()
    if not branch_name or branch_name == "HEAD":
        return ""
    return branch_name


def _validate_branch_naming_contract(contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    default_branch = contract.repository.default_branch
    if not default_branch:
        errors.append("repository.default_branch is required")

    branch_naming = contract.repository.branch_naming
    if branch_naming.model != "github-flow":
        errors.append("repository.branch_naming.model must be github-flow")

    prefixes = branch_naming.purpose_prefixes
    if not prefixes:
        errors.append("repository.branch_naming.purpose_prefixes must define at least one prefix")
        return errors

    seen_prefixes: set[str] = set()
    for prefix in prefixes:
        if prefix in seen_prefixes:
            errors.append(f"duplicate branch purpose prefix: {prefix}")
            continue
        seen_prefixes.add(prefix)

        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*/", prefix):
            errors.append(
                f"invalid branch purpose prefix format: {prefix} (expected lowercase kebab-case with trailing '/')"
            )

    required_flow_prefixes = {"feature/", "fix/", "chore/", "docs/"}
    missing_required = sorted(required_flow_prefixes - seen_prefixes)
    if missing_required:
        errors.append("missing required github-flow purpose prefixes: " + ", ".join(missing_required))

    branch_name = _resolve_branch_name()
    if not branch_name or (default_branch and branch_name == default_branch):
        return errors

    matching_prefixes = [prefix for prefix in prefixes if branch_name.startswith(prefix)]
    if not matching_prefixes:
        errors.append(
            f"branch '{branch_name}' must start with one of configured purpose prefixes: {', '.join(prefixes)}"
        )
        return errors

    matched_prefix = matching_prefixes[0]
    if branch_name == matched_prefix:
        errors.append(
            f"branch '{branch_name}' must include a descriptive suffix after prefix '{matched_prefix}'"
        )
    return errors


def _validate_make_contract(repo_root: Path, required_targets: list[str], required_namespaces: list[str]) -> list[str]:
    errors: list[str] = []
    targets = _make_targets(repo_root)
    if not targets:
        return ["Makefile not found or no targets discovered"]

    for required in required_targets:
        if required not in targets:
            errors.append(f"missing make target: {required}")

    for namespace in required_namespaces:
        if not any(target.startswith(namespace) for target in targets):
            errors.append(f"missing make namespace: {namespace}")

    makefile_text = "\n".join(path.read_text(encoding="utf-8") for path in _makefile_paths(repo_root))
    if not re.search(r"^help:.*##", makefile_text, flags=re.MULTILINE):
        errors.append("Makefile help target must include a ## self-documenting description")

    return errors


def _validate_make_ownership_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    ownership = contract.make_contract.ownership

    root_loader_file = ownership.root_loader_file
    blueprint_generated_file = ownership.blueprint_generated_file
    platform_editable_file = ownership.platform_editable_file
    platform_editable_include_dir = ownership.platform_editable_include_dir
    platform_seed_mode = ownership.platform_seed_mode

    if not root_loader_file:
        errors.append("make_contract.ownership.root_loader_file is required")
    if not blueprint_generated_file:
        errors.append("make_contract.ownership.blueprint_generated_file is required")
    if not platform_editable_file:
        errors.append("make_contract.ownership.platform_editable_file is required")
    if not platform_editable_include_dir:
        errors.append("make_contract.ownership.platform_editable_include_dir is required")
    if platform_seed_mode != "create_if_missing":
        errors.append("make_contract.ownership.platform_seed_mode must be create_if_missing")

    root_loader_path = repo_root / root_loader_file if root_loader_file else None
    if root_loader_path and not root_loader_path.is_file():
        errors.append(f"missing make root loader file: {root_loader_file}")

    blueprint_generated_path = repo_root / blueprint_generated_file if blueprint_generated_file else None
    if blueprint_generated_path and not blueprint_generated_path.is_file():
        errors.append(f"missing blueprint generated make file: {blueprint_generated_file}")

    platform_editable_path = repo_root / platform_editable_file if platform_editable_file else None
    if platform_editable_path and not platform_editable_path.is_file():
        errors.append(f"missing platform editable make file: {platform_editable_file}")

    platform_editable_include_path = repo_root / platform_editable_include_dir if platform_editable_include_dir else None
    if platform_editable_include_path and not platform_editable_include_path.is_dir():
        errors.append(f"missing platform editable make include dir: {platform_editable_include_dir}")

    if root_loader_path and root_loader_path.is_file():
        loader_text = root_loader_path.read_text(encoding="utf-8")
        if "include $(BLUEPRINT_MAKEFILE)" not in loader_text:
            errors.append(
                "root Makefile loader must include blueprint generated make include: include $(BLUEPRINT_MAKEFILE)"
            )
        if "-include $(PLATFORM_MAKEFILE)" not in loader_text:
            errors.append(
                "root Makefile loader must include platform editable make include: -include $(PLATFORM_MAKEFILE)"
            )
        if "-include $(wildcard $(PLATFORM_MAKEFILES_DIR)/*.mk)" not in loader_text:
            errors.append(
                "root Makefile loader must include platform include-dir wildcard: "
                "-include $(wildcard $(PLATFORM_MAKEFILES_DIR)/*.mk)"
            )

    return errors


def _validate_optional_target_materialization_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    materialization = contract.make_contract.optional_target_materialization

    if materialization.mode != "conditional":
        errors.append("make_contract.optional_target_materialization.mode must be conditional")

    source_template = materialization.source_template
    if not source_template:
        errors.append("make_contract.optional_target_materialization.source_template is required")
    elif not (repo_root / source_template).is_file():
        errors.append("missing optional-target materialization template: " f"{source_template}")

    output_file = materialization.output_file
    if not output_file:
        errors.append("make_contract.optional_target_materialization.output_file is required")
    elif not (repo_root / output_file).is_file():
        errors.append("missing optional-target materialization output file: " f"{output_file}")

    materialization_command = materialization.materialization_command
    if not materialization_command:
        errors.append("make_contract.optional_target_materialization.materialization_command is required")
    elif not materialization_command.startswith("make "):
        errors.append("make_contract.optional_target_materialization.materialization_command must start with 'make '")
    else:
        target = materialization_command.split(maxsplit=1)[1].strip()
        if not target:
            errors.append(
                "make_contract.optional_target_materialization.materialization_command must include a make target"
            )
        elif target not in _make_targets(repo_root):
            errors.append(
                "make_contract.optional_target_materialization.materialization_command references missing make target: "
                f"{target}"
            )

    return errors


def _validate_shell_scripts(repo_root: Path, globs: list[str]) -> list[str]:
    errors: list[str] = []
    discovered: list[Path] = []
    for glob in globs:
        discovered.extend(sorted(repo_root.glob(glob)))
    discovered = sorted({path for path in discovered if path.is_file()})
    if not discovered:
        return ["no shell scripts discovered from configured shell globs"]

    shebang = "#!/usr/bin/env bash"
    for path in discovered:
        relative = path.relative_to(repo_root).as_posix()
        if relative.startswith("scripts/bin/") and path.stat().st_mode & 0o111 == 0:
            errors.append(f"script not executable: {path.relative_to(repo_root)}")
        first_line = path.read_text(encoding="utf-8").splitlines()
        if not first_line or first_line[0].strip() != shebang:
            errors.append(f"invalid/missing shebang: {path.relative_to(repo_root)}")
    return errors


def _validate_script_ownership_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    blueprint_roots = contract.script_contract.blueprint_managed_roots
    platform_roots = contract.script_contract.platform_editable_roots
    if not blueprint_roots:
        errors.append("script_contract.blueprint_managed_roots must define at least one root")
    if not platform_roots:
        errors.append("script_contract.platform_editable_roots must define at least one root")

    overlap = sorted(set(blueprint_roots) & set(platform_roots))
    if overlap:
        errors.append("script_contract roots overlap between blueprint/platform: " + ", ".join(overlap))

    for root in blueprint_roots + platform_roots:
        if not root.endswith("/"):
            errors.append(f"script_contract root must end with '/': {root}")
            continue
        path = repo_root / root
        if not path.is_dir():
            errors.append(f"missing script_contract root directory: {root}")

    for root in platform_roots:
        if not root.startswith("scripts/bin/platform/") and not root.startswith("scripts/lib/platform/"):
            errors.append(
                "script_contract.platform_editable_roots must be under scripts/bin/platform or scripts/lib/platform: "
                f"{root}"
            )

    return errors


def _validate_mermaid_docs(repo_root: Path, mermaid_files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in mermaid_files:
        path = repo_root / relative_path
        if not path.is_file():
            errors.append(f"missing mermaid markdown file: {relative_path}")
            continue
        if "```mermaid" not in path.read_text(encoding="utf-8"):
            errors.append(f"mermaid block missing in: {relative_path}")
    return errors


def _expand_optional_module_path(path_value: str) -> list[str]:
    if "${ENV}" not in path_value:
        return [path_value]
    return [path_value.replace("${ENV}", env) for env in ("local", "dev", "stage", "prod")]


def _is_optional_module_enabled(contract: BlueprintContract, module_name: str) -> bool:
    module = contract.optional_modules.modules.get(module_name)
    if not module:
        return False

    enable_flag = module.enable_flag
    enabled_by_default = module.enabled_by_default
    if not enable_flag:
        return enabled_by_default

    env_value = os.environ.get(enable_flag)
    if env_value is None:
        return enabled_by_default
    return _normalize_bool(env_value)


def _validate_optional_module_paths(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []

    for module_name, module in contract.optional_modules.modules.items():
        for key, value in module.paths.items():
            is_conditionally_required = (
                module.scaffolding_mode == "conditional" and key in set(module.paths_required_when_enabled)
            )
            module_enabled = _is_optional_module_enabled(contract, module_name)
            if is_conditionally_required and not module_enabled:
                continue

            for expanded in _expand_optional_module_path(value):
                path = repo_root / expanded
                if key == "helm_path" and expanded.endswith("/observability"):
                    if not path.is_dir():
                        errors.append(f"missing module path for module={module_name} key={key}: {expanded}")
                    continue
                if not path.exists():
                    errors.append(f"missing module path for module={module_name} key={key}: {expanded}")
    return errors


def _validate_optional_module_make_targets(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    targets = _make_targets(repo_root)

    for module_name, module in contract.optional_modules.modules.items():
        make_targets = module.make_targets
        if not make_targets:
            errors.append(f"missing optional module make_targets list: {module_name}")
            continue

        if module.make_targets_mode != "conditional":
            errors.append(f"optional module make_targets_mode must be conditional for module={module_name}")

        module_enabled = _is_optional_module_enabled(contract, module_name)
        for make_target in make_targets:
            target_exists = make_target in targets
            if module_enabled and not target_exists:
                errors.append(f"missing optional-module make target for enabled module={module_name}: {make_target}")
            if not module_enabled and target_exists:
                errors.append(
                    "optional-module make target must not be materialized when module disabled "
                    f"module={module_name}: {make_target}"
                )

    return errors


def _module_wrapper_template_name(make_target: str) -> str:
    target = make_target.removeprefix("infra-")
    return target.replace("-", "_")


def _validate_module_wrapper_skeleton_templates(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    templates_root = repo_root / "scripts/templates/infra/module_wrappers"
    if not templates_root.is_dir():
        return ["missing optional-module wrapper template root: scripts/templates/infra/module_wrappers"]

    for module_name, module in contract.optional_modules.modules.items():
        module_dir = templates_root / module_name
        if not module_dir.is_dir():
            errors.append(
                "missing optional-module wrapper template directory for module="
                f"{module_name}: {module_dir.relative_to(repo_root).as_posix()}"
            )
            continue
        for make_target in module.make_targets:
            template_name = _module_wrapper_template_name(make_target)
            template_path = module_dir / f"{template_name}.sh.tmpl"
            if not template_path.is_file():
                errors.append(
                    "missing optional-module wrapper skeleton template for module="
                    f"{module_name} target={make_target}: {template_path.relative_to(repo_root).as_posix()}"
                )
    return errors


def _validate_airflow_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    if not _is_optional_module_enabled(contract, "workflows"):
        return errors

    layout = contract.architecture.airflow_dag_layout

    if layout.shared_bootstrap_file:
        path = repo_root / layout.shared_bootstrap_file
        if not path.is_file():
            errors.append(f"missing airflow shared bootstrap file: {layout.shared_bootstrap_file}")

    forbid_pattern = layout.forbid_dag_entrypoints_under
    if forbid_pattern == "apps/**":
        apps_root = repo_root / "apps"
        if apps_root.is_dir():
            dag_files = sorted(apps_root.rglob("*dag*.py"))
            if dag_files:
                first = dag_files[0].relative_to(repo_root)
                errors.append(f"dag entrypoint forbidden under apps/** (found: {first})")

    airflow_ignore = repo_root / "dags/.airflowignore"
    if layout.airflowignore_must_restrict_parser_scope and not airflow_ignore.is_file():
        errors.append("missing airflow parser scope file: dags/.airflowignore")
    elif airflow_ignore.is_file() and forbid_pattern and forbid_pattern not in airflow_ignore.read_text(encoding="utf-8"):
        errors.append(f"dags/.airflowignore must include parser-scope rule: {forbid_pattern}")

    return errors


def _validate_docs_edit_link(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    if not contract.docs_contract.edit_link_enabled:
        return errors

    docusaurus_config = repo_root / "docs/docusaurus.config.js"
    if not docusaurus_config.is_file():
        return ["missing docs config file: docs/docusaurus.config.js"]

    content = docusaurus_config.read_text(encoding="utf-8")
    if "editUrl" not in content:
        errors.append("docs edit_link_enabled=true requires editUrl in docs/docusaurus.config.js")
    return errors


def _validate_platform_docs_seed_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    platform_docs = contract.docs_contract.platform_docs

    platform_root = platform_docs.root
    if not platform_root:
        errors.append("docs_contract.platform_docs.root is required")
    elif not (repo_root / platform_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.root directory: {platform_root}")

    if platform_docs.seed_mode != "create_if_missing":
        errors.append("docs_contract.platform_docs.seed_mode must be create_if_missing")

    if platform_docs.bootstrap_command != "make blueprint-bootstrap":
        errors.append("docs_contract.platform_docs.bootstrap_command must be make blueprint-bootstrap")
    elif "blueprint-bootstrap" not in _make_targets(repo_root):
        errors.append("docs_contract.platform_docs.bootstrap_command references missing make target: blueprint-bootstrap")

    template_root = platform_docs.template_root
    if not template_root:
        errors.append("docs_contract.platform_docs.template_root is required")
    elif not (repo_root / template_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.template_root directory: {template_root}")

    required_seed_files = platform_docs.required_seed_files
    if not required_seed_files:
        errors.append("docs_contract.platform_docs.required_seed_files must define at least one file")
        return errors

    for relative_path in required_seed_files:
        target_path = repo_root / relative_path
        if not target_path.is_file():
            errors.append(f"missing platform docs seed file: {relative_path}")
            continue
        if not target_path.read_text(encoding="utf-8").strip():
            errors.append(f"platform docs seed file is empty: {relative_path}")

        if platform_root and not relative_path.startswith(f"{platform_root}/"):
            errors.append(
                "platform docs seed file must be under configured root " f"{platform_root}: {relative_path}"
            )
            continue

        if not template_root or not platform_root:
            continue
        suffix = relative_path.removeprefix(f"{platform_root}/")
        template_path = repo_root / template_root / suffix
        if not template_path.is_file():
            errors.append(
                "missing platform docs seed template file for "
                f"{relative_path}: {(Path(template_root) / suffix).as_posix()}"
            )
            continue
        template_lines = template_path.read_text(encoding="utf-8").splitlines()
        first_nonempty = next((line.strip() for line in template_lines if line.strip()), "")
        if not first_nonempty.startswith("# "):
            errors.append(
                "platform docs seed template must start with a markdown heading: "
                f"{(Path(template_root) / suffix).as_posix()}"
            )

    return errors


def _validate_bootstrap_template_sync(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    repository = contract.repository
    consumer_owned_seed_paths = set(repository.consumer_seeded_paths)
    init_managed_paths = set(repository.init_managed_paths)

    # These files are materialized by blueprint-bootstrap/infra-bootstrap from
    # static templates and must stay byte-for-byte synchronized to keep generated
    # repositories stable.
    template_sync_contract = (
        (
            repo_root / "scripts/templates/blueprint/bootstrap",
            (
                "Makefile",
                ".editorconfig",
                ".gitignore",
                ".dockerignore",
                ".pre-commit-config.yaml",
                "blueprint/contract.yaml",
                "blueprint/repo.init.env",
                "blueprint/repo.init.secrets.example.env",
                "docs/docusaurus.config.js",
                "docs/README.md",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/ownership_matrix.md",
            ),
        ),
        (
            repo_root / "scripts/templates/infra/bootstrap",
            (
                "tests/infra/modules/observability/README.md",
                "infra/local/crossplane/kustomization.yaml",
                "infra/local/crossplane/namespace.yaml",
                "infra/local/helm/core/argocd.values.yaml",
                "infra/local/helm/core/external-secrets.values.yaml",
                "infra/local/helm/core/crossplane.values.yaml",
                "infra/local/helm/observability/grafana.values.yaml",
                "infra/local/helm/observability/otel-collector.values.yaml",
                "infra/gitops/argocd/base/kustomization.yaml",
                "infra/gitops/argocd/base/namespace.yaml",
                "infra/gitops/argocd/environments/dev/kustomization.yaml",
                "infra/gitops/argocd/environments/dev/platform-config.yaml",
                "infra/gitops/argocd/overlays/local/kustomization.yaml",
                "infra/gitops/platform/base/kustomization.yaml",
                "infra/gitops/platform/base/namespaces.yaml",
                "infra/gitops/platform/base/security/kustomization.yaml",
                "infra/gitops/platform/base/security/runtime-source-store.yaml",
                "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
                "infra/gitops/platform/environments/local/kustomization.yaml",
                "infra/gitops/platform/environments/local/runtime-contract-configmap.yaml",
                "infra/gitops/platform/environments/dev/kustomization.yaml",
                "infra/gitops/platform/environments/dev/runtime-contract-configmap.yaml",
            ),
        ),
    )

    # These ArgoCD files are intentionally rewritten by blueprint-init-repo to
    # inject repository identity (repoURL). They are validated by placeholder/
    # identity checks, not by strict byte-for-byte template sync.
    # The platform extensions kustomization is intentionally excluded from strict
    # sync so generated repos can extend security/runtime topology safely.
    for template_root, synced_files in template_sync_contract:
        for rel_path in synced_files:
            # Generated consumer repos replace a small set of source-root docs/CI
            # files during blueprint-init-repo, so those files no longer follow
            # the source bootstrap template byte-for-byte afterwards.
            if repository.repo_mode == repository.consumer_init.mode_to and (
                rel_path in consumer_owned_seed_paths or rel_path in init_managed_paths
            ):
                continue
            target_path = repo_root / rel_path
            template_path = template_root / rel_path
            template_rel = template_path.relative_to(repo_root).as_posix()
            if not target_path.is_file():
                errors.append(f"missing bootstrap target file for template sync: {rel_path}")
                continue
            if not template_path.is_file():
                errors.append(f"missing bootstrap template file: {template_rel}")
                continue
            if target_path.read_text(encoding="utf-8") != template_path.read_text(encoding="utf-8"):
                errors.append("bootstrap template drift detected for " f"{rel_path}; sync with {template_rel}")
    return errors


def parse_args() -> argparse.Namespace:
    repo_root = _resolve_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract-path",
        default=str(repo_root / "blueprint/contract.yaml"),
        help="Path to blueprint contract YAML.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = _resolve_repo_root()
    contract_path = Path(args.contract_path).resolve()

    try:
        contract = load_blueprint_contract(contract_path)
        required_files = _required_files_for_repo_mode(contract)
        required_paths = contract.structure.required_paths
        required_diagrams = contract.docs_contract.required_diagrams
        required_targets = contract.make_contract.required_targets
        required_namespaces = contract.make_contract.required_namespaces
        if not required_files:
            raise ValueError("required_files list is empty")
        if not required_paths:
            raise ValueError("required_paths list is empty")
        if not required_targets:
            raise ValueError("required_targets list is empty")
        if not required_namespaces:
            raise ValueError("required_namespaces list is empty")
    except ValueError as exc:
        print(f"[infra-validate] contract error: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(_validate_repository_mode_contract(repo_root, contract))
    errors.extend(_validate_required_files(repo_root, required_files))
    errors.extend(_validate_required_paths(repo_root, required_paths))
    errors.extend(_validate_template_bootstrap_contract(repo_root, contract))
    errors.extend(_validate_async_message_contract(repo_root, contract))
    errors.extend(_validate_branch_naming_contract(contract))
    errors.extend(_validate_make_contract(repo_root, required_targets, required_namespaces))
    errors.extend(_validate_make_ownership_contract(repo_root, contract))
    errors.extend(_validate_optional_target_materialization_contract(repo_root, contract))
    errors.extend(_validate_script_ownership_contract(repo_root, contract))
    errors.extend(_validate_shell_scripts(repo_root, ["scripts/bin/**/*.sh", "scripts/lib/**/*.sh"]))
    errors.extend(_validate_mermaid_docs(repo_root, required_diagrams))
    errors.extend(_validate_optional_module_paths(repo_root, contract))
    errors.extend(_validate_optional_module_make_targets(repo_root, contract))
    errors.extend(_validate_module_wrapper_skeleton_templates(repo_root, contract))
    errors.extend(_validate_airflow_contract(repo_root, contract))
    errors.extend(_validate_docs_edit_link(repo_root, contract))
    errors.extend(_validate_platform_docs_seed_contract(repo_root, contract))
    errors.extend(_validate_runtime_credentials_contract(repo_root))
    errors.extend(_validate_event_messaging_contract(repo_root, contract))
    errors.extend(_validate_zero_downtime_evolution_contract(repo_root, contract))
    errors.extend(_validate_tenant_context_contract(contract))
    errors.extend(_validate_bootstrap_template_sync(repo_root, contract))

    if errors:
        for error in errors:
            print(f"[infra-validate] error: {error}", file=sys.stderr)
        print(f"[infra-validate] failed with {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print("[infra-validate] contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
