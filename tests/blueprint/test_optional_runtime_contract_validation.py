from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT, run


VALIDATE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
CONTRACT_PATH = REPO_ROOT / "blueprint/contract.yaml"


class OptionalRuntimeContractValidationTests(unittest.TestCase):
    def _run_validate_result(self, contract_path, env_overrides: dict[str, str]):
        return run(
            [
                sys.executable,
                str(VALIDATE_SCRIPT),
                "--contract-path",
                str(contract_path),
            ],
            env_overrides=env_overrides,
            cwd=REPO_ROOT,
        )

    def _run_validate(self, env_overrides: dict[str, str]) -> None:
        result = self._run_validate_result(CONTRACT_PATH, env_overrides)
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

    def test_event_messaging_contract_empty_mapping_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?ms)^  event_messaging_contract:\n.*?(?=^  zero_downtime_evolution_contract:\n)",
                "  event_messaging_contract: {}\n\n",
                content,
                count=1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "main",
                },
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(
                "spec.event_messaging_contract.enabled_by_default must be a boolean",
                result.stdout + result.stderr,
            )

    def test_integer_fields_reject_boolean_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = content.replace(
                "deprecation_window_releases: 2",
                "deprecation_window_releases: true",
                1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "main",
                },
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(
                "spec.event_messaging_contract.versioning_policy.deprecation_window_releases must be an integer",
                result.stdout + result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
