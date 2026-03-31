from __future__ import annotations

import unittest

from tests.blueprint.contract_refactor_cases import RefactorContractsTests


def _all_case_names() -> set[str]:
    return {name for name in dir(RefactorContractsTests) if name.startswith("test_")}


def _pick_cases(unassigned: set[str], keywords: tuple[str, ...], explicit: tuple[str, ...] = ()) -> list[str]:
    picked = {name for name in unassigned if any(keyword in name for keyword in keywords)}
    for name in explicit:
        if name in unassigned:
            picked.add(name)
    return sorted(picked)


_unassigned = _all_case_names()

STACKIT_RUNTIME_CASES = _pick_cases(
    _unassigned,
    (
        "stackit",
        "rabbitmq",
        "public_endpoints",
        "identity_aware_proxy",
        "keycloak",
        "runtime_credentials",
        "workflows_scaffolding",
        "langfuse_postgres_neo4j",
        "iap_contract",
        "module_destroy_scripts",
        "module_lifecycle_runner",
        "argocd",
        "platform_base_namespaces",
    ),
    explicit=("test_bootstrap_preserves_disabled_optional_scaffolding",),
)
_unassigned -= set(STACKIT_RUNTIME_CASES)

BOOTSTRAP_SURFACE_CASES = _pick_cases(
    _unassigned,
    (
        "bootstrap",
        "docs",
        "platform_docs",
        "consumer_",
        "endpoint_exposure",
        "protected_api_routes",
        "gateway_module",
        "apps_bootstrap_keeps_only_canonical_app_dirs",
        "apps_version_baseline",
        "crossplane_scaffold",
        "ci_workflows_and_docs_exist",
    ),
)
_unassigned -= set(BOOTSTRAP_SURFACE_CASES)

QUALITY_TOOLING_CASES = _pick_cases(
    _unassigned,
    (
        "quality",
        "validator",
        "validate_command",
        "make_contract",
        "makefile_template",
        "shell_contract_helpers",
        "pre_commit",
        "metrics",
        "touchpoints_test_lanes",
        "dry_run_toggle",
        "contract_surface_assets_targets_and_namespaces",
        "contract_template_bootstrap_metadata",
        "docs_generator_uses_schema_driven_contract_loader",
    ),
)
_unassigned -= set(QUALITY_TOOLING_CASES)

INIT_GOVERNANCE_CASES = sorted(_unassigned)

_partition_union = (
    set(STACKIT_RUNTIME_CASES)
    | set(BOOTSTRAP_SURFACE_CASES)
    | set(QUALITY_TOOLING_CASES)
    | set(INIT_GOVERNANCE_CASES)
)
if _partition_union != _all_case_names():
    missing = sorted(_all_case_names() - _partition_union)
    raise RuntimeError(f"incomplete contract test partition: {missing}")


def build_split_case(class_name: str, method_names: list[str], module_name: str) -> type[unittest.TestCase]:
    attrs: dict[str, object] = {
        "__module__": module_name,
        "_contract_lines": RefactorContractsTests._contract_lines,
    }
    for name in method_names:
        attrs[name] = getattr(RefactorContractsTests, name)
    return type(class_name, (unittest.TestCase,), attrs)
