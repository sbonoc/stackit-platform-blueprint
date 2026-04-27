"""Consumer app descriptor — loader, safe path resolver, and validators.

Reads `apps/descriptor.yaml` (consumer-owned, S1 contract entry) with safe YAML
parsing, applies schema and path-safety rules, resolves explicit + convention
default manifest references under `infra/gitops/platform/base/apps/`, and
verifies kustomization membership.

Requirements covered: FR-003, FR-004, FR-005, FR-006, NFR-SEC-001, NFR-OBS-001,
AC-002, AC-003, AC-004.

Presence policy (NFR-REL-001 — hard-fail in template-source/new-init paths,
warn-only for existing-consumer migration) is owned by the upgrade-side wiring
(S4) and is intentionally NOT enforced here. ``validate_app_descriptor`` skips
silently when the descriptor file is absent so the validator is safe to invoke
in any repo mode.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

DESCRIPTOR_RELATIVE_PATH = "apps/descriptor.yaml"
APP_RUNTIME_MANIFEST_BASE = "infra/gitops/platform/base/apps"
KUSTOMIZATION_RELATIVE_PATH = f"{APP_RUNTIME_MANIFEST_BASE}/kustomization.yaml"

# DNS-style label rule (Kubernetes convention). Rejects `..`, `/`, shell
# metacharacters, leading/trailing hyphens, uppercase, and empty strings —
# satisfies the AC-002 unsafe-id cases (`../bad`, `nested/app`, `api;rm`) by
# construction.
_SAFE_ID_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_UNSAFE_PATH_CHARS = frozenset(';|&$`<>*?[]{}\\"\'\x00\n\r\t')


@dataclass(frozen=True)
class ResolvedComponent:
    app_id: str
    component_id: str
    kind: str
    deployment_manifest: str
    service_manifest: str
    service: dict
    health: dict


@dataclass(frozen=True)
class ResolvedDescriptor:
    schema_version: str
    components: tuple[ResolvedComponent, ...]


def load_app_descriptor(
    descriptor_path: Path,
) -> tuple[ResolvedDescriptor | None, list[str]]:
    """Parse + validate the descriptor at ``descriptor_path``.

    Returns ``(descriptor, errors)``. ``descriptor`` is None when the file is
    missing, unparseable, or missing the top-level ``apps`` list — cases where
    no useful resolved view can be produced. Otherwise ``descriptor`` is
    populated with whatever components could be resolved; errors collect every
    non-fatal validation failure encountered along the way.
    """
    errors: list[str] = []
    if not descriptor_path.is_file():
        errors.append(f"{descriptor_path}: descriptor file is missing")
        return None, errors

    try:
        raw = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{descriptor_path}: failed to parse YAML: {exc}")
        return None, errors

    if not isinstance(raw, dict):
        errors.append(f"{descriptor_path}: top-level must be a mapping")
        return None, errors

    schema_version = raw.get("schemaVersion")
    if not isinstance(schema_version, str) or not schema_version.strip():
        errors.append(
            f"{descriptor_path}: schemaVersion must be a non-empty string"
        )
        schema_version = ""

    apps = raw.get("apps")
    if not isinstance(apps, list) or not apps:
        errors.append(f"{descriptor_path}: apps must be a non-empty list")
        return None, errors

    components: list[ResolvedComponent] = []
    for app_index, app in enumerate(apps):
        components.extend(_collect_app_components(descriptor_path, app_index, app, errors))

    descriptor = ResolvedDescriptor(
        schema_version=schema_version,
        components=tuple(components),
    )
    return descriptor, errors


def _collect_app_components(
    descriptor_path: Path,
    app_index: int,
    app: object,
    errors: list[str],
) -> list[ResolvedComponent]:
    if not isinstance(app, dict):
        errors.append(f"{descriptor_path}: apps[{app_index}] must be a mapping")
        return []

    app_id = app.get("id")
    if not isinstance(app_id, str) or not _SAFE_ID_RE.match(app_id):
        errors.append(
            f"{descriptor_path}: apps[{app_index}].id must be a DNS-style label "
            f"(lowercase alphanumerics and hyphens; no '/', '..', or shell metacharacters): {app_id!r}"
        )
        return []

    owner = app.get("owner")
    if (
        not isinstance(owner, dict)
        or not isinstance(owner.get("team"), str)
        or not owner["team"].strip()
    ):
        errors.append(
            f"{descriptor_path}: app[{app_id}].owner.team is required (non-empty string)"
        )

    raw_components = app.get("components")
    if not isinstance(raw_components, list) or not raw_components:
        errors.append(
            f"{descriptor_path}: app[{app_id}].components must be a non-empty list"
        )
        return []

    resolved: list[ResolvedComponent] = []
    for comp_index, comp in enumerate(raw_components):
        component = _resolve_component(descriptor_path, app_id, comp_index, comp, errors)
        if component is not None:
            resolved.append(component)
    return resolved


def _resolve_component(
    descriptor_path: Path,
    app_id: str,
    comp_index: int,
    comp: object,
    errors: list[str],
) -> ResolvedComponent | None:
    if not isinstance(comp, dict):
        errors.append(
            f"{descriptor_path}: app[{app_id}].components[{comp_index}] must be a mapping"
        )
        return None

    comp_id = comp.get("id")
    if not isinstance(comp_id, str) or not _SAFE_ID_RE.match(comp_id):
        errors.append(
            f"{descriptor_path}: app[{app_id}].components[{comp_index}].id must be a "
            f"DNS-style label: {comp_id!r}"
        )
        return None

    kind = comp.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        errors.append(
            f"{descriptor_path}: app[{app_id}].component[{comp_id}].kind is required"
        )
        return None

    manifests_raw_value = comp.get("manifests")
    if manifests_raw_value is None:
        manifests_raw: dict = {}
    elif not isinstance(manifests_raw_value, dict):
        errors.append(
            f"{descriptor_path}: app[{app_id}].component[{comp_id}].manifests must be a "
            f"mapping (got {type(manifests_raw_value).__name__}); explicit deployment/service "
            f"paths must be declared as a YAML mapping, not a scalar or list"
        )
        return None
    else:
        manifests_raw = manifests_raw_value
    deployment_path, dep_errs = _resolve_manifest_path(
        descriptor_path, app_id, comp_id, manifests_raw, "deployment"
    )
    service_path, svc_errs = _resolve_manifest_path(
        descriptor_path, app_id, comp_id, manifests_raw, "service"
    )
    errors.extend(dep_errs)
    errors.extend(svc_errs)
    if dep_errs or svc_errs:
        return None

    service = comp.get("service") if isinstance(comp.get("service"), dict) else {}
    health = comp.get("health") if isinstance(comp.get("health"), dict) else {}
    return ResolvedComponent(
        app_id=app_id,
        component_id=comp_id,
        kind=kind,
        deployment_manifest=deployment_path,
        service_manifest=service_path,
        service=service,
        health=health,
    )


def _resolve_manifest_path(
    descriptor_path: Path,
    app_id: str,
    component_id: str,
    manifests_raw: dict,
    kind: str,
) -> tuple[str, list[str]]:
    """Return ``(resolved_path, errors)``.

    Falls back to the convention default
    ``infra/gitops/platform/base/apps/{component_id}-{kind}.yaml`` when the
    component omits the explicit reference (FR-004).
    """
    explicit = manifests_raw.get(kind)
    if explicit is None:
        path = f"{APP_RUNTIME_MANIFEST_BASE}/{component_id}-{kind}.yaml"
    else:
        if not isinstance(explicit, str) or not explicit.strip():
            return "", [
                f"{descriptor_path}: app[{app_id}].component[{component_id}].manifests.{kind} "
                f"must be a non-empty string"
            ]
        path = explicit

    errs = _validate_manifest_path(descriptor_path, app_id, component_id, kind, path)
    return path, errs


def _validate_manifest_path(
    descriptor_path: Path,
    app_id: str,
    component_id: str,
    kind: str,
    path: str,
) -> list[str]:
    """Reject absolute paths, parent traversal, shell metacharacters, and
    paths that don't live under ``APP_RUNTIME_MANIFEST_BASE/`` (NFR-SEC-001)."""
    label = (
        f"{descriptor_path}: app[{app_id}].component[{component_id}].manifests.{kind}"
    )
    if any(c in _UNSAFE_PATH_CHARS for c in path):
        return [f"{label} contains unsafe characters: {path!r}"]
    if path.startswith("/"):
        return [
            f"{label} must be a relative path under {APP_RUNTIME_MANIFEST_BASE}/: {path!r}"
        ]
    parts = path.split("/")
    if ".." in parts or any(part == "" for part in parts):
        return [
            f"{label} must not contain empty segments or '..': {path!r}"
        ]
    if not path.startswith(f"{APP_RUNTIME_MANIFEST_BASE}/"):
        return [
            f"{label} must live under {APP_RUNTIME_MANIFEST_BASE}/: {path!r}"
        ]
    return []


def verify_resolved_manifests_exist(
    repo_root: Path, descriptor: ResolvedDescriptor
) -> list[str]:
    """Verify every resolved manifest exists on disk (FR-006, AC-003)."""
    errors: list[str] = []
    for component in descriptor.components:
        for kind, rel_path in (
            ("deployment", component.deployment_manifest),
            ("service", component.service_manifest),
        ):
            if not (repo_root / rel_path).is_file():
                errors.append(
                    f"{DESCRIPTOR_RELATIVE_PATH}: app[{component.app_id}]."
                    f"component[{component.component_id}]: {kind} manifest missing: {rel_path}"
                )
    return errors


def verify_kustomization_membership(
    repo_root: Path,
    descriptor: ResolvedDescriptor,
    kustomization_resources: Callable[[Path], set[str]],
) -> list[str]:
    """Verify each resolved manifest filename is listed in
    ``infra/gitops/platform/base/apps/kustomization.yaml`` (FR-006, AC-004)."""
    errors: list[str] = []
    kustomization_path = repo_root / KUSTOMIZATION_RELATIVE_PATH
    if not kustomization_path.is_file():
        errors.append(
            f"{DESCRIPTOR_RELATIVE_PATH}: kustomization manifest missing: "
            f"{KUSTOMIZATION_RELATIVE_PATH}"
        )
        return errors
    resources = kustomization_resources(kustomization_path)
    for component in descriptor.components:
        for kind, rel_path in (
            ("deployment", component.deployment_manifest),
            ("service", component.service_manifest),
        ):
            filename = Path(rel_path).name
            if filename not in resources:
                errors.append(
                    f"{DESCRIPTOR_RELATIVE_PATH}: app[{component.app_id}]."
                    f"component[{component.component_id}]: {kind} manifest filename not listed "
                    f"in {KUSTOMIZATION_RELATIVE_PATH}: {filename}"
                )
    return errors


def validate_app_descriptor(
    repo_root: Path,
    kustomization_resources: Callable[[Path], set[str]],
) -> list[str]:
    """Top-level descriptor validation entry point.

    Returns the combined error list from schema/path validation plus manifest
    existence and kustomization membership. Skips silently when
    ``apps/descriptor.yaml`` is absent — presence policy lives elsewhere.
    """
    descriptor_path = repo_root / DESCRIPTOR_RELATIVE_PATH
    if not descriptor_path.is_file():
        return []
    descriptor, errors = load_app_descriptor(descriptor_path)
    if descriptor is None:
        return errors
    errors.extend(verify_resolved_manifests_exist(repo_root, descriptor))
    errors.extend(verify_kustomization_membership(repo_root, descriptor, kustomization_resources))
    return errors
