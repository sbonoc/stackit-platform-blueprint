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

    def test_checker_resolves_source_only_directory_roots_without_trailing_slash(self) -> None:
        result = _run_checker("--json", "tests/blueprint/test_ownership_check.py")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["owner"], "source-only")

    def test_checker_resolves_dot_prefixed_consumer_seeded_paths(self) -> None:
        result = _run_checker("--json", ".github/CODEOWNERS")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["owner"], "consumer-seeded")

    def test_checker_marks_parent_traversal_as_outside_repository(self) -> None:
        result = _run_checker("--json", "../make/platform.mk")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["owner"], "outside-repository")

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

    def test_ownership_help_text_uses_plain_quotes(self) -> None:
        makefile_text = (REPO_ROOT / "make" / "blueprint.generated.mk").read_text(encoding="utf-8")
        self.assertIn('OWNERSHIP_PATHS="path/one path/two"', makefile_text)
        self.assertNotIn('OWNERSHIP_PATHS=\\"path/one path/two\\"', makefile_text)

        help_result = run_command(["make", "help"], cwd=REPO_ROOT)
        self.assertEqual(help_result.returncode, 0, msg=help_result.stdout + help_result.stderr)
        self.assertIn('OWNERSHIP_PATHS="path/one path/two"', help_result.stdout)
        self.assertNotIn('OWNERSHIP_PATHS=\\"path/one path/two\\"', help_result.stdout)


if __name__ == "__main__":
    unittest.main()
