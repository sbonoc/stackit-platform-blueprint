"""Issue #230 / AC-004 — contract drift guard for the init force-reseed scope.

Asserts that ``blueprint/contract.yaml``'s ``consumer_seeded`` list declares
every path the ``blueprint-init-repo`` force-reseed actually writes — in
particular, that ``apps/descriptor.yaml`` and
``infra/gitops/platform/base/apps/kustomization.yaml`` (the descriptor↔
kustomization paired-reseed group from Option A) are BOTH present.

Without this guard, a future contract edit could remove either path from
``consumer_seeded`` and silently regress issue #230 — the validator and
smoke assertion (PR #228) would still run, but the init force-reseed
would only update one half of the pair.
"""
from __future__ import annotations

import unittest

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.helpers import REPO_ROOT


# Paths that the blueprint-init-repo force-reseed must overwrite together
# to keep validate_app_descriptor → verify_kustomization_membership green
# on every consumer upgrade. Adding either entry without the other resurrects
# issue #230. The kustomization template was added by issue #230 (Option A);
# the descriptor template was added by the consumer-app-descriptor work item.
INIT_FORCE_PAIRED_PATHS = (
    "apps/descriptor.yaml",
    "infra/gitops/platform/base/apps/kustomization.yaml",
)


class ContractInitForcePairedPathsCompleteTests(unittest.TestCase):
    def test_blueprint_contract_consumer_seeded_includes_paired_init_paths(self) -> None:
        contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        missing = [p for p in INIT_FORCE_PAIRED_PATHS if p not in consumer_seeded]
        self.assertEqual(
            missing,
            [],
            msg=(
                "blueprint/contract.yaml consumer_seeded MUST list every path the "
                "blueprint-init-repo force-reseed writes; missing paths regress "
                "issue #230 (descriptor↔kustomization lockstep on force-init). "
                f"Missing: {missing}"
            ),
        )

    def test_bootstrap_contract_template_consumer_seeded_includes_paired_init_paths(self) -> None:
        """Mirror the assertion against the bootstrap template so newly-generated
        consumer repos inherit the paired-reseed scope."""
        bootstrap_contract_path = (
            REPO_ROOT / "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml"
        )
        contract = load_blueprint_contract(bootstrap_contract_path)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        missing = [p for p in INIT_FORCE_PAIRED_PATHS if p not in consumer_seeded]
        self.assertEqual(
            missing,
            [],
            msg=(
                "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml "
                "consumer_seeded MUST stay in lockstep with the source contract; "
                f"missing: {missing}"
            ),
        )

    def test_paired_init_paths_have_consumer_init_template_files(self) -> None:
        """Every paired-reseed path MUST have a matching .tmpl under the consumer
        init template root, so seed_consumer_owned_files can render it on force."""
        contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
        template_root = REPO_ROOT / contract.repository.consumer_init.template_root
        for relative_path in INIT_FORCE_PAIRED_PATHS:
            template_path = template_root / f"{relative_path}.tmpl"
            self.assertTrue(
                template_path.is_file(),
                msg=(
                    f"missing consumer-init template for paired-reseed path "
                    f"{relative_path}: expected {template_path} to exist"
                ),
            )


if __name__ == "__main__":
    unittest.main()
