"""Regression test for issue #260 — blueprint-template-smoke target filtering.

Ensures _get_effective_validation_targets filters 'blueprint-template-smoke'
from VALIDATION_TARGETS when repo_mode equals the generated-consumer mode value,
mirroring the skip logic already applied by the quality-hooks-strict runner.
"""

from __future__ import annotations

import unittest

from scripts.lib.blueprint.upgrade_consumer_validate import (
    VALIDATION_TARGETS,
    _get_effective_validation_targets,
)
from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.helpers import REPO_ROOT

_CONTRACT_PATH = REPO_ROOT / "blueprint" / "contract.yaml"
_TEMPLATE_SMOKE_TARGET = "blueprint-template-smoke"


class ValidateTargetFilterIssue260Tests(unittest.TestCase):
    def test_template_smoke_excluded_for_generated_consumer(self) -> None:
        """blueprint-template-smoke MUST NOT appear in effective targets for generated-consumer."""
        contract = load_blueprint_contract(_CONTRACT_PATH)
        # Patch repo_mode to generated-consumer via a fake contract object
        from unittest.mock import MagicMock
        fake_contract = MagicMock()
        fake_contract.repository.repo_mode = "generated-consumer"
        fake_contract.repository.consumer_init.mode_to = "generated-consumer"

        targets = _get_effective_validation_targets(fake_contract)
        self.assertNotIn(
            _TEMPLATE_SMOKE_TARGET,
            targets,
            msg=(
                f"'{_TEMPLATE_SMOKE_TARGET}' must be filtered from VALIDATION_TARGETS "
                "when repo_mode equals generated-consumer."
            ),
        )

    def test_template_smoke_present_for_template_source(self) -> None:
        """blueprint-template-smoke MUST remain in effective targets for template-source repos."""
        from unittest.mock import MagicMock
        fake_contract = MagicMock()
        fake_contract.repository.repo_mode = "template-source"
        fake_contract.repository.consumer_init.mode_to = "generated-consumer"

        targets = _get_effective_validation_targets(fake_contract)
        self.assertIn(
            _TEMPLATE_SMOKE_TARGET,
            targets,
            msg=(
                f"'{_TEMPLATE_SMOKE_TARGET}' must remain in VALIDATION_TARGETS "
                "for template-source repos — it is a valid check there."
            ),
        )

    def test_all_other_targets_preserved_for_generated_consumer(self) -> None:
        """All targets other than blueprint-template-smoke must be preserved."""
        from unittest.mock import MagicMock
        fake_contract = MagicMock()
        fake_contract.repository.repo_mode = "generated-consumer"
        fake_contract.repository.consumer_init.mode_to = "generated-consumer"

        targets = _get_effective_validation_targets(fake_contract)
        expected_preserved = [t for t in VALIDATION_TARGETS if t != _TEMPLATE_SMOKE_TARGET]
        for target in expected_preserved:
            self.assertIn(
                target,
                targets,
                msg=f"Non-smoke target '{target}' must not be removed by the filter.",
            )

    def test_real_contract_template_source_mode_includes_smoke(self) -> None:
        """The real contract (template-source mode) must include blueprint-template-smoke."""
        contract = load_blueprint_contract(_CONTRACT_PATH)
        targets = _get_effective_validation_targets(contract)
        self.assertIn(
            _TEMPLATE_SMOKE_TARGET,
            targets,
            msg="Real contract is template-source; blueprint-template-smoke must be included.",
        )
