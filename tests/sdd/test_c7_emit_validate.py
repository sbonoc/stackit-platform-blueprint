"""T-103: helper schema-validation function MUST return the parsed record.

Spec T-103: "helper schema-validation function MUST return the parsed
record (not just True/False) when an envelope is well-formed; unit test
asserts the returned record preserves all eleven required fields +
execution_mode."
"""
from __future__ import annotations

import json
import unittest

from scripts.lib.sdd.c7_emit import (
    EmitC7EventUseCase,
    EnvVarModelResolver,
    LifecycleEvent,
    validate_event,
)


class ValidateEventTests(unittest.TestCase):
    """Positive-path: validate_event returns the parsed LifecycleEvent."""

    def _build_payload(self) -> dict:
        event = EmitC7EventUseCase(
            ticket_id="347",
            phase="intake",
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=0,
            model_resolver=EnvVarModelResolver(),
        ).build()
        return json.loads(event.model_dump_json())

    def test_validate_returns_parsed_lifecycle_event(self) -> None:
        result = validate_event(self._build_payload())
        self.assertIsInstance(result, LifecycleEvent)

    def test_validate_preserves_all_eleven_required_fields(self) -> None:
        result = validate_event(self._build_payload())
        required = (
            "event_id", "ticket_id", "parent_ticket_id", "phase", "persona",
            "model", "timestamp", "outcome", "rerun_round", "owner_team", "emitter",
        )
        dumped = result.model_dump()
        for field in required:
            self.assertIn(field, dumped, f"Missing required field: {field}")

    def test_validate_preserves_execution_mode_extension(self) -> None:
        result = validate_event(self._build_payload())
        self.assertEqual(result.execution_mode, "human-assisted")

    def test_validate_raises_on_malformed_payload(self) -> None:
        # Missing required field — Pydantic must reject
        bad = {"event_id": "x", "ticket_id": "347"}
        with self.assertRaises(Exception):
            validate_event(bad)

    def test_validate_raises_on_invalid_phase(self) -> None:
        payload = self._build_payload()
        payload["phase"] = "not-a-phase"
        with self.assertRaises(Exception):
            validate_event(payload)

    def test_validate_raises_on_invalid_outcome(self) -> None:
        payload = self._build_payload()
        payload["outcome"] = "not-an-outcome"
        with self.assertRaises(Exception):
            validate_event(payload)

    def test_validate_accepts_opt_out_phase(self) -> None:
        payload = self._build_payload()
        payload["phase"] = "c7-emission-opted-out"
        result = validate_event(payload)
        self.assertEqual(result.phase, "c7-emission-opted-out")


if __name__ == "__main__":
    unittest.main()
