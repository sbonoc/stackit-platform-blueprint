from __future__ import annotations

import unittest
from tests._shared.helpers import REPO_ROOT

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "opensearch"


class OpenSearchTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_has_opensearch_resources(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_opensearch_instance", content)
        self.assertIn("stackit_opensearch_credential", content)
        self.assertIn("create_before_destroy", content)

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        variables_tf = _MODULE_DIR / "variables.tf"
        content = variables_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_project_id", content)
        self.assertIn("opensearch_instance_name", content)
        self.assertIn("opensearch_version", content)
        self.assertIn("opensearch_plan_name", content)

    def test_terraform_module_outputs_expose_contract_keys(self) -> None:
        outputs_tf = _MODULE_DIR / "outputs.tf"
        content = outputs_tf.read_text(encoding="utf-8")
        for key in (
            "opensearch_host",
            "opensearch_hosts",
            "opensearch_port",
            "opensearch_scheme",
            "opensearch_uri",
            "opensearch_dashboard_url",
            "opensearch_username",
            "opensearch_password",
        ):
            self.assertIn(key, content, msg=f"missing output: {key}")

    def test_terraform_module_versions_tf_exists_with_provider_constraint(self) -> None:
        versions_tf = _MODULE_DIR / "versions.tf"
        content = versions_tf.read_text(encoding="utf-8")
        self.assertIn("stackitcloud/stackit", content)
        self.assertIn("required_providers", content)
