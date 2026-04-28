"""Issue #230 reproducer — descriptor↔kustomization lockstep on force-init.

Builds a synthetic generated-consumer repo whose pre-existing
``infra/gitops/platform/base/apps/kustomization.yaml`` lists non-demo
``marketplace-*`` manifests (i.e. the v1.8.0 consumer shape that hits the
upstream bug). Runs ``seed_consumer_owned_files`` with ``force=True`` to
simulate ``BLUEPRINT_INIT_FORCE=true make blueprint-init-repo`` and asserts
that the post-reseed on-disk state satisfies ``validate_app_descriptor``
with zero errors (FR-001, AC-002).

Pre-fix v1.8.1 behaviour: descriptor is force-reseeded to backend-api /
touchpoints-web; the consumer kustomization is preserved with marketplace-*
resources; ``validate_app_descriptor`` reports 4 ``manifest filename not
listed`` errors. The fix (Option A) adds the kustomization to the
``consumer_seeded`` paired-reseed scope so the post-init pair is
membership-consistent by construction.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.bin.blueprint.validate_contract import _kustomization_resources
from scripts.lib.blueprint.app_descriptor import validate_app_descriptor
from scripts.lib.blueprint.cli_support import ChangeSummary
from scripts.lib.blueprint.init_repo_contract import seed_consumer_owned_files
from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.helpers import REPO_ROOT


CONSUMER_KUSTOMIZATION_PRE_UPGRADE = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - marketplace-deployment.yaml
  - marketplace-service.yaml
"""


CONSUMER_DESCRIPTOR_PRE_UPGRADE = """\
schemaVersion: v1
apps:
  - id: marketplace
    owner:
      team: marketplace
    components:
      - id: marketplace
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/marketplace-deployment.yaml
          service: infra/gitops/platform/base/apps/marketplace-service.yaml
        service:
          port: 8080
          targetPort: http
        health:
          readiness: /
          liveness: /
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_generated_consumer_repo(tmp_root: Path) -> None:
    """Materialize a minimal generated-consumer repo at ``tmp_root``.

    Only the surface needed by ``seed_consumer_owned_files`` is created:
    a contract pinned to ``repo_mode: generated-consumer`` and the consumer
    init template tree referenced by ``consumer_seeded``.
    """
    contract_text = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8")
    contract_text = contract_text.replace(
        "repo_mode: template-source",
        "repo_mode: generated-consumer",
        1,
    )
    _write(tmp_root / "blueprint/contract.yaml", contract_text)

    contract = load_blueprint_contract(tmp_root / "blueprint/contract.yaml")
    template_root = REPO_ROOT / contract.repository.consumer_init.template_root
    for relative_path in contract.repository.consumer_seeded_paths:
        src = template_root / f"{relative_path}.tmpl"
        if not src.is_file():
            continue
        _write(
            tmp_root / contract.repository.consumer_init.template_root / f"{relative_path}.tmpl",
            src.read_text(encoding="utf-8"),
        )


def _materialize_v180_consumer_state(tmp_root: Path) -> None:
    """Pre-populate descriptor + kustomization + manifests in the v1.8.0 shape."""
    _write(tmp_root / "apps/descriptor.yaml", CONSUMER_DESCRIPTOR_PRE_UPGRADE)
    _write(
        tmp_root / "infra/gitops/platform/base/apps/kustomization.yaml",
        CONSUMER_KUSTOMIZATION_PRE_UPGRADE,
    )
    for filename in ("marketplace-deployment.yaml", "marketplace-service.yaml"):
        _write(
            tmp_root / "infra/gitops/platform/base/apps" / filename,
            "kind: Deployment\nmetadata:\n  name: marketplace\n",
        )


REPLACEMENTS = {
    "REPO_NAME": "acme-platform",
    "DOCS_TITLE": "Acme Platform",
    "DOCS_TAGLINE": "Acme platform docs",
    "DEFAULT_BRANCH": "main",
    "TEMPLATE_VERSION": "v1-test",
}


def _module_enablement_all_disabled(tmp_root: Path) -> dict[str, bool]:
    contract = load_blueprint_contract(tmp_root / "blueprint/contract.yaml")
    return {module.module_id: False for module in contract.optional_modules.modules.values()}


class ForceInitDescriptorKustomizationPairingTests(unittest.TestCase):
    def test_force_init_against_consumer_kustomization_passes_validate_app_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            _seed_generated_consumer_repo(tmp_root)
            _materialize_v180_consumer_state(tmp_root)

            seed_consumer_owned_files(
                repo_root=tmp_root,
                dry_run=False,
                force=True,
                summary=ChangeSummary(label="init-test"),
                replacements=REPLACEMENTS,
                module_enablement=_module_enablement_all_disabled(tmp_root),
            )

            errors = validate_app_descriptor(tmp_root, _kustomization_resources)
            self.assertEqual(
                errors,
                [],
                msg=(
                    "post-force-init descriptor and kustomization must be membership-consistent; "
                    "got errors: " + "\n".join(errors)
                ),
            )

    def test_force_init_is_idempotent(self) -> None:
        """NFR-REL-001: two consecutive force inits must converge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            _seed_generated_consumer_repo(tmp_root)
            _materialize_v180_consumer_state(tmp_root)

            for _ in range(2):
                seed_consumer_owned_files(
                    repo_root=tmp_root,
                    dry_run=False,
                    force=True,
                    summary=ChangeSummary(label="init-test"),
                    replacements=REPLACEMENTS,
                    module_enablement={},
                )

            self.assertEqual(
                validate_app_descriptor(tmp_root, _kustomization_resources),
                [],
                msg="post-force-init state must remain valid after a second force-init",
            )


if __name__ == "__main__":
    unittest.main()
