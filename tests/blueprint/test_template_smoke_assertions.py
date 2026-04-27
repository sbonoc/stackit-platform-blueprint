"""Unit tests for template_smoke_assertions helpers.

Covers the dynamic workload derivation path introduced in issue #208:
  - _extract_kustomization_resources() — yaml.safe_load-based parser
  - assert_make_target_presence() — regex-based make target checker
  - validate_app_runtime_conformance() reads app_manifest_paths from kustomization.yaml
    at runtime rather than from a hardcoded list.

Also covers the descriptor-kustomization cross-check introduced in issue #217:
  - _assert_descriptor_kustomization_agreement() — checks descriptor manifest filenames
    against app_manifest_names set (FR-001/AC-001/AC-002).
  - Template consistency: descriptor.yaml.tmpl and kustomization.yaml must agree (FR-002/AC-003).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.template_smoke_assertions import (  # noqa: E402
    _assert_descriptor_kustomization_agreement,
    _extract_kustomization_resources,
    assert_make_target_presence,
)


class ExtractKustomizationResourcesTests(unittest.TestCase):
    def test_parses_standard_resources_section(self) -> None:
        text = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources:\n  - foo-deployment.yaml\n  - foo-service.yaml\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, ["foo-deployment.yaml", "foo-service.yaml"])

    def test_parses_consumer_named_resources(self) -> None:
        text = "resources:\n  - marketplace-api-deployment.yaml\n  - marketplace-api-service.yaml\n  - marketplace-web-deployment.yaml\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, [
            "marketplace-api-deployment.yaml",
            "marketplace-api-service.yaml",
            "marketplace-web-deployment.yaml",
        ])

    def test_empty_resources_section_returns_empty_list(self) -> None:
        text = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources: []\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, [])

    def test_no_resources_section_returns_empty_list(self) -> None:
        text = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, [])

    def test_stops_at_next_top_level_key(self) -> None:
        text = "resources:\n  - alpha.yaml\n  - beta.yaml\npatches:\n  - patch.yaml\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, ["alpha.yaml", "beta.yaml"])

    def test_skips_comment_lines(self) -> None:
        text = "resources:\n  # this is a comment\n  - valid.yaml\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, ["valid.yaml"])

    def test_strips_inline_comments_from_resource_entries(self) -> None:
        text = "resources:\n  - marketplace-api-deployment.yaml # app workload\n  - marketplace-api-service.yaml # service\n"
        result = _extract_kustomization_resources(text)
        self.assertEqual(result, ["marketplace-api-deployment.yaml", "marketplace-api-service.yaml"])

    def test_blueprint_template_kustomization_is_parseable(self) -> None:
        kust_path = REPO_ROOT / "scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml"
        text = kust_path.read_text(encoding="utf-8")
        result = _extract_kustomization_resources(text)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0, "template kustomization must declare at least one resource")
        for entry in result:
            self.assertTrue(entry.endswith(".yaml"), f"expected .yaml extension, got: {entry!r}")


class AssertMakeTargetPresenceTests(unittest.TestCase):
    """Unit tests for assert_make_target_presence — exercises the re import."""

    def test_present_target_passes_when_expected_present(self) -> None:
        makefile = "infra-smoke:\n\t@scripts/bin/infra/smoke.sh\n"
        assert_make_target_presence(makefile, "infra-smoke", True, "test")

    def test_absent_target_passes_when_expected_absent(self) -> None:
        makefile = "infra-smoke:\n\t@scripts/bin/infra/smoke.sh\n"
        assert_make_target_presence(makefile, "infra-deploy", False, "test")

    def test_present_target_raises_when_expected_absent(self) -> None:
        makefile = "infra-smoke:\n\t@scripts/bin/infra/smoke.sh\n"
        with self.assertRaises(AssertionError):
            assert_make_target_presence(makefile, "infra-smoke", False, "test")

    def test_absent_target_raises_when_expected_present(self) -> None:
        makefile = "infra-smoke:\n\t@scripts/bin/infra/smoke.sh\n"
        with self.assertRaises(AssertionError):
            assert_make_target_presence(makefile, "infra-deploy", True, "test")

    def test_partial_name_does_not_match(self) -> None:
        makefile = "infra-smoke-extended:\n\t@echo ok\n"
        with self.assertRaises(AssertionError):
            assert_make_target_presence(makefile, "infra-smoke", True, "test")


class DynamicWorkloadDerivationRegressionTests(unittest.TestCase):
    """Regression guards that verify no hardcoded seed names appear in production code."""

    def test_no_hardcoded_app_manifest_names_in_template_smoke_assertions(self) -> None:
        """_extract_kustomization_resources must be used; hardcoded seed names must not appear in validate_app_runtime_conformance."""
        source = (REPO_ROOT / "scripts/lib/blueprint/template_smoke_assertions.py").read_text(encoding="utf-8")
        hardcoded_seed_names = [
            "backend-api-deployment.yaml",
            "backend-api-service.yaml",
            "touchpoints-web-deployment.yaml",
            "touchpoints-web-service.yaml",
        ]
        found = [name for name in hardcoded_seed_names if name in source]
        self.assertEqual(
            found,
            [],
            msg=(
                "template_smoke_assertions.py must not hardcode blueprint seed workload manifest names. "
                f"Found: {found}. Use _extract_kustomization_resources() to derive app_manifest_paths "
                "from infra/gitops/platform/base/apps/kustomization.yaml at runtime."
            ),
        )


class DescriptorKustomizationCrossCheckTests(unittest.TestCase):
    """FR-001/AC-001/AC-002: descriptor-kustomization cross-check assertion."""

    _DESCRIPTOR_PATH = Path("/fake/repo/apps/descriptor.yaml")
    _KUSTOMIZATION_PATH = Path("/fake/repo/infra/gitops/platform/base/apps/kustomization.yaml")

    def _make_descriptor(self, apps: list[dict]) -> dict:
        """Build a minimal descriptor dict."""
        return {"schemaVersion": "v1", "apps": apps}

    def _make_app(self, app_id: str, components: list[dict]) -> dict:
        return {"id": app_id, "owner": {"team": "platform"}, "components": components}

    def _make_component_explicit(
        self,
        component_id: str,
        kind: str,
        deployment: str,
        service: str,
    ) -> dict:
        return {
            "id": component_id,
            "kind": kind,
            "manifests": {
                "deployment": f"infra/gitops/platform/base/apps/{deployment}",
                "service": f"infra/gitops/platform/base/apps/{service}",
            },
        }

    def _make_component_no_manifests(self, component_id: str, kind: str) -> dict:
        return {"id": component_id, "kind": kind}

    def test_consistent_descriptor_kustomization_passes(self) -> None:
        """AC-002: consistent descriptor+kustomization -> no AssertionError."""
        descriptor = self._make_descriptor([
            self._make_app("backend-api", [
                self._make_component_explicit(
                    "backend-api", "Deployment",
                    "backend-api-deployment.yaml", "backend-api-service.yaml",
                )
            ]),
            self._make_app("touchpoints-web", [
                self._make_component_explicit(
                    "touchpoints-web", "Deployment",
                    "touchpoints-web-deployment.yaml", "touchpoints-web-service.yaml",
                )
            ]),
        ])
        app_manifest_names = [
            "backend-api-deployment.yaml",
            "backend-api-service.yaml",
            "touchpoints-web-deployment.yaml",
            "touchpoints-web-service.yaml",
        ]
        # Should not raise
        _assert_descriptor_kustomization_agreement(
            app_manifest_names=app_manifest_names,
            descriptor=descriptor,
            descriptor_path=self._DESCRIPTOR_PATH,
            kustomization_path=self._KUSTOMIZATION_PATH,
        )

    def test_missing_filename_raises_assertion_error(self) -> None:
        """AC-001: descriptor referencing absent filename raises AssertionError naming the missing file."""
        descriptor = self._make_descriptor([
            self._make_app("foo", [
                self._make_component_explicit(
                    "foo", "Deployment",
                    "foo-deployment.yaml", "foo-service.yaml",
                )
            ]),
        ])
        # kustomization only has the deployment, not the service
        app_manifest_names = ["foo-deployment.yaml"]
        with self.assertRaises(AssertionError) as ctx:
            _assert_descriptor_kustomization_agreement(
                app_manifest_names=app_manifest_names,
                descriptor=descriptor,
                descriptor_path=self._DESCRIPTOR_PATH,
                kustomization_path=self._KUSTOMIZATION_PATH,
            )
        self.assertIn("foo-service.yaml", str(ctx.exception))

    def test_convention_default_path_handled(self) -> None:
        """Component without explicit manifests: block uses {id}-{kind}.yaml convention."""
        # No manifests block -> convention default: backend-api-deployment.yaml, backend-api-service.yaml
        descriptor = self._make_descriptor([
            self._make_app("backend-api", [
                self._make_component_no_manifests("backend-api", "Deployment")
            ]),
        ])
        app_manifest_names = [
            "backend-api-deployment.yaml",
            "backend-api-service.yaml",
        ]
        # Should not raise
        _assert_descriptor_kustomization_agreement(
            app_manifest_names=app_manifest_names,
            descriptor=descriptor,
            descriptor_path=self._DESCRIPTOR_PATH,
            kustomization_path=self._KUSTOMIZATION_PATH,
        )

    def test_convention_default_missing_raises(self) -> None:
        """Convention-default derived filename absent from kustomization raises AssertionError."""
        descriptor = self._make_descriptor([
            self._make_app("backend-api", [
                self._make_component_no_manifests("backend-api", "Deployment")
            ]),
        ])
        # Only the deployment present, service missing
        app_manifest_names = ["backend-api-deployment.yaml"]
        with self.assertRaises(AssertionError) as ctx:
            _assert_descriptor_kustomization_agreement(
                app_manifest_names=app_manifest_names,
                descriptor=descriptor,
                descriptor_path=self._DESCRIPTOR_PATH,
                kustomization_path=self._KUSTOMIZATION_PATH,
            )
        self.assertIn("backend-api-service.yaml", str(ctx.exception))

    def test_error_message_names_missing_file_and_both_paths(self) -> None:
        """NFR-OBS-001: error message names filename, descriptor path, and kustomization path."""
        descriptor = self._make_descriptor([
            self._make_app("foo", [
                self._make_component_explicit(
                    "foo", "Deployment",
                    "foo-deployment.yaml", "foo-service.yaml",
                )
            ]),
        ])
        app_manifest_names = ["foo-deployment.yaml"]  # foo-service.yaml missing
        with self.assertRaises(AssertionError) as ctx:
            _assert_descriptor_kustomization_agreement(
                app_manifest_names=app_manifest_names,
                descriptor=descriptor,
                descriptor_path=self._DESCRIPTOR_PATH,
                kustomization_path=self._KUSTOMIZATION_PATH,
            )
        message = str(ctx.exception)
        self.assertIn("foo-service.yaml", message)
        self.assertIn(str(self._DESCRIPTOR_PATH), message)
        self.assertIn(str(self._KUSTOMIZATION_PATH), message)

    def test_four_filenames_kustomization_missing_one_raises(self) -> None:
        """T-104: descriptor with 4 filenames, kustomization listing only 1 -> AssertionError."""
        descriptor = self._make_descriptor([
            self._make_app("backend-api", [
                self._make_component_explicit(
                    "backend-api", "Deployment",
                    "backend-api-deployment.yaml", "backend-api-service.yaml",
                )
            ]),
            self._make_app("touchpoints-web", [
                self._make_component_explicit(
                    "touchpoints-web", "Deployment",
                    "touchpoints-web-deployment.yaml", "touchpoints-web-service.yaml",
                )
            ]),
        ])
        # kustomization only lists one of the four filenames
        app_manifest_names = ["backend-api-deployment.yaml"]
        with self.assertRaises(AssertionError):
            _assert_descriptor_kustomization_agreement(
                app_manifest_names=app_manifest_names,
                descriptor=descriptor,
                descriptor_path=self._DESCRIPTOR_PATH,
                kustomization_path=self._KUSTOMIZATION_PATH,
            )


class TemplateConsistencyTests(unittest.TestCase):
    """FR-002/AC-003: descriptor.yaml.tmpl and kustomization.yaml template must agree."""

    def test_template_descriptor_and_kustomization_have_same_filenames(self) -> None:
        """The two seed templates must reference the same set of manifest filenames."""
        descriptor_tmpl_path = (
            REPO_ROOT
            / "scripts/templates/consumer/init/apps/descriptor.yaml.tmpl"
        )
        kust_path = (
            REPO_ROOT
            / "scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml"
        )

        # Extract filenames from descriptor template
        descriptor = yaml.safe_load(descriptor_tmpl_path.read_text(encoding="utf-8")) or {}
        descriptor_filenames: set[str] = set()
        for app in descriptor.get("apps") or []:
            for component in app.get("components") or []:
                component_id = component.get("id", "")
                manifests = component.get("manifests") or {}
                # Explicit deployment
                dep_val = manifests.get("deployment")
                if dep_val:
                    descriptor_filenames.add(Path(dep_val).name)
                else:
                    descriptor_filenames.add(f"{component_id}-deployment.yaml")
                # Explicit service
                svc_val = manifests.get("service")
                if svc_val:
                    descriptor_filenames.add(Path(svc_val).name)
                else:
                    descriptor_filenames.add(f"{component_id}-service.yaml")

        # Extract filenames from kustomization template
        kust_resources = set(_extract_kustomization_resources(kust_path.read_text(encoding="utf-8")))

        self.assertEqual(
            descriptor_filenames,
            kust_resources,
            msg=(
                "descriptor.yaml.tmpl and kustomization.yaml template must reference the same "
                f"set of manifest filenames.\n"
                f"  Descriptor-only: {descriptor_filenames - kust_resources}\n"
                f"  Kustomization-only: {kust_resources - descriptor_filenames}"
            ),
        )
