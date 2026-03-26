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

        generated = REPO_ROOT / "docs" / "reference" / "generated" / "contract_metadata.generated.md"
        self.assertTrue(generated.exists(), msg="generated docs file not found")
        content = generated.read_text(encoding="utf-8")
        self.assertIn("Contract Metadata (Generated)", content)
        self.assertIn("## Supported Profiles", content)
        self.assertIn("## Required Make Targets", content)
        self.assertIn("## Optional Modules", content)

        for module_id in module_ids_from_contract():
            self.assertIn(f"Module: `{module_id}`", content)


if __name__ == "__main__":
    unittest.main()
