from __future__ import annotations

import inspect
import unittest

from scripts.lib.blueprint.contract_schema import load_module_contract
from scripts.lib.blueprint.init_repo_contract import load_blueprint_contract_for_init
from tests._shared.helpers import REPO_ROOT, module_flags_env


class ModuleRequiredEnvFixtureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_blueprint_contract_for_init(REPO_ROOT)

    def _required_env_pairs(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for module in self.contract.optional_modules.modules.values():
            module_contract = load_module_contract(REPO_ROOT / module.paths["contract_path"], REPO_ROOT)
            for env_name in module_contract.required_env:
                pairs.append((module.module_id, env_name))
        return sorted(set(pairs), key=lambda item: (item[0], item[1]))

    def test_module_flags_env_has_parameter_for_every_optional_module_toggle(self) -> None:
        signature = inspect.signature(module_flags_env)
        missing: list[str] = []
        for module in self.contract.optional_modules.modules.values():
            expected_param = module.module_id.replace("-", "_")
            if expected_param not in signature.parameters:
                missing.append(f"{module.module_id}->{expected_param}")

        self.assertEqual(
            missing,
            [],
            msg=(
                "module_flags_env missing module toggle parameter(s): "
                + ", ".join(missing)
                + ". Add matching kwargs so fixture enablement remains contract-aligned."
            ),
        )

    def test_module_flags_env_populates_required_env_for_all_enabled_modules(self) -> None:
        all_enabled_kwargs = {
            module.module_id.replace("-", "_"): "true"
            for module in self.contract.optional_modules.modules.values()
        }
        env = module_flags_env(
            profile="stackit-dev",
            hydrate_module_required_env="true",
            **all_enabled_kwargs,
        )

        missing: list[str] = []
        for module_id, env_name in self._required_env_pairs():
            value = str(env.get(env_name, "")).strip()
            if not value:
                missing.append(f"{module_id}:{env_name}")

        self.assertEqual(
            missing,
            [],
            msg=(
                "missing required optional-module fixture env defaults: "
                + ", ".join(missing)
                + ". Update canonical module required-env defaults and fixture hydration wiring."
            ),
        )

    def test_required_env_contract_parity_reports_no_missing_defaults(self) -> None:
        all_enabled_kwargs = {
            module.module_id.replace("-", "_"): "true"
            for module in self.contract.optional_modules.modules.values()
        }
        env = module_flags_env(
            profile="stackit-dev",
            hydrate_module_required_env="true",
            **all_enabled_kwargs,
        )

        missing_by_module: dict[str, list[str]] = {}
        for module in self.contract.optional_modules.modules.values():
            module_contract = load_module_contract(REPO_ROOT / module.paths["contract_path"], REPO_ROOT)
            required_missing = [
                env_name
                for env_name in module_contract.required_env
                if not str(env.get(env_name, "")).strip()
            ]
            if required_missing:
                missing_by_module[module.module_id] = sorted(required_missing)

        self.assertEqual(
            missing_by_module,
            {},
            msg=(
                "optional-module required_env parity drift detected: "
                + "; ".join(
                    f"{module_id}=[{','.join(names)}]"
                    for module_id, names in sorted(missing_by_module.items())
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
