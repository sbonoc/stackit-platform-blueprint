"""Unit tests for template_smoke_assertions helpers.

Covers the dynamic workload derivation path introduced in issue #208:
  - _extract_kustomization_resources() stdlib parser
  - validate_app_runtime_conformance() reads app_manifest_paths from kustomization.yaml
    at runtime rather than from a hardcoded list.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.template_smoke_assertions import (  # noqa: E402
    _extract_kustomization_resources,
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
