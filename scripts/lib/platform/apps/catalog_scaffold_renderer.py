#!/usr/bin/env python3
"""Render and validate app catalog scaffold artifacts from typed inputs.

App catalog manifest entries (`deliveryTopology.workloads` and
`runtimeDeliveryContract.gitopsWorkloads`) are derived from the consumer-owned
`apps/descriptor.yaml` (loaded via `scripts.lib.blueprint.app_descriptor`).
Image and image-env-var bindings per component are supplied by the caller via
the repeatable `--component-image ID=IMAGE` and `--component-image-env-var
ID=ENV_VAR` flags so the renderer holds no baseline workload knowledge of its
own.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from string import Template
from typing import Iterable


_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.blueprint.app_descriptor import (  # noqa: E402
    ResolvedComponent,
    ResolvedDescriptor,
    load_app_descriptor,
)


REQUIRED_MANIFEST_MARKERS: tuple[str, ...] = (
    "schemaVersion:",
    "appVersionContract:",
    "runtimePinnedVersions:",
    "frameworkPinnedVersions:",
    "deliveryTopology:",
    "runtimeDeliveryContract:",
    "observabilityRuntimeContract:",
)

WORKLOAD_NAMESPACE = "apps"
APP_RUNTIME_MANIFEST_BASE = "infra/gitops/platform/base/apps"


@dataclass(frozen=True)
class CatalogRenderContext:
    python_runtime_base_image_version: str
    node_runtime_base_image_version: str
    nginx_runtime_base_image_version: str
    fastapi_version: str
    pydantic_version: str
    vue_version: str
    vue_router_version: str
    pinia_version: str
    app_runtime_gitops_enabled: bool
    app_descriptor_path: Path
    component_image: dict[str, str]
    component_image_env_var: dict[str, str]
    observability_enabled: bool
    otel_exporter_otlp_endpoint: str
    otel_protocol: str
    otel_traces_enabled: bool
    otel_metrics_enabled: bool
    otel_logs_enabled: bool
    faro_enabled: bool
    faro_collect_path: str

    @staticmethod
    def _require_non_empty(value: str, field_name: str) -> str:
        normalized = value.strip()
        if normalized == "":
            raise ValueError(f"{field_name} must be non-empty")
        return normalized

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CatalogRenderContext":
        return cls(
            python_runtime_base_image_version=cls._require_non_empty(
                args.python_runtime_base_image_version,
                "python_runtime_base_image_version",
            ),
            node_runtime_base_image_version=cls._require_non_empty(
                args.node_runtime_base_image_version,
                "node_runtime_base_image_version",
            ),
            nginx_runtime_base_image_version=cls._require_non_empty(
                args.nginx_runtime_base_image_version,
                "nginx_runtime_base_image_version",
            ),
            fastapi_version=cls._require_non_empty(args.fastapi_version, "fastapi_version"),
            pydantic_version=cls._require_non_empty(args.pydantic_version, "pydantic_version"),
            vue_version=cls._require_non_empty(args.vue_version, "vue_version"),
            vue_router_version=cls._require_non_empty(args.vue_router_version, "vue_router_version"),
            pinia_version=cls._require_non_empty(args.pinia_version, "pinia_version"),
            app_runtime_gitops_enabled=args.app_runtime_gitops_enabled,
            app_descriptor_path=Path(
                cls._require_non_empty(args.app_descriptor_path, "app_descriptor_path")
            ),
            component_image=_parse_id_value_pairs(args.component_image, "component_image"),
            component_image_env_var=_parse_id_value_pairs(
                args.component_image_env_var, "component_image_env_var"
            ),
            observability_enabled=args.observability_enabled,
            otel_exporter_otlp_endpoint=args.otel_exporter_otlp_endpoint,
            otel_protocol=args.otel_protocol,
            otel_traces_enabled=args.otel_traces_enabled,
            otel_metrics_enabled=args.otel_metrics_enabled,
            otel_logs_enabled=args.otel_logs_enabled,
            faro_enabled=args.faro_enabled,
            faro_collect_path=args.faro_collect_path,
        )


def _parse_id_value_pairs(entries: Iterable[str] | None, field_name: str) -> dict[str, str]:
    """Parse ``ID=value`` repeatable CLI entries into a dict."""
    parsed: dict[str, str] = {}
    if entries is None:
        return parsed
    for raw in entries:
        if "=" not in raw:
            raise ValueError(
                f"--{field_name.replace('_', '-')} entry must be ID=value: {raw!r}"
            )
        component_id, _, value = raw.partition("=")
        component_id = component_id.strip()
        value = value.strip()
        if not component_id or not value:
            raise ValueError(
                f"--{field_name.replace('_', '-')} entry has empty id or value: {raw!r}"
            )
        if component_id in parsed:
            raise ValueError(
                f"--{field_name.replace('_', '-')} duplicate id: {component_id}"
            )
        parsed[component_id] = value
    return parsed


def _load_descriptor(descriptor_path: Path) -> tuple[ResolvedDescriptor | None, list[str]]:
    """Thin wrapper around `load_app_descriptor` for renderer-internal use."""
    return load_app_descriptor(descriptor_path)


def _indent_block(lines: list[str], spaces: int) -> str:
    indent = " " * spaces
    return "".join(f"{indent}{line}\n" for line in lines)


def _derive_default_image_env_var(component_id: str) -> str:
    """Convention env-var name when the caller doesn't pass `--component-image-env-var`.

    Example: ``backend-api`` → ``APP_RUNTIME_BACKEND_API_IMAGE``.
    """
    return f"APP_RUNTIME_{component_id.upper().replace('-', '_')}_IMAGE"


def _resolve_image_and_env_var(
    component: ResolvedComponent,
    component_image: dict[str, str],
    component_image_env_var: dict[str, str],
    fallback_warnings: list[str],
) -> tuple[str, str]:
    """Look up image + env-var with sensible fallbacks for descriptor components missing
    explicit per-component CLI mappings (Codex P1 / Codex review on ``bootstrap.sh:95``).

    When no `--component-image <id>=<image>` mapping is supplied for a descriptor component,
    fall back to an empty image string (consumer overrides at deploy time via the env var
    below). When no `--component-image-env-var <id>=<name>` mapping is supplied, derive the
    env-var name from the component id via the project convention. ``fallback_warnings``
    accumulates the (component_id, app_id) of every component that took a fallback so the
    caller can emit a single deterministic stderr warning at the end.
    """
    image = component_image.get(component.component_id)
    env_var = component_image_env_var.get(component.component_id)
    used_fallback = False
    if image is None:
        image = ""
        used_fallback = True
    if env_var is None:
        env_var = _derive_default_image_env_var(component.component_id)
        used_fallback = True
    if used_fallback:
        fallback_warnings.append(
            f"{component.component_id} (app {component.app_id})"
        )
    return image, env_var


def render_delivery_workloads_block(
    components: Iterable[ResolvedComponent],
    component_image: dict[str, str],
    component_image_env_var: dict[str, str] | None = None,
    fallback_warnings: list[str] | None = None,
) -> str:
    """Render the indented `deliveryTopology.workloads` list body from descriptor records.

    Accepts the env-var map + a shared ``fallback_warnings`` list so the delivery and
    gitops blocks share the same fallback bookkeeping; both arguments are optional for
    callers that only need the image binding (kept for backward compatibility with
    earlier slice-3 unit tests on this helper).
    """
    env_var_map = component_image_env_var if component_image_env_var is not None else {}
    warnings_acc: list[str] = fallback_warnings if fallback_warnings is not None else []
    lines: list[str] = []
    for component in components:
        image, _env_var = _resolve_image_and_env_var(
            component, component_image, env_var_map, warnings_acc
        )
        service_port = component.service.get("port", "")
        service_name = component.service.get("serviceName") or component.component_id
        lines.extend(
            [
                f"- workloadId: {component.component_id}",
                f"  appId: {component.app_id}",
                f"  kind: {component.kind}",
                f"  namespace: {WORKLOAD_NAMESPACE}",
                f"  serviceName: {service_name}",
                f"  servicePort: {service_port}",
                f"  image: {image}",
            ]
        )
    return _indent_block(lines, spaces=4)


def render_gitops_workloads_block(
    components: Iterable[ResolvedComponent],
    component_image: dict[str, str],
    component_image_env_var: dict[str, str],
    fallback_warnings: list[str] | None = None,
) -> str:
    """Render the indented `runtimeDeliveryContract.gitopsWorkloads` list body."""
    warnings_acc: list[str] = fallback_warnings if fallback_warnings is not None else []
    lines: list[str] = []
    for component in components:
        image, env_var = _resolve_image_and_env_var(
            component, component_image, component_image_env_var, warnings_acc
        )
        lines.extend(
            [
                f"- id: {component.component_id}",
                f"  appId: {component.app_id}",
                f"  deploymentManifest: {component.deployment_manifest}",
                f"  serviceManifest: {component.service_manifest}",
                f"  imageEnvVar: {env_var}",
                f"  defaultImage: {image}",
            ]
        )
    return _indent_block(lines, spaces=4)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean true/false value, got: {value}")


def _bool_literal(value: bool) -> str:
    return "true" if value else "false"


def _ensure_template_resolved(rendered: str, context_label: str) -> None:
    unresolved = sorted(set(re.findall(r"\$\{[A-Z0-9_]+\}", rendered)))
    if unresolved:
        raise ValueError(
            f"{context_label} contains unresolved template tokens: {', '.join(unresolved)}"
        )


def _render_template(template_path: Path, values: dict[str, str], *, context_label: str) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    rendered = template.safe_substitute(values)
    _ensure_template_resolved(rendered, context_label)
    return rendered.rstrip("\n") + "\n"


def validate_manifest_text(
    manifest_text: str,
    *,
    app_runtime_gitops_enabled: bool,
    observability_enabled: bool,
) -> list[str]:
    errors: list[str] = []

    for marker in REQUIRED_MANIFEST_MARKERS:
        if marker not in manifest_text:
            errors.append(f"manifest key missing ({marker})")

    if app_runtime_gitops_enabled:
        for marker in (
            "gitopsEnabled: true",
            "mode: k8s-manifests",
            f"manifestsRoot: {APP_RUNTIME_MANIFEST_BASE}",
        ):
            if marker not in manifest_text:
                errors.append(f"runtime delivery marker missing ({marker})")
        # Generic descriptor-derived check: at least one gitopsWorkloads entry must reference a
        # deployment manifest under the apps base; the renderer derives the entry list from
        # apps/descriptor.yaml so the check no longer pins specific baseline manifest filenames.
        deployment_marker = f"deploymentManifest: {APP_RUNTIME_MANIFEST_BASE}/"
        if deployment_marker not in manifest_text:
            errors.append(
                "runtimeDeliveryContract.gitopsWorkloads must contain at least one entry "
                f"with deploymentManifest under {APP_RUNTIME_MANIFEST_BASE}/ when "
                "gitopsEnabled is true"
            )
    else:
        if "gitopsEnabled: false" not in manifest_text:
            errors.append("runtime delivery marker missing (gitopsEnabled: false)")

    expected_observability_marker = "enabled: true" if observability_enabled else "enabled: false"
    if expected_observability_marker not in manifest_text:
        errors.append(
            "observabilityRuntimeContract.enabled marker does not match expected OBSERVABILITY_ENABLED state"
        )

    if observability_enabled and "endpoint: http" not in manifest_text:
        errors.append(
            "observabilityRuntimeContract.otel.endpoint must contain an OTLP endpoint when observability is enabled"
        )

    return errors


def cmd_render(args: argparse.Namespace) -> int:
    context = CatalogRenderContext.from_args(args)

    descriptor, descriptor_errors = _load_descriptor(context.app_descriptor_path)
    if descriptor is None:
        raise ValueError(
            "app catalog manifest cannot be rendered: descriptor failed to load — "
            + "; ".join(descriptor_errors)
        )
    if descriptor_errors:
        raise ValueError(
            "app catalog manifest cannot be rendered: descriptor invalid — "
            + "; ".join(descriptor_errors)
        )

    fallback_warnings: list[str] = []
    delivery_workloads_block = render_delivery_workloads_block(
        descriptor.components,
        context.component_image,
        context.component_image_env_var,
        fallback_warnings,
    )
    # Render the gitops block with the SAME shared accumulator. The two helpers visit
    # each component once apiece, so a missing mapping appears twice in the raw list;
    # de-duplicate before warning so the operator sees one entry per affected component.
    gitops_workloads_block = render_gitops_workloads_block(
        descriptor.components,
        context.component_image,
        context.component_image_env_var,
        fallback_warnings,
    ).rstrip("\n")  # drop trailing newline so template's own newline is preserved

    if fallback_warnings:
        unique_components = sorted(set(fallback_warnings))
        print(
            "warning: app catalog renderer fell back to default image and/or env-var "
            "for descriptor components without an explicit `--component-image[-env-var]` "
            "mapping (image: empty, env-var: APP_RUNTIME_<COMPONENT_ID>_IMAGE convention). "
            "Add the missing flags to scripts/bin/platform/apps/bootstrap.sh — affected "
            "components: " + ", ".join(unique_components),
            file=sys.stderr,
        )

    # Build env-var → image substitutions generically from the descriptor + component
    # maps so renderer logic stays free of any baseline component-id knowledge.
    # Templates may reference ${<ENV_VAR>} placeholders for any descriptor-declared
    # component; the substitution map is built without naming specific IDs here.
    env_var_substitutions: dict[str, str] = {}
    for component in descriptor.components:
        image = context.component_image.get(component.component_id)
        env_var = context.component_image_env_var.get(component.component_id)
        if image is None or env_var is None:
            continue  # template-substitution map only needs explicitly-mapped pairs
        env_var_substitutions[env_var] = image

    manifest_values = {
        "PYTHON_RUNTIME_BASE_IMAGE_VERSION": context.python_runtime_base_image_version,
        "NODE_RUNTIME_BASE_IMAGE_VERSION": context.node_runtime_base_image_version,
        "NGINX_RUNTIME_BASE_IMAGE_VERSION": context.nginx_runtime_base_image_version,
        "FASTAPI_VERSION": context.fastapi_version,
        "PYDANTIC_VERSION": context.pydantic_version,
        "VUE_VERSION": context.vue_version,
        "VUE_ROUTER_VERSION": context.vue_router_version,
        "PINIA_VERSION": context.pinia_version,
        "APP_RUNTIME_GITOPS_ENABLED": _bool_literal(context.app_runtime_gitops_enabled),
        "DELIVERY_WORKLOADS_BLOCK": delivery_workloads_block.rstrip("\n"),
        "GITOPS_WORKLOADS_BLOCK": gitops_workloads_block,
        "OBSERVABILITY_ENABLED": _bool_literal(context.observability_enabled),
        "OTEL_EXPORTER_OTLP_ENDPOINT": context.otel_exporter_otlp_endpoint,
        "OTEL_PROTOCOL": context.otel_protocol,
        "OTEL_TRACES_ENABLED": _bool_literal(context.otel_traces_enabled),
        "OTEL_METRICS_ENABLED": _bool_literal(context.otel_metrics_enabled),
        "OTEL_LOGS_ENABLED": _bool_literal(context.otel_logs_enabled),
        "FARO_ENABLED": _bool_literal(context.faro_enabled),
        "FARO_COLLECT_PATH": context.faro_collect_path,
        **env_var_substitutions,
    }
    manifest_text = _render_template(
        Path(args.manifest_template),
        manifest_values,
        context_label="manifest template",
    )
    manifest_errors = validate_manifest_text(
        manifest_text,
        app_runtime_gitops_enabled=context.app_runtime_gitops_enabled,
        observability_enabled=context.observability_enabled,
    )
    if manifest_errors:
        raise ValueError("rendered app catalog manifest failed validation: " + "; ".join(manifest_errors))

    versions_values = {
        "PYTHON_RUNTIME_BASE_IMAGE_VERSION": context.python_runtime_base_image_version,
        "NODE_RUNTIME_BASE_IMAGE_VERSION": context.node_runtime_base_image_version,
        "NGINX_RUNTIME_BASE_IMAGE_VERSION": context.nginx_runtime_base_image_version,
        "FASTAPI_VERSION": context.fastapi_version,
        "PYDANTIC_VERSION": context.pydantic_version,
        "VUE_VERSION": context.vue_version,
        "VUE_ROUTER_VERSION": context.vue_router_version,
        "PINIA_VERSION": context.pinia_version,
        "APP_RUNTIME_GITOPS_ENABLED": _bool_literal(context.app_runtime_gitops_enabled),
        **env_var_substitutions,
    }
    versions_text = _render_template(
        Path(args.versions_template),
        versions_values,
        context_label="versions lock template",
    )

    manifest_output = Path(args.manifest_output)
    versions_output = Path(args.versions_output)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    versions_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(manifest_text, encoding="utf-8")
    versions_output.write_text(versions_text, encoding="utf-8")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    manifest_text = Path(args.manifest_path).read_text(encoding="utf-8")
    errors = validate_manifest_text(
        manifest_text,
        app_runtime_gitops_enabled=args.app_runtime_gitops_enabled,
        observability_enabled=args.observability_enabled,
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--manifest-template", required=True)
    render_parser.add_argument("--versions-template", required=True)
    render_parser.add_argument("--manifest-output", required=True)
    render_parser.add_argument("--versions-output", required=True)
    render_parser.add_argument("--python-runtime-base-image-version", required=True)
    render_parser.add_argument("--node-runtime-base-image-version", required=True)
    render_parser.add_argument("--nginx-runtime-base-image-version", required=True)
    render_parser.add_argument("--fastapi-version", required=True)
    render_parser.add_argument("--pydantic-version", required=True)
    render_parser.add_argument("--vue-version", required=True)
    render_parser.add_argument("--vue-router-version", required=True)
    render_parser.add_argument("--pinia-version", required=True)
    render_parser.add_argument("--app-runtime-gitops-enabled", type=_parse_bool, required=True)
    render_parser.add_argument(
        "--app-descriptor-path",
        required=True,
        help="Path to apps/descriptor.yaml (drives deliveryTopology.workloads + gitopsWorkloads)",
    )
    render_parser.add_argument(
        "--component-image",
        action="append",
        default=[],
        metavar="ID=IMAGE",
        help="Per-component image binding: <component-id>=<image>; repeatable",
    )
    render_parser.add_argument(
        "--component-image-env-var",
        action="append",
        default=[],
        metavar="ID=ENV_VAR",
        help="Per-component image env-var name: <component-id>=<env-var>; repeatable",
    )
    render_parser.add_argument("--observability-enabled", type=_parse_bool, required=True)
    render_parser.add_argument("--otel-exporter-otlp-endpoint", required=True)
    render_parser.add_argument("--otel-protocol", required=True)
    render_parser.add_argument("--otel-traces-enabled", type=_parse_bool, required=True)
    render_parser.add_argument("--otel-metrics-enabled", type=_parse_bool, required=True)
    render_parser.add_argument("--otel-logs-enabled", type=_parse_bool, required=True)
    render_parser.add_argument("--faro-enabled", type=_parse_bool, required=True)
    render_parser.add_argument("--faro-collect-path", required=True)
    render_parser.set_defaults(func=cmd_render)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--manifest-path", required=True)
    validate_parser.add_argument("--app-runtime-gitops-enabled", type=_parse_bool, required=True)
    validate_parser.add_argument("--observability-enabled", type=_parse_bool, required=True)
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
