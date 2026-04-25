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

    def _render_legacy_contract_without_codex_prefixes(self) -> str:
        content = CONTRACT_PATH.read_text(encoding="utf-8")
        content = re.sub(r"(?m)^\s*-\s*codex/\s*$", "", content, count=1)
        content = re.sub(r"(?m)^\s*-\s*copilot/\s*$", "", content, count=1)
        return content

    def test_optional_runtime_contracts_disabled_pass_validation(self) -> None:
        self._run_validate(
            {
                "BLUEPRINT_BRANCH_NAME": "main",
                "APP_CATALOG_SCAFFOLD_ENABLED": "false",
                "APP_RUNTIME_GITOPS_ENABLED": "false",
                "LOCAL_POST_DEPLOY_HOOK_ENABLED": "false",
                "EVENT_MESSAGING_BASELINE_ENABLED": "false",
                "ZERO_DOWNTIME_EVOLUTION_ENABLED": "false",
                "TENANT_CONTEXT_PROPAGATION_ENABLED": "false",
            }
        )

    def test_optional_runtime_contracts_enabled_pass_validation(self) -> None:
        self._run_validate(
            {
                "BLUEPRINT_BRANCH_NAME": "main",
                "APP_CATALOG_SCAFFOLD_ENABLED": "true",
                "APP_RUNTIME_GITOPS_ENABLED": "true",
                "LOCAL_POST_DEPLOY_HOOK_ENABLED": "true",
                "EVENT_MESSAGING_BASELINE_ENABLED": "true",
                "ZERO_DOWNTIME_EVOLUTION_ENABLED": "true",
                "TENANT_CONTEXT_PROPAGATION_ENABLED": "true",
            }
        )

    def test_local_post_deploy_hook_contract_missing_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?ms)^  local_post_deploy_hook_contract:\n.*?(?=^  tech_preferences:\n)",
                "",
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
                "spec.local_post_deploy_hook_contract is required",
                result.stdout + result.stderr,
            )

    def test_local_post_deploy_hook_command_toggle_reference_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = content.replace(
                "    command_env_var: LOCAL_POST_DEPLOY_HOOK_CMD",
                "    command_env_var: LOCAL_POST_DEPLOY_HOOK_CMD_MISSING",
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
                "spec.local_post_deploy_hook_contract.command_env_var must reference an existing toggle",
                result.stdout + result.stderr,
            )

    def test_local_post_deploy_hook_disabled_allows_missing_consumer_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?m)^    consumer_target:\s*.+\n",
                "",
                content,
                count=1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "main",
                    "LOCAL_POST_DEPLOY_HOOK_ENABLED": "false",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("[infra-validate] contract validation passed", result.stdout)

    def test_app_catalog_scaffold_contract_missing_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?ms)^  app_catalog_scaffold_contract:\n.*?(?=^  tech_preferences:\n)",
                "",
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
                "spec.app_catalog_scaffold_contract is required",
                result.stdout + result.stderr,
            )

    def test_app_catalog_scaffold_contract_enabled_missing_path_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = content.replace(
                "      - apps/catalog/manifest.yaml",
                "      - apps/catalog/missing-manifest.yaml",
                1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "main",
                    "APP_CATALOG_SCAFFOLD_ENABLED": "true",
                },
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(
                "missing file: apps/catalog/missing-manifest.yaml",
                result.stdout + result.stderr,
            )

    def test_app_runtime_gitops_contract_missing_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?ms)^  app_runtime_gitops_contract:\n.*?(?=^  tech_preferences:\n)",
                "",
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
                "spec.app_runtime_gitops_contract is required",
                result.stdout + result.stderr,
            )

    def test_app_runtime_gitops_contract_enabled_missing_path_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = content.replace(
                "      - infra/gitops/platform/base/apps/backend-api-deployment.yaml",
                "      - infra/gitops/platform/base/apps/missing-backend-deployment.yaml",
                1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "main",
                    "APP_RUNTIME_GITOPS_ENABLED": "true",
                },
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(
                "missing file: infra/gitops/platform/base/apps/missing-backend-deployment.yaml",
                result.stdout + result.stderr,
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

    def test_branch_naming_compat_accepts_codex_prefix_for_legacy_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            contract_path.write_text(self._render_legacy_contract_without_codex_prefixes(), encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "codex/upgrade-consumer-blueprint",
                    "EVENT_MESSAGING_BASELINE_ENABLED": "false",
                    "APP_RUNTIME_GITOPS_ENABLED": "true",
                    "ZERO_DOWNTIME_EVOLUTION_ENABLED": "false",
                    "TENANT_CONTEXT_PROPAGATION_ENABLED": "false",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("[infra-validate] contract validation passed", result.stdout)

    def test_branch_naming_unknown_prefix_still_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            contract_path.write_text(self._render_legacy_contract_without_codex_prefixes(), encoding="utf-8")
            result = self._run_validate_result(
                contract_path,
                {
                    "BLUEPRINT_BRANCH_NAME": "assistant/upgrade-consumer-blueprint",
                    "EVENT_MESSAGING_BASELINE_ENABLED": "false",
                    "APP_RUNTIME_GITOPS_ENABLED": "true",
                    "ZERO_DOWNTIME_EVOLUTION_ENABLED": "false",
                    "TENANT_CONTEXT_PROPAGATION_ENABLED": "false",
                },
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("must start with one of allowed purpose prefixes", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
