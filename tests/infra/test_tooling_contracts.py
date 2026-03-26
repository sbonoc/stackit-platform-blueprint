from __future__ import annotations

import unittest

from tests._shared.helpers import run


class ToolingContractsTests(unittest.TestCase):
    def test_help_reference_includes_primary_workflows(self) -> None:
        result = run(["make", "infra-help-reference"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Primary Workflows", result.stdout)
        self.assertIn("make quality-hooks-run", result.stdout)
        self.assertIn("make blueprint-bootstrap", result.stdout)
        self.assertIn("make infra-bootstrap", result.stdout)
        self.assertIn("quality-docs-sync-core-targets", result.stdout)

    def test_prereqs_help_mentions_extended_optional_tooling(self) -> None:
        result = run(["scripts/bin/infra/prereqs.sh", "--help"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("terraform kubectl helm docker kind uv gh jq pnpm kustomize nc", result.stdout)

    def test_quality_test_pyramid_target_passes(self) -> None:
        result = run(["make", "quality-test-pyramid"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[test-pyramid] OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
