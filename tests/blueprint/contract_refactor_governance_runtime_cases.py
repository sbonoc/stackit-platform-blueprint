from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class GovernanceRuntimePolicyCases(RefactorContractBase):
    def test_validator_has_core_contract_sections(self) -> None:
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")
        self.assertIn("load_blueprint_contract", validate_py)
        for marker in (
            "_validate_optional_target_materialization_contract",
            "_validate_template_bootstrap_contract",
            "_validate_branch_naming_contract",
            "_validate_optional_module_make_targets",
            "_validate_module_wrapper_skeleton_templates",
            "_validate_bootstrap_template_sync",
            "_validate_make_ownership_contract",
            "_validate_repository_mode_contract",
            "_validate_script_ownership_contract",
            "_validate_platform_docs_seed_contract",
            "_validate_async_message_contract",
            "_validate_event_messaging_contract",
            "_validate_zero_downtime_evolution_contract",
            "_validate_tenant_context_contract",
        ):
            self.assertIn(marker, validate_py)
        self.assertNotIn("def _extract_yaml_list", validate_py)

    def test_contract_includes_optional_runtime_policy_sections(self) -> None:
        contract_yaml = _read("blueprint/contract.yaml")
        self.assertIn("EVENT_MESSAGING_BASELINE_ENABLED:", contract_yaml)
        self.assertIn("ZERO_DOWNTIME_EVOLUTION_ENABLED:", contract_yaml)
        self.assertIn("TENANT_CONTEXT_PROPAGATION_ENABLED:", contract_yaml)
        self.assertIn("event_messaging_contract:", contract_yaml)
        self.assertIn("zero_downtime_evolution_contract:", contract_yaml)
        self.assertIn("tenant_context_contract:", contract_yaml)

    def test_platform_base_namespaces_include_network_for_shared_gateway(self) -> None:
        namespaces = _read("infra/gitops/platform/base/namespaces.yaml")
        namespaces_template = _read("scripts/templates/infra/bootstrap/infra/gitops/platform/base/namespaces.yaml")
        self.assertIn("name: network", namespaces)
        self.assertIn("Shared gateway/route attachment namespace", namespaces)
        self.assertEqual(namespaces, namespaces_template)
