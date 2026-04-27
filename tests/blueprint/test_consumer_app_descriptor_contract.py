from __future__ import annotations

from pathlib import Path
import unittest

import yaml

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.helpers import REPO_ROOT


CONSUMER_DESCRIPTOR_RELATIVE_PATH = "apps/descriptor.yaml"
CONSUMER_DESCRIPTOR_TEMPLATE_RELATIVE_PATH = "apps/descriptor.yaml.tmpl"
BOOTSTRAP_CONTRACT_PATH = (
    REPO_ROOT / "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml"
)
SOURCE_CONTRACT_PATH = REPO_ROOT / "blueprint/contract.yaml"
CONSUMER_INIT_TEMPLATE_ROOT = REPO_ROOT / "scripts/templates/consumer/init"


class ConsumerAppDescriptorContractTests(unittest.TestCase):
    def test_apps_descriptor_listed_under_consumer_seeded_in_source_contract(self) -> None:
        contract = load_blueprint_contract(SOURCE_CONTRACT_PATH)
        self.assertIn(
            CONSUMER_DESCRIPTOR_RELATIVE_PATH,
            contract.repository.consumer_seeded_paths,
            "blueprint/contract.yaml must declare apps/descriptor.yaml as consumer-seeded",
        )

    def test_apps_descriptor_listed_under_consumer_seeded_in_bootstrap_mirror(self) -> None:
        contract = load_blueprint_contract(BOOTSTRAP_CONTRACT_PATH)
        self.assertIn(
            CONSUMER_DESCRIPTOR_RELATIVE_PATH,
            contract.repository.consumer_seeded_paths,
            "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml must declare "
            "apps/descriptor.yaml as consumer-seeded so generated consumers receive it",
        )

    def test_consumer_init_template_exists_for_app_descriptor(self) -> None:
        template_path = CONSUMER_INIT_TEMPLATE_ROOT / CONSUMER_DESCRIPTOR_TEMPLATE_RELATIVE_PATH
        self.assertTrue(
            template_path.is_file(),
            f"missing consumer init template: {template_path}",
        )

    def test_baseline_template_yaml_is_safe_loadable_with_baseline_apps(self) -> None:
        template_path = CONSUMER_INIT_TEMPLATE_ROOT / CONSUMER_DESCRIPTOR_TEMPLATE_RELATIVE_PATH
        text = template_path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(text)
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("schemaVersion"), "v1")
        apps = loaded.get("apps")
        self.assertIsInstance(apps, list)
        app_ids = {entry.get("id") for entry in apps if isinstance(entry, dict)}
        self.assertEqual(
            app_ids,
            {"backend-api", "touchpoints-web"},
            "baseline app descriptor template must seed exactly the two baseline apps",
        )
        for entry in apps:
            self.assertIsInstance(entry, dict)
            owner = entry.get("owner")
            self.assertIsInstance(owner, dict)
            self.assertIn("team", owner)
            components = entry.get("components")
            self.assertIsInstance(components, list)
            self.assertGreaterEqual(len(components), 1)
            for component in components:
                self.assertIsInstance(component, dict)
                self.assertIn("id", component)
                self.assertIn("kind", component)
                manifests = component.get("manifests")
                self.assertIsInstance(manifests, dict)
                deployment_path = manifests.get("deployment")
                service_path = manifests.get("service")
                self.assertIsInstance(deployment_path, str)
                self.assertIsInstance(service_path, str)
                self.assertTrue(
                    deployment_path.startswith("infra/gitops/platform/base/apps/"),
                    f"deployment manifest must live under apps base path: {deployment_path}",
                )
                self.assertTrue(
                    service_path.startswith("infra/gitops/platform/base/apps/"),
                    f"service manifest must live under apps base path: {service_path}",
                )
                resolved_deployment = REPO_ROOT / "scripts/templates/consumer/init" / f"{deployment_path}.tmpl"
                self.assertTrue(
                    resolved_deployment.is_file(),
                    f"baseline deployment manifest template must exist: {resolved_deployment}",
                )

    def test_source_and_bootstrap_contracts_share_consumer_seeded_descriptor_entry(self) -> None:
        source_contract = load_blueprint_contract(SOURCE_CONTRACT_PATH)
        bootstrap_contract = load_blueprint_contract(BOOTSTRAP_CONTRACT_PATH)
        self.assertEqual(
            source_contract.repository.consumer_seeded_paths,
            bootstrap_contract.repository.consumer_seeded_paths,
            "source and bootstrap contracts must agree on consumer_seeded paths",
        )


if __name__ == "__main__":
    unittest.main()
