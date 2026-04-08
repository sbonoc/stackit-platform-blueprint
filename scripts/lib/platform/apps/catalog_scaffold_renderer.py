#!/usr/bin/env python3
"""Render and validate app catalog scaffold artifacts from typed inputs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
from string import Template


REQUIRED_MANIFEST_MARKERS: tuple[str, ...] = (
    "schemaVersion:",
    "appVersionContract:",
    "runtimePinnedVersions:",
    "frameworkPinnedVersions:",
    "deliveryTopology:",
    "runtimeDeliveryContract:",
    "observabilityRuntimeContract:",
)


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
    app_runtime_backend_image: str
    app_runtime_touchpoints_image: str
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
            app_runtime_backend_image=cls._require_non_empty(args.app_runtime_backend_image, "app_runtime_backend_image"),
            app_runtime_touchpoints_image=cls._require_non_empty(
                args.app_runtime_touchpoints_image,
                "app_runtime_touchpoints_image",
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

    runtime_markers = (
        (
            "gitopsEnabled: true",
            "mode: k8s-manifests",
            "manifestsRoot: infra/gitops/platform/base/apps",
            "backend-api-deployment.yaml",
            "touchpoints-web-deployment.yaml",
        )
        if app_runtime_gitops_enabled
        else ("gitopsEnabled: false",)
    )
    for marker in runtime_markers:
        if marker not in manifest_text:
            errors.append(f"runtime delivery marker missing ({marker})")

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
        "APP_RUNTIME_BACKEND_IMAGE": context.app_runtime_backend_image,
        "APP_RUNTIME_TOUCHPOINTS_IMAGE": context.app_runtime_touchpoints_image,
        "OBSERVABILITY_ENABLED": _bool_literal(context.observability_enabled),
        "OTEL_EXPORTER_OTLP_ENDPOINT": context.otel_exporter_otlp_endpoint,
        "OTEL_PROTOCOL": context.otel_protocol,
        "OTEL_TRACES_ENABLED": _bool_literal(context.otel_traces_enabled),
        "OTEL_METRICS_ENABLED": _bool_literal(context.otel_metrics_enabled),
        "OTEL_LOGS_ENABLED": _bool_literal(context.otel_logs_enabled),
        "FARO_ENABLED": _bool_literal(context.faro_enabled),
        "FARO_COLLECT_PATH": context.faro_collect_path,
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

    versions_text = _render_template(
        Path(args.versions_template),
        {
            "PYTHON_RUNTIME_BASE_IMAGE_VERSION": context.python_runtime_base_image_version,
            "NODE_RUNTIME_BASE_IMAGE_VERSION": context.node_runtime_base_image_version,
            "NGINX_RUNTIME_BASE_IMAGE_VERSION": context.nginx_runtime_base_image_version,
            "FASTAPI_VERSION": context.fastapi_version,
            "PYDANTIC_VERSION": context.pydantic_version,
            "VUE_VERSION": context.vue_version,
            "VUE_ROUTER_VERSION": context.vue_router_version,
            "PINIA_VERSION": context.pinia_version,
            "APP_RUNTIME_GITOPS_ENABLED": _bool_literal(context.app_runtime_gitops_enabled),
            "APP_RUNTIME_BACKEND_IMAGE": context.app_runtime_backend_image,
            "APP_RUNTIME_TOUCHPOINTS_IMAGE": context.app_runtime_touchpoints_image,
        },
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
    render_parser.add_argument("--app-runtime-backend-image", required=True)
    render_parser.add_argument("--app-runtime-touchpoints-image", required=True)
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
