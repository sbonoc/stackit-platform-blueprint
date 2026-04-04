from __future__ import annotations

import json
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


def _run_checker(*args: str):
    return run_command(
        ["python3", "scripts/bin/blueprint/ownership_check.py", *args],
        cwd=REPO_ROOT,
    )


class OwnershipCheckTests(unittest.TestCase):
    def test_checker_metadata_exposes_platform_script_rule(self) -> None:
        result = _run_checker("--metadata-json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("rules", payload)
        self.assertTrue(
            any(
                rule.get("owner") == "platform-owned" and rule.get("pattern") == "scripts/bin/platform/"
                for rule in payload["rules"]
            ),
            msg=result.stdout,
        )

    def test_checker_resolves_platform_owned_paths(self) -> None:
        result = _run_checker(
            "--json",
            "scripts/bin/platform/touchpoints/test_e2e.sh",
            "make/platform.mk",
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        owners = {entry["normalized_path"]: entry["owner"] for entry in payload["results"]}
        self.assertEqual(owners["scripts/bin/platform/touchpoints/test_e2e.sh"], "platform-owned")
        self.assertEqual(owners["make/platform.mk"], "platform-owned")

    def test_checker_resolves_blueprint_managed_path(self) -> None:
        result = _run_checker("--json", "scripts/bin/infra/argocd_topology_validate.sh")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["owner"], "blueprint-managed")

    def test_make_target_wraps_checker(self) -> None:
        result = run_command(
            [
                "make",
                "OWNERSHIP_PATHS=scripts/bin/platform/touchpoints/test_e2e.sh",
                "blueprint-ownership-check",
            ],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("owner=platform-owned", result.stdout)


if __name__ == "__main__":
    unittest.main()
