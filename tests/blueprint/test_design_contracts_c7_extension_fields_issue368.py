"""
T-201 — AC-008 (issue #368): verify that design-contracts.md § C7 extension-field
vocabulary contains the three new standardized rows added by #368 and that the
`outcome_details.routing_keys` row no longer restricts scope to `phase: agent-pr-review` only.
"""
from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT

_CONTRACTS_PATH = REPO_ROOT / "docs/blueprint/autonomous-factory/design-contracts.md"


def _read_contracts() -> str:
    return _CONTRACTS_PATH.read_text(encoding="utf-8")


class C7TokenUsageExtensionFieldTests(unittest.TestCase):
    """FR-001 / AC-008: outcome_details.token_usage row present."""

    def test_token_usage_field_row_present(self) -> None:
        self.assertIn("outcome_details.token_usage", _read_contracts())

    def test_token_usage_describes_per_expert_map(self) -> None:
        contracts = _read_contracts()
        self.assertIn("expert_slug", contracts[contracts.index("outcome_details.token_usage"):
                                                contracts.index("outcome_details.token_usage") + 500])

    def test_token_usage_documents_input_tokens_field(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.token_usage")
        surrounding = contracts[idx: idx + 500]
        self.assertIn("input_tokens", surrounding)

    def test_token_usage_documents_output_tokens_field(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.token_usage")
        surrounding = contracts[idx: idx + 500]
        self.assertIn("output_tokens", surrounding)

    def test_token_usage_scope_is_all_panel_dispatched(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.token_usage")
        surrounding = contracts[idx: idx + 600]
        self.assertIn("panel-dispatched", surrounding)


class C7MergerOverheadExtensionFieldTests(unittest.TestCase):
    """FR-002 / AC-008: outcome_details.merger_overhead row present."""

    def test_merger_overhead_field_row_present(self) -> None:
        self.assertIn("outcome_details.merger_overhead", _read_contracts())

    def test_merger_overhead_documents_findings_before_dedup(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.merger_overhead")
        surrounding = contracts[idx: idx + 500]
        self.assertIn("findings_before_dedup", surrounding)

    def test_merger_overhead_documents_findings_after_dedup(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.merger_overhead")
        surrounding = contracts[idx: idx + 500]
        self.assertIn("findings_after_dedup", surrounding)

    def test_merger_overhead_documents_severity_escalation_events(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.merger_overhead")
        surrounding = contracts[idx: idx + 500]
        self.assertIn("severity_escalation_events", surrounding)

    def test_merger_overhead_scope_is_all_panel_dispatched(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.merger_overhead")
        surrounding = contracts[idx: idx + 600]
        self.assertIn("panel-dispatched", surrounding)


class C7TicketTokenSummaryExtensionFieldTests(unittest.TestCase):
    """FR-003 / AC-008: outcome_details.ticket_token_summary row present."""

    def test_ticket_token_summary_field_row_present(self) -> None:
        self.assertIn("outcome_details.ticket_token_summary", _read_contracts())

    def test_ticket_token_summary_documents_total_input_tokens(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.ticket_token_summary")
        surrounding = contracts[idx: idx + 600]
        self.assertIn("total_input_tokens", surrounding)

    def test_ticket_token_summary_documents_total_output_tokens(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.ticket_token_summary")
        surrounding = contracts[idx: idx + 600]
        self.assertIn("total_output_tokens", surrounding)

    def test_ticket_token_summary_documents_total_expert_step_instantiations(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.ticket_token_summary")
        surrounding = contracts[idx: idx + 900]
        self.assertIn("total_expert_step_instantiations", surrounding)

    def test_ticket_token_summary_scope_is_step08_only(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.ticket_token_summary")
        surrounding = contracts[idx: idx + 600]
        self.assertTrue(
            "step08" in surrounding or "agent-pr-review" in surrounding,
            "ticket_token_summary scope must identify step08/agent-pr-review boundary",
        )

    def test_ticket_token_summary_documents_sentinel_minus_one_handling(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.ticket_token_summary")
        surrounding = contracts[idx: idx + 800]
        self.assertIn("-1", surrounding)


class C7RoutingKeysScopeWideningTests(unittest.TestCase):
    """FR-005 / AC-008: outcome_details.routing_keys scope widened beyond agent-pr-review."""

    def test_routing_keys_row_present(self) -> None:
        self.assertIn("outcome_details.routing_keys", _read_contracts())

    def test_routing_keys_scope_is_not_restricted_to_agent_pr_review_only(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.routing_keys")
        surrounding = contracts[idx: idx + 400]
        self.assertNotIn(
            "for `phase: agent-pr-review` events",
            surrounding,
            "routing_keys scope restriction to agent-pr-review must be removed (FR-005)",
        )

    def test_routing_keys_new_scope_covers_all_panel_phases(self) -> None:
        contracts = _read_contracts()
        idx = contracts.index("outcome_details.routing_keys")
        surrounding = contracts[idx: idx + 600]
        self.assertIn("panel-dispatched", surrounding)


class C7ExtensionFieldOrderTests(unittest.TestCase):
    """AC-008: three new rows appear after outcome_details.routing_keys."""

    def test_token_usage_appears_after_routing_keys(self) -> None:
        contracts = _read_contracts()
        rk_idx = contracts.index("outcome_details.routing_keys")
        tu_idx = contracts.index("outcome_details.token_usage")
        self.assertGreater(tu_idx, rk_idx,
                           "token_usage must appear after routing_keys in the table")

    def test_merger_overhead_appears_after_token_usage(self) -> None:
        contracts = _read_contracts()
        tu_idx = contracts.index("outcome_details.token_usage")
        mo_idx = contracts.index("outcome_details.merger_overhead")
        self.assertGreater(mo_idx, tu_idx,
                           "merger_overhead must appear after token_usage in the table")

    def test_ticket_token_summary_appears_after_merger_overhead(self) -> None:
        contracts = _read_contracts()
        mo_idx = contracts.index("outcome_details.merger_overhead")
        ts_idx = contracts.index("outcome_details.ticket_token_summary")
        self.assertGreater(ts_idx, mo_idx,
                           "ticket_token_summary must appear after merger_overhead in the table")


if __name__ == "__main__":
    unittest.main()
