from __future__ import annotations

import json
import re
import unittest

from tests._shared.helpers import REPO_ROOT

_CONTRACTS_PATH = REPO_ROOT / "docs/blueprint/autonomous-factory/design-contracts.md"


def _read_contracts() -> str:
    return _CONTRACTS_PATH.read_text(encoding="utf-8")


class C7EmitterEnumTests(unittest.TestCase):
    """Slice 1 contract: three-emitter sealed rule (FR-001, FR-010)."""

    def test_c7_emitter_enum_contains_local_cli(self) -> None:
        self.assertIn('"local-cli"', _read_contracts())

    def test_c7_emitter_enum_retains_orchestrator(self) -> None:
        self.assertIn('"orchestrator"', _read_contracts())

    def test_c7_emitter_enum_retains_webhook_handler(self) -> None:
        self.assertIn('"webhook-handler"', _read_contracts())

    def test_c7_three_emitter_rule_prose(self) -> None:
        contracts = _read_contracts()
        self.assertRegex(contracts, r"EXACTLY ONE OF three deterministic surfaces")

    def test_c7_execution_mode_extension_documented(self) -> None:
        contracts = _read_contracts()
        self.assertIn("execution_mode", contracts)

    def test_c7_local_cli_event_id_rule_documented(self) -> None:
        contracts = _read_contracts()
        self.assertRegex(contracts, r"local-cli.*four-input|four-input.*local-cli", re.DOTALL)


if __name__ == "__main__":
    unittest.main()
