"""Tests for scripts/bin/quality/validate_c7_jsonl.py.

Covers: required-field check, emitter enum, rerun_round non-negative,
phase enum, and outcome enum — all fields the JSONL pre-push hook validates.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.bin.quality.validate_c7_jsonl import validate_file, _VALID_PHASES, _VALID_OUTCOMES  # noqa: E402


def _good_event(**overrides) -> dict:
    base = {
        "event_id": "abc123",
        "ticket_id": "347",
        "parent_ticket_id": None,
        "phase": "intake",
        "persona": "blueprint-sdd-step01-intake",
        "model": "claude-sonnet-4-6",
        "timestamp": "2026-05-31T00:00:00Z",
        "outcome": "success",
        "rerun_round": 0,
        "owner_team": "platform-ops",
        "emitter": "local-cli",
        "execution_mode": "human-assisted",
    }
    base.update(overrides)
    return base


class ValidateFileRequiredFieldsTests(unittest.TestCase):
    def _write_jsonl(self, tmp_path: Path, event: dict) -> Path:
        p = tmp_path / "test.jsonl"
        p.write_text(json.dumps(event) + "\n", encoding="utf-8")
        return p

    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_valid_event_produces_no_errors(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event())
        self.assertEqual(validate_file(p), [])

    def test_missing_required_field_is_reported(self) -> None:
        event = _good_event()
        del event["ticket_id"]
        p = self._write_jsonl(self._tmp, event)
        errors = validate_file(p)
        self.assertTrue(any("ticket_id" in e for e in errors))

    def test_invalid_emitter_is_reported(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(emitter="bogus-emitter"))
        errors = validate_file(p)
        self.assertTrue(any("emitter" in e for e in errors))

    def test_negative_rerun_round_is_reported(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(rerun_round=-1))
        errors = validate_file(p)
        self.assertTrue(any("rerun_round" in e for e in errors))

    def test_invalid_phase_is_reported(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(phase="typo-phase"))
        errors = validate_file(p)
        self.assertTrue(any("phase" in e for e in errors), errors)

    def test_invalid_outcome_is_reported(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(outcome="ok"))
        errors = validate_file(p)
        self.assertTrue(any("outcome" in e for e in errors), errors)

    def test_opt_out_phase_is_valid(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(phase="c7-emission-opted-out", outcome="rejected"))
        self.assertEqual(validate_file(p), [])

    def test_all_sdd_phases_are_valid(self) -> None:
        for phase in _VALID_PHASES:
            with self.subTest(phase=phase):
                p = self._write_jsonl(self._tmp, _good_event(phase=phase))
                errors = [e for e in validate_file(p) if "phase" in e]
                self.assertEqual(errors, [], f"phase {phase!r} should be valid")

    def test_all_outcomes_are_valid(self) -> None:
        for outcome in _VALID_OUTCOMES:
            with self.subTest(outcome=outcome):
                p = self._write_jsonl(self._tmp, _good_event(outcome=outcome))
                errors = [e for e in validate_file(p) if "outcome" in e]
                self.assertEqual(errors, [], f"outcome {outcome!r} should be valid")

    def test_local_cli_missing_execution_mode_is_reported(self) -> None:
        event = _good_event()
        del event["execution_mode"]
        p = self._write_jsonl(self._tmp, event)
        errors = validate_file(p)
        self.assertTrue(any("execution_mode" in e for e in errors), errors)

    def test_local_cli_wrong_execution_mode_is_reported(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(execution_mode="automated"))
        errors = validate_file(p)
        self.assertTrue(any("execution_mode" in e for e in errors), errors)

    def test_local_cli_correct_execution_mode_passes(self) -> None:
        p = self._write_jsonl(self._tmp, _good_event(execution_mode="human-assisted"))
        self.assertEqual(validate_file(p), [])

    def test_non_local_cli_emitter_does_not_require_execution_mode(self) -> None:
        event = _good_event(emitter="orchestrator")
        del event["execution_mode"]
        p = self._write_jsonl(self._tmp, event)
        errors = [e for e in validate_file(p) if "execution_mode" in e]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
