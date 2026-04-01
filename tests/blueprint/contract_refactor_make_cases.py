from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class MakeRefactorCases(RefactorContractBase):
    def test_make_contract_optional_materialization_is_canonical(self) -> None:
        contract_lines = self._contract_lines()
        make_contract_section = _extract_yaml_section(contract_lines, "make_contract")
        required_targets = set(_extract_yaml_list(contract_lines, "required_targets"))
        required_namespaces = set(_extract_yaml_list(contract_lines, "required_namespaces"))
        optional_target_materialization = _extract_yaml_section(
            make_contract_section,
            "optional_target_materialization",
        )
        self.assertEqual(_extract_yaml_scalar(optional_target_materialization, "mode"), "conditional")
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "source_template"),
            "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
        )
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "output_file"),
            "make/blueprint.generated.mk",
        )
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "materialization_command"),
            "make blueprint-render-makefile",
        )

        make_targets = _make_targets()
        self.assertTrue(required_targets.issubset(make_targets), msg="contract required_targets drifted from Makefile")
        for namespace in required_namespaces:
            self.assertTrue(any(target.startswith(namespace) for target in make_targets))

    def test_platform_make_is_seeded_but_not_template_synced(self) -> None:
        contract_lines = _read("blueprint/contract.yaml").splitlines()
        make_contract = _extract_yaml_section(contract_lines, "make_contract")
        ownership = _extract_yaml_section(make_contract, "ownership")
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        bootstrap_lib = _read("scripts/lib/shell/bootstrap.sh")
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")

        self.assertEqual(_extract_yaml_scalar(ownership, "platform_seed_mode"), "create_if_missing")
        self.assertEqual(_extract_yaml_scalar(ownership, "platform_editable_file"), "make/platform.mk")
        self.assertEqual(_extract_yaml_scalar(ownership, "blueprint_generated_file"), "make/blueprint.generated.mk")
        self.assertIn('"make/platform.mk"', bootstrap)
        self.assertIn("if [[ -f \"$path\" ]]; then", bootstrap_lib)
        self.assertIn("_validate_make_ownership_contract", validate_py)
        self.assertNotIn('"make/platform.mk",', validate_py)

    def test_makefile_template_supports_conditional_optional_targets(self) -> None:
        makefile_template = _read("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl")
        makefile_renderer = _read("scripts/bin/blueprint/render_makefile.sh")

        self.assertIn("{{PHONY_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{PHONY_WORKFLOWS}}", makefile_template)
        self.assertIn("{{PHONY_LANGFUSE}}", makefile_template)
        self.assertIn("{{PHONY_POSTGRES}}", makefile_template)
        self.assertIn("{{PHONY_NEO4J}}", makefile_template)
        self.assertIn("{{PHONY_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{PHONY_RABBITMQ}}", makefile_template)
        self.assertIn("{{PHONY_DNS}}", makefile_template)
        self.assertIn("{{PHONY_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{PHONY_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{PHONY_KMS}}", makefile_template)
        self.assertIn("{{PHONY_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_WORKFLOWS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_LANGFUSE}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_POSTGRES}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_NEO4J}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_RABBITMQ}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_DNS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_KMS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn("INFRA_ENV_GUARDED_TARGETS :=", makefile_template)
        self.assertIn("$(INFRA_ENV_GUARDED_TARGETS): blueprint-check-placeholders", makefile_template)
        self.assertIn("{{TARGETS_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{TARGETS_WORKFLOWS}}", makefile_template)
        self.assertIn("{{TARGETS_LANGFUSE}}", makefile_template)
        self.assertIn("{{TARGETS_POSTGRES}}", makefile_template)
        self.assertIn("{{TARGETS_NEO4J}}", makefile_template)
        self.assertIn("{{TARGETS_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{TARGETS_RABBITMQ}}", makefile_template)
        self.assertIn("{{TARGETS_DNS}}", makefile_template)
        self.assertIn("{{TARGETS_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{TARGETS_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{TARGETS_KMS}}", makefile_template)
        self.assertIn("{{TARGETS_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn('"INFRA_ENV_GUARDED_OBSERVABILITY=$phony_observability" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_WORKFLOWS=$phony_workflows" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_LANGFUSE=$phony_langfuse" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_POSTGRES=$phony_postgres" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_NEO4J=$phony_neo4j" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_OBJECT_STORAGE=$phony_object_storage" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_RABBITMQ=$phony_rabbitmq" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_DNS=$phony_dns" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_PUBLIC_ENDPOINTS=$phony_public_endpoints" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_SECRETS_MANAGER=$phony_secrets_manager" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_KMS=$phony_kms" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_IDENTITY_AWARE_PROXY=$phony_identity_aware_proxy" \\', makefile_renderer)
        self.assertIn("render_makefile()", makefile_renderer)
        self.assertIn('render_bootstrap_template_content \\', makefile_renderer)
        self.assertIn('"blueprint" \\', makefile_renderer)

    def test_async_message_contract_targets_are_in_blueprint_generated_makefiles(self) -> None:
        makefile_template = _read("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl")
        generated_makefile = _read("make/blueprint.generated.mk")

        self.assertIn("test-contracts-async-producer", makefile_template)
        self.assertIn("test-contracts-async-consumer", makefile_template)
        self.assertIn("test-contracts-async-all", makefile_template)
        self.assertIn("test-contracts-all: test-contracts-async-all", makefile_template)

        self.assertIn("test-contracts-async-producer", generated_makefile)
        self.assertIn("test-contracts-async-consumer", generated_makefile)
        self.assertIn("test-contracts-async-all", generated_makefile)
        self.assertIn("test-contracts-all: test-contracts-async-all", generated_makefile)
