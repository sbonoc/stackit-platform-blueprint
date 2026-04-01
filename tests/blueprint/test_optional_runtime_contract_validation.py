from __future__ import annotations

import sys
import unittest

from tests._shared.helpers import REPO_ROOT, run


VALIDATE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
CONTRACT_PATH = REPO_ROOT / "blueprint/contract.yaml"


class OptionalRuntimeContractValidationTests(unittest.TestCase):
    def _run_validate(self, env_overrides: dict[str, str]) -> None:
        result = run(
            [
                sys.executable,
                str(VALIDATE_SCRIPT),
                "--contract-path",
                str(CONTRACT_PATH),
            ],
            env_overrides=env_overrides,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[infra-validate] contract validation passed", result.stdout)

    def test_optional_runtime_contracts_disabled_pass_validation(self) -> None:
        self._run_validate(
            {
                "BLUEPRINT_BRANCH_NAME": "main",
                "EVENT_MESSAGING_BASELINE_ENABLED": "false",
                "ZERO_DOWNTIME_EVOLUTION_ENABLED": "false",
                "TENANT_CONTEXT_PROPAGATION_ENABLED": "false",
            }
        )

    def test_optional_runtime_contracts_enabled_pass_validation(self) -> None:
        self._run_validate(
            {
                "BLUEPRINT_BRANCH_NAME": "main",
                "EVENT_MESSAGING_BASELINE_ENABLED": "true",
                "ZERO_DOWNTIME_EVOLUTION_ENABLED": "true",
                "TENANT_CONTEXT_PROPAGATION_ENABLED": "true",
            }
        )


if __name__ == "__main__":
    unittest.main()
