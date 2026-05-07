"""Slice 5 — deprecation markers for the bridge guard and the catalog compatibility output.

Covers FR-008 (apps/catalog/manifest.yaml deprecation), FR-010 (bridge guard
deprecation), AC-009 (deprecation diagnostics with two-minor-release tracking).
"""
from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from scripts.lib.blueprint import upgrade_consumer
from tests._shared.helpers import REPO_ROOT


CATALOG_MANIFEST_TEMPLATE = REPO_ROOT / "scripts/templates/platform/apps/catalog/manifest.yaml.tmpl"
RENDERED_CATALOG_MANIFEST = REPO_ROOT / "apps/catalog/manifest.yaml"
BACKLOG_PATH = REPO_ROOT / "AGENTS.backlog.md"


class BridgeGuardDeprecationTests(unittest.TestCase):
    """FR-010 / AC-009: _is_consumer_owned_workload is marked deprecated with removal trigger."""

    def test_is_consumer_owned_workload_docstring_marks_deprecated(self) -> None:
        doc = inspect.getdoc(upgrade_consumer._is_consumer_owned_workload) or ""
        self.assertIn(
            "DEPRECATED",
            doc,
            "bridge guard must be marked DEPRECATED in its docstring",
        )

    def test_is_consumer_owned_workload_docstring_names_removal_trigger(self) -> None:
        doc = inspect.getdoc(upgrade_consumer._is_consumer_owned_workload) or ""
        for marker in ("two", "minor release", "consumer-app-descriptor"):
            self.assertIn(
                marker,
                doc.lower(),
                f"bridge guard docstring must reference removal trigger marker {marker!r}; got:\n{doc}",
            )


class CatalogManifestDeprecationTests(unittest.TestCase):
    """FR-008 / AC-009: apps/catalog/manifest.yaml is marked as a deprecated compatibility artifact."""

    def test_catalog_manifest_template_has_deprecation_header_comment(self) -> None:
        text = CATALOG_MANIFEST_TEMPLATE.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:10])
        self.assertIn(
            "DEPRECATED",
            head,
            f"catalog manifest template must lead with a DEPRECATED header comment; got:\n{head}",
        )
        self.assertIn(
            "apps/descriptor.yaml",
            head,
            "deprecation header must reference the canonical apps/descriptor.yaml replacement",
        )
        # Two-minor-release window must be explicit so consumers can plan migration
        self.assertTrue(
            "two" in head.lower() and "minor release" in head.lower(),
            f"deprecation header must name the two-minor-release migration window; got:\n{head}",
        )

    def test_rendered_catalog_manifest_contains_deprecation_header_comment(self) -> None:
        """The deprecation header must survive `make apps-bootstrap` rendering and land in the live file."""
        text = RENDERED_CATALOG_MANIFEST.read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:10])
        self.assertIn(
            "DEPRECATED",
            head,
            f"rendered catalog manifest must include the DEPRECATED header comment; got:\n{head}",
        )


class BacklogDecommissionTrackingTests(unittest.TestCase):
    """AC-009: AGENTS.backlog.md tracks decommission with the consumer-app-descriptor-adoption trigger."""

    def test_backlog_tracks_apps_catalog_manifest_decommission(self) -> None:
        text = BACKLOG_PATH.read_text(encoding="utf-8")
        self.assertIn("decommission:", text.lower())
        self.assertIn("apps/catalog/manifest.yaml", text)
        self.assertIn("after: consumer-app-descriptor-adoption", text)

    def test_backlog_tracks_consumer_owned_workload_bridge_decommission(self) -> None:
        text = BACKLOG_PATH.read_text(encoding="utf-8")
        self.assertIn("_is_consumer_owned_workload()", text)
        # Same trigger phrase MUST be present so step01-intake surfaces both at once
        self.assertIn("after: consumer-app-descriptor-adoption", text)


if __name__ == "__main__":
    unittest.main()
