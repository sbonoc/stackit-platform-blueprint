"""Regression tests for issue #277 — ArgoCD health=N/A fix.

AC-001: argocd.values.yaml overrides ignoreResourceUpdates.all to empty string.
AC-002: bootstrap template argocd.values.yaml applies the same override.
AC-003: ARGOCD_CHART_VERSION is pinned to 9.5.13 in versions.sh.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

_ARGOCD_VALUES = REPO_ROOT / "infra/local/helm/core/argocd.values.yaml"
_ARGOCD_TEMPLATE = REPO_ROOT / "scripts/templates/infra/bootstrap/infra/local/helm/core/argocd.values.yaml"
_VERSIONS_SH = REPO_ROOT / "scripts/lib/infra/versions.sh"
_VERSIONS_BASELINE_SH = REPO_ROOT / "scripts/lib/infra/versions.baseline.sh"
_EXPECTED_CHART_VERSION = "9.5.13"
_IGNORE_KEY = "resource.customizations.ignoreResourceUpdates.all"
_VERSION_RE = re.compile(r'^ARGOCD_CHART_VERSION="([^"]+)"', re.MULTILINE)


class ArgoCDHealthFixTests(unittest.TestCase):
    def _assert_ignore_all_is_empty(self, path: Path) -> None:
        values = yaml.safe_load(path.read_text(encoding="utf-8"))
        cm = (values or {}).get("configs", {}).get("cm", {})
        self.assertIn(
            _IGNORE_KEY,
            cm,
            msg=f"{path.relative_to(REPO_ROOT)}: missing configs.cm['{_IGNORE_KEY}'] override (issue #277 fix not applied)",
        )
        value = cm[_IGNORE_KEY]
        self.assertEqual(
            value,
            "",
            msg=(
                f"{path.relative_to(REPO_ROOT)}: configs.cm['{_IGNORE_KEY}'] "
                f"MUST be empty string to prevent health=N/A; got {value!r}"
            ),
        )

    def test_argocd_values_ignoreResourceUpdates_all_is_empty(self) -> None:
        """AC-001: infra/local/helm/core/argocd.values.yaml must override ignoreResourceUpdates.all to ''."""
        self._assert_ignore_all_is_empty(_ARGOCD_VALUES)

    def test_argocd_template_ignoreResourceUpdates_all_is_empty(self) -> None:
        """AC-002: bootstrap template argocd.values.yaml must carry the same override."""
        self._assert_ignore_all_is_empty(_ARGOCD_TEMPLATE)

    def _assert_chart_version(self, path: Path) -> None:
        content = path.read_text(encoding="utf-8")
        match = _VERSION_RE.search(content)
        self.assertIsNotNone(
            match,
            msg=f"ARGOCD_CHART_VERSION not found in {path.relative_to(REPO_ROOT)}",
        )
        actual = match.group(1)
        self.assertEqual(
            actual,
            _EXPECTED_CHART_VERSION,
            msg=f"ARGOCD_CHART_VERSION is {actual!r}; expected {_EXPECTED_CHART_VERSION!r} (issue #277 chart bump)",
        )

    def test_argocd_chart_version_is_9_5_13(self) -> None:
        """AC-003: ARGOCD_CHART_VERSION must be pinned to 9.5.13 in versions.sh."""
        self._assert_chart_version(_VERSIONS_SH)

    def test_argocd_baseline_chart_version_is_9_5_13(self) -> None:
        """AC-003: ARGOCD_CHART_VERSION must be pinned to 9.5.13 in versions.baseline.sh."""
        self._assert_chart_version(_VERSIONS_BASELINE_SH)


if __name__ == "__main__":
    unittest.main()
