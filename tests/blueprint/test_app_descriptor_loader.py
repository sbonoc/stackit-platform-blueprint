"""Slice 2 — descriptor loader, safe path resolver, app_runtime_gitops integration.

Covers FR-003 (schema), FR-004 (explicit + convention defaults), FR-005 (multi-component),
FR-006 (existence + kustomization membership), NFR-SEC-001 (yaml.safe_load + safe paths),
NFR-OBS-001 (deterministic messages), AC-002, AC-003, AC-004.
"""
from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path


def _kustomization_resources_for_test(path: Path) -> set[str]:
    """Mirror of validate_contract._kustomization_resources for unit-test isolation."""
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


def _write_descriptor(repo_root: Path, body: str) -> Path:
    descriptor_path = repo_root / "apps" / "descriptor.yaml"
    descriptor_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor_path.write_text(textwrap.dedent(body), encoding="utf-8")
    return descriptor_path


def _write_apps_manifest(repo_root: Path, filename: str, content: str = "kind: Deployment\nmetadata:\n  name: x\n") -> Path:
    apps_dir = repo_root / "infra" / "gitops" / "platform" / "base" / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    manifest = apps_dir / filename
    manifest.write_text(content, encoding="utf-8")
    return manifest


def _write_apps_kustomization(repo_root: Path, resources: list[str]) -> Path:
    apps_dir = repo_root / "infra" / "gitops" / "platform" / "base" / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    body = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources:\n" + "".join(
        f"  - {r}\n" for r in resources
    )
    path = apps_dir / "kustomization.yaml"
    path.write_text(body, encoding="utf-8")
    return path


_VALID_BASELINE = """\
schemaVersion: v1
apps:
  - id: backend-api
    owner:
      team: platform
    components:
      - id: backend-api
        kind: deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/backend-api-deployment.yaml
          service: infra/gitops/platform/base/apps/backend-api-service.yaml
        service:
          port: 8080
        health:
          readiness: /
"""


class AppDescriptorLoaderSchemaTests(unittest.TestCase):
    """FR-003: schema validation."""

    def test_loads_baseline_descriptor_with_no_errors(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            descriptor_path = _write_descriptor(repo_root, _VALID_BASELINE)
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertEqual(errors, [])
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor.schema_version, "v1")
        self.assertEqual(len(descriptor.components), 1)
        self.assertEqual(descriptor.components[0].app_id, "backend-api")
        self.assertEqual(descriptor.components[0].component_id, "backend-api")

    def test_invalid_yaml_reports_parse_error(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(Path(tmpdir), "schemaVersion: v1\napps: [\n  invalid")
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertIsNone(descriptor)
        self.assertEqual(len(errors), 1)
        self.assertIn("failed to parse YAML", errors[0])

    def test_missing_schema_version_reports_error(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("schemaVersion" in e for e in errors),
            f"expected schemaVersion error; got: {errors}",
        )

    def test_missing_apps_reports_error(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(Path(tmpdir), "schemaVersion: v1\n")
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertIsNone(descriptor)
        self.assertTrue(
            any("apps" in e for e in errors),
            f"expected apps error; got: {errors}",
        )

    def test_app_owner_team_required(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("owner.team" in e and "backend-api" in e for e in errors),
            f"expected owner.team error naming app; got: {errors}",
        )

    def test_component_kind_required(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("kind" in e and "backend-api" in e for e in errors),
            f"expected kind error naming component; got: {errors}",
        )


class AppDescriptorUnsafeIdAndPathTests(unittest.TestCase):
    """AC-002, NFR-SEC-001: reject unsafe app/component IDs and manifest paths."""

    def test_app_id_with_parent_traversal_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: ../bad
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("../bad" in e or "'../bad'" in e for e in errors),
            f"expected unsafe app id error; got: {errors}",
        )

    def test_app_id_with_slash_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: nested/app
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("nested/app" in e for e in errors),
            f"expected unsafe app id error; got: {errors}",
        )

    def test_component_id_with_unsafe_chars_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: api;rm
                        kind: deployment
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("api;rm" in e for e in errors),
            f"expected unsafe component id error; got: {errors}",
        )

    def test_absolute_manifest_path_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                        manifests:
                          deployment: /etc/passwd
                          service: infra/gitops/platform/base/apps/backend-api-service.yaml
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("/etc/passwd" in e and "deployment" in e for e in errors),
            f"expected absolute path rejection naming kind+path; got: {errors}",
        )

    def test_manifest_path_with_parent_traversal_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                        manifests:
                          deployment: infra/gitops/platform/base/apps/../../../etc/passwd
                          service: infra/gitops/platform/base/apps/backend-api-service.yaml
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any(".." in e and "deployment" in e for e in errors),
            f"expected parent-traversal rejection; got: {errors}",
        )

    def test_manifest_path_with_shell_metas_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                        manifests:
                          deployment: "infra/gitops/platform/base/apps/$(rm -rf /).yaml"
                          service: infra/gitops/platform/base/apps/backend-api-service.yaml
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any("unsafe characters" in e and "deployment" in e for e in errors),
            f"expected shell-meta rejection; got: {errors}",
        )

    def test_manifest_path_outside_apps_base_rejected(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                        manifests:
                          deployment: infra/secrets/leaked-deployment.yaml
                          service: infra/gitops/platform/base/apps/backend-api-service.yaml
                """,
            )
            _, errors = load_app_descriptor(descriptor_path)

        self.assertTrue(
            any(
                "infra/gitops/platform/base/apps" in e and "infra/secrets/leaked" in e
                for e in errors
            ),
            f"expected outside-apps-base rejection naming the base path; got: {errors}",
        )


class AppDescriptorConventionAndMultiComponentTests(unittest.TestCase):
    """FR-004 (explicit + convention defaults), FR-005 (multi-component)."""

    def test_convention_defaults_used_when_manifests_omitted(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertEqual(errors, [])
        self.assertIsNotNone(descriptor)
        component = descriptor.components[0]
        self.assertEqual(
            component.deployment_manifest,
            "infra/gitops/platform/base/apps/backend-api-deployment.yaml",
        )
        self.assertEqual(
            component.service_manifest,
            "infra/gitops/platform/base/apps/backend-api-service.yaml",
        )

    def test_explicit_manifest_paths_take_precedence_over_convention(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                        manifests:
                          deployment: infra/gitops/platform/base/apps/custom-deploy.yaml
                          service: infra/gitops/platform/base/apps/custom-svc.yaml
                """,
            )
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertEqual(errors, [])
        component = descriptor.components[0]
        self.assertEqual(
            component.deployment_manifest,
            "infra/gitops/platform/base/apps/custom-deploy.yaml",
        )
        self.assertEqual(
            component.service_manifest,
            "infra/gitops/platform/base/apps/custom-svc.yaml",
        )

    def test_app_with_multiple_components_loads_each(self) -> None:
        from scripts.lib.blueprint.app_descriptor import load_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(
                Path(tmpdir),
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                      - id: backend-worker
                        kind: deployment
                """,
            )
            descriptor, errors = load_app_descriptor(descriptor_path)

        self.assertEqual(errors, [])
        component_ids = [c.component_id for c in descriptor.components]
        self.assertEqual(component_ids, ["backend-api", "backend-worker"])


class AppDescriptorPathExistenceAndKustomizationTests(unittest.TestCase):
    """FR-006, AC-003, AC-004, NFR-OBS-001."""

    def test_missing_resolved_deployment_manifest_reports_named_error(self) -> None:
        """AC-003 + NFR-OBS-001: error names app, component, kind, and resolved path."""
        from scripts.lib.blueprint.app_descriptor import validate_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_descriptor(
                repo_root,
                """\
                schemaVersion: v1
                apps:
                  - id: marketplace-api
                    owner:
                      team: platform
                    components:
                      - id: marketplace-api
                        kind: deployment
                """,
            )
            # Provide kustomization but NOT the deployment manifest file
            _write_apps_manifest(repo_root, "marketplace-api-service.yaml")
            _write_apps_kustomization(
                repo_root,
                ["marketplace-api-deployment.yaml", "marketplace-api-service.yaml"],
            )
            errors = validate_app_descriptor(repo_root, _kustomization_resources_for_test)

        self.assertTrue(
            any(
                "marketplace-api" in e
                and "deployment" in e
                and "marketplace-api-deployment.yaml" in e
                for e in errors
            ),
            f"expected missing-deployment error naming app+component+path; got: {errors}",
        )

    def test_missing_kustomization_membership_reports_named_error(self) -> None:
        """AC-004 + NFR-OBS-001: error names component, manifest filename, kustomization path."""
        from scripts.lib.blueprint.app_descriptor import validate_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_descriptor(
                repo_root,
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            # Manifests exist but kustomization is missing the deployment entry
            _write_apps_manifest(repo_root, "backend-api-deployment.yaml")
            _write_apps_manifest(repo_root, "backend-api-service.yaml")
            _write_apps_kustomization(
                repo_root,
                ["backend-api-service.yaml"],  # deployment intentionally absent
            )
            errors = validate_app_descriptor(repo_root, _kustomization_resources_for_test)

        self.assertTrue(
            any(
                "backend-api" in e
                and "backend-api-deployment.yaml" in e
                and "kustomization" in e
                for e in errors
            ),
            f"expected kustomization-membership error; got: {errors}",
        )

    def test_valid_descriptor_with_all_manifests_returns_no_errors(self) -> None:
        from scripts.lib.blueprint.app_descriptor import validate_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_descriptor(repo_root, _VALID_BASELINE)
            _write_apps_manifest(repo_root, "backend-api-deployment.yaml")
            _write_apps_manifest(repo_root, "backend-api-service.yaml")
            _write_apps_kustomization(
                repo_root,
                ["backend-api-deployment.yaml", "backend-api-service.yaml"],
            )
            errors = validate_app_descriptor(repo_root, _kustomization_resources_for_test)

        self.assertEqual(errors, [])

    def test_validate_app_descriptor_silent_when_descriptor_absent(self) -> None:
        """S4 owns the missing-descriptor presence policy. S2's validator skips silently."""
        from scripts.lib.blueprint.app_descriptor import validate_app_descriptor

        with tempfile.TemporaryDirectory() as tmpdir:
            errors = validate_app_descriptor(Path(tmpdir), _kustomization_resources_for_test)

        self.assertEqual(errors, [])


class AppDescriptorAppRuntimeGitopsIntegrationTests(unittest.TestCase):
    """T-004: descriptor validation is wired into validate_app_runtime_gitops_contract."""

    def test_descriptor_errors_propagate_through_app_runtime_gitops_validator(self) -> None:
        """Construct a minimal repo_root with the optional contract DISABLED so the validator's
        existing checks fall through silently — descriptor validation must still run and produce
        errors when apps/descriptor.yaml is broken."""
        from scripts.lib.blueprint.contract_validators.app_runtime_gitops import (
            validate_app_runtime_gitops_contract,
        )
        from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers

        # Synthetic blueprint contract with the optional gitops contract DISABLED so the
        # heavy app_runtime_gitops_contract checks are skipped (returns early after section
        # validation). Descriptor validation must still execute.
        from types import SimpleNamespace

        contract = SimpleNamespace(
            raw={
                "spec": {
                    "toggles": {
                        "APP_RUNTIME_GITOPS_ENABLED": {"default": False},
                    },
                    "app_runtime_gitops_contract": {
                        "enabled_by_default": True,
                        "enable_flag": "APP_RUNTIME_GITOPS_ENABLED",
                        "required_paths_when_enabled": ["infra/gitops/platform/base/apps"],
                        "workload_kinds_required_when_enabled": ["Deployment"],
                        "docs_paths": [],
                        "app_catalog_manifest_path": "apps/catalog/manifest.yaml",
                        "smoke_guardrails": {
                            "app_namespace": "apps",
                            "workload_kinds": ["Deployment"],
                            "minimum_workloads_env": "APP_RUNTIME_GITOPS_ENABLED",
                            "minimum_workloads_default": False,
                            "diagnostics_reason": "empty-runtime-workloads",
                        },
                    },
                }
            }
        )

        def _passthrough_mapping(value, _path, _errors):
            return value if isinstance(value, dict) else {}

        def _passthrough_list_str(value, _path, _errors):
            return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []

        def _passthrough_str(value, _path, _errors):
            return value if isinstance(value, str) else ""

        def _passthrough_bool(value, _path, _errors):
            return value if isinstance(value, bool) else None

        def _passthrough_int(value, _path, _errors):
            return value if isinstance(value, int) else None

        helpers = ContractValidationHelpers(
            validate_required_files=lambda _r, _p: [],
            validate_required_paths=lambda _r, _p: [],
            mapping_or_error=_passthrough_mapping,
            list_of_str_or_error=_passthrough_list_str,
            string_or_error=_passthrough_str,
            bool_or_error=_passthrough_bool,
            int_or_error=_passthrough_int,
            is_optional_contract_enabled=lambda _spec, _section: False,  # disabled — skip heavy checks
            kustomization_resources=_kustomization_resources_for_test,
            manifest_kinds_under_path=lambda _p: set(),
            make_targets=lambda _p: set(),
            manifest_sync_policy_has_automated=lambda _c: False,
            validate_argocd_https_repo_url_contract=lambda _p: [],
            load_runtime_identity_contract=lambda _p: None,
            render_eso_external_secrets_manifest=lambda _c: "",
            runtime_dependency_edges=tuple(),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            # Broken descriptor: deployment file is missing, kustomization is missing entries
            _write_descriptor(
                repo_root,
                """\
                schemaVersion: v1
                apps:
                  - id: backend-api
                    owner:
                      team: platform
                    components:
                      - id: backend-api
                        kind: deployment
                """,
            )
            _write_apps_kustomization(repo_root, [])

            errors = validate_app_runtime_gitops_contract(repo_root, contract, helpers)

        self.assertTrue(
            any("backend-api-deployment.yaml" in e for e in errors),
            f"descriptor validation must propagate through app_runtime_gitops validator; got: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
