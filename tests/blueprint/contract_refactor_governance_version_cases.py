from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class GovernanceVersionPolicyCases(RefactorContractBase):
    def test_governance_documents_legacy_vendor_registry_exception(self) -> None:
        agents = _read("AGENTS.md")
        decisions = _read("AGENTS.decisions.md")
        versions = _read("scripts/lib/infra/versions.sh")
        postgres_doc = _read("docs/platform/modules/postgres/README.md")
        rabbitmq_doc = _read("docs/platform/modules/rabbitmq/README.md")
        object_storage_doc = _read("docs/platform/modules/object-storage/README.md")

        self.assertIn("vendor repository name that contains `legacy` is allowed", agents)
        self.assertIn("bitnamilegacy/*", decisions)
        self.assertIn("Bitnami publishes some current multi-arch tags under the `bitnamilegacy/*`", versions)
        self.assertIn("despite the registry namespace", postgres_doc)
        self.assertIn("despite the registry namespace", rabbitmq_doc)
        self.assertIn("vendor namespace quirk", object_storage_doc)

    def test_apps_version_baseline_pins_pinia_304(self) -> None:
        versions = _read("scripts/lib/platform/apps/versions.sh")
        baseline = _read("scripts/lib/platform/apps/versions.baseline.sh")
        manifest = _read("apps/catalog/manifest.yaml")
        versions_lock = _read("apps/catalog/versions.lock")

        self.assertIn('PINIA_VERSION="3.0.4"', versions)
        self.assertIn('PINIA_VERSION="3.0.4"', baseline)
        self.assertIn('pinia: 3.0.4', manifest)
        self.assertIn('PINIA_VERSION=3.0.4', versions_lock)

    def test_apps_version_baseline_pins_vue_router_504(self) -> None:
        versions = _read("scripts/lib/platform/apps/versions.sh")
        baseline = _read("scripts/lib/platform/apps/versions.baseline.sh")
        manifest = _read("apps/catalog/manifest.yaml")
        versions_lock = _read("apps/catalog/versions.lock")

        self.assertIn('VUE_ROUTER_VERSION="5.0.4"', versions)
        self.assertIn('VUE_ROUTER_VERSION="5.0.4"', baseline)
        self.assertIn('vue_router: 5.0.4', manifest)
        self.assertIn('VUE_ROUTER_VERSION=5.0.4', versions_lock)
