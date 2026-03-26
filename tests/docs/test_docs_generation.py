from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, run


def module_ids_from_contract() -> list[str]:
    module_contracts = sorted((REPO_ROOT / "blueprint" / "modules").glob("*/module.contract.yaml"))
    return [path.parent.name for path in module_contracts]


class DocsGenerationTests(unittest.TestCase):
    def test_docs_build_and_smoke(self) -> None:
        install = run(["make", "docs-install"])
        self.assertEqual(install.returncode, 0, msg=install.stdout + install.stderr)

        build = run(["make", "docs-build"])
        self.assertEqual(build.returncode, 0, msg=build.stdout + build.stderr)

        smoke = run(["make", "docs-smoke"])
        self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)

        core_targets_check = run(["make", "quality-docs-check-core-targets-sync"])
        self.assertEqual(core_targets_check.returncode, 0, msg=core_targets_check.stdout + core_targets_check.stderr)

        contract_metadata_check = run(["make", "quality-docs-check-contract-metadata-sync"])
        self.assertEqual(
            contract_metadata_check.returncode,
            0,
            msg=contract_metadata_check.stdout + contract_metadata_check.stderr,
        )

        contract_generated = REPO_ROOT / "docs" / "reference" / "generated" / "contract_metadata.generated.md"
        self.assertTrue(contract_generated.exists(), msg="generated contract metadata doc not found")
        contract_content = contract_generated.read_text(encoding="utf-8")
        self.assertIn("Contract Metadata (Generated)", contract_content)
        self.assertIn("## Supported Profiles", contract_content)
        self.assertIn("## Required Make Targets", contract_content)
        self.assertIn("## Optional Modules", contract_content)

        for module_id in module_ids_from_contract():
            self.assertIn(f"Module: `{module_id}`", contract_content)

        core_targets_generated = REPO_ROOT / "docs" / "reference" / "generated" / "core_targets.generated.md"
        self.assertTrue(core_targets_generated.exists(), msg="generated core targets doc not found")
        core_targets_content = core_targets_generated.read_text(encoding="utf-8")
        self.assertIn("Core Make Targets", core_targets_content)
        self.assertIn("`quality-hooks-run`", core_targets_content)
        self.assertIn("`quality-test-pyramid`", core_targets_content)


if __name__ == "__main__":
    unittest.main()
