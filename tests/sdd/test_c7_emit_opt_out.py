from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.sdd.c7_emit import (
    EnvVarModelResolver,
    JsonlReaderAdapter,
    JsonlSinkAdapter,
    OptOutAuditUseCase,
)


class OptOutAuditTests(unittest.TestCase):
    """FR-007, AC-004: opt-out audit event semantics."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.sink_path = self.tmp / "c7" / "test.jsonl"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_audit(self, phase: str = "intake") -> OptOutAuditUseCase:
        return OptOutAuditUseCase(
            ticket_id="347",
            phase=phase,
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            sink=JsonlSinkAdapter(self.sink_path),
            reader=JsonlReaderAdapter(self.sink_path),
            model_resolver=EnvVarModelResolver(),
        )

    def test_is_opted_out_true_when_env_zero(self) -> None:
        with patch.dict(os.environ, {"BLUEPRINT_SDD_C7_EMIT": "0"}):
            self.assertTrue(OptOutAuditUseCase.is_opted_out())

    def test_is_opted_out_false_when_env_one(self) -> None:
        with patch.dict(os.environ, {"BLUEPRINT_SDD_C7_EMIT": "1"}):
            self.assertFalse(OptOutAuditUseCase.is_opted_out())

    def test_is_opted_out_false_when_env_absent(self) -> None:
        env_clean = {k: v for k, v in os.environ.items()
                     if k != "BLUEPRINT_SDD_C7_EMIT"}
        with patch.dict(os.environ, env_clean, clear=True):
            self.assertFalse(OptOutAuditUseCase.is_opted_out())

    def test_exactly_one_audit_event_per_invocation(self) -> None:
        audit = self._make_audit()
        audit.emit_audit_event()
        lines = self.sink_path.read_text(encoding="utf-8").splitlines()
        # Exactly ONE audit event written
        self.assertEqual(len(lines), 1)

    def test_audit_event_phase_is_opted_out_sentinel(self) -> None:
        audit = self._make_audit()
        audit.emit_audit_event()
        event = json.loads(self.sink_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(event["phase"], "c7-emission-opted-out")

    def test_audit_event_has_all_eleven_required_fields(self) -> None:
        audit = self._make_audit()
        audit.emit_audit_event()
        event = json.loads(self.sink_path.read_text(encoding="utf-8").splitlines()[0])
        required = {
            "event_id", "ticket_id", "parent_ticket_id", "phase", "persona",
            "model", "timestamp", "outcome", "rerun_round", "owner_team", "emitter",
        }
        for field in required:
            self.assertIn(field, event, f"Opt-out audit event missing field: {field}")

    def test_second_invocation_increments_rerun_round(self) -> None:
        audit = self._make_audit()
        audit.emit_audit_event()
        # Second call uses a fresh audit use case but same sink/reader
        audit2 = self._make_audit()
        audit2.emit_audit_event()
        lines = self.sink_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        self.assertEqual(first["rerun_round"], 0)
        self.assertEqual(second["rerun_round"], 1)


if __name__ == "__main__":
    unittest.main()
