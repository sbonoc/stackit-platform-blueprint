from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.lib.sdd.c7_emit import (
    EmitC7EventUseCase,
    EnvVarModelResolver,
    JsonlReaderAdapter,
    JsonlSinkAdapter,
)


class JsonlRoundTripTests(unittest.TestCase):
    """NFR-OPS-001: rerun_round increments correctly across 10 sequential emissions."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.sink_path = self.tmp / "c7" / "roundtrip.jsonl"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _emit(self, phase: str, rerun_round: int) -> None:
        sink = JsonlSinkAdapter(self.sink_path)
        uc = EmitC7EventUseCase(
            ticket_id="347",
            phase=phase,
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=rerun_round,
            model_resolver=EnvVarModelResolver(),
        )
        sink.append(uc.build())

    def test_ten_sequential_emissions_produce_ten_lines(self) -> None:
        # Mix of phases to verify rerun_round per (ticket_id, phase)
        phases = [
            "intake", "intake", "intake",
            "implement", "implement",
            "intake",
            "document-sync",
            "implement",
            "intake", "intake",
        ]
        for i, phase in enumerate(phases):
            # compute rerun_round from prior events in the sink for this phase
            reader = JsonlReaderAdapter(self.sink_path)
            rerun_round = reader.compute_rerun_round("347", phase)
            self._emit(phase, rerun_round)

        lines = self.sink_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 10)

    def test_rerun_round_increments_per_phase(self) -> None:
        for i in range(5):
            reader = JsonlReaderAdapter(self.sink_path)
            rr = reader.compute_rerun_round("347", "intake")
            self._emit("intake", rr)

        reader = JsonlReaderAdapter(self.sink_path)
        events = reader.read_events()
        intake_events = [e for e in events if e["phase"] == "intake"]
        rounds = [e["rerun_round"] for e in intake_events]
        self.assertEqual(rounds, [0, 1, 2, 3, 4])

    def test_distinct_phases_have_independent_rerun_rounds(self) -> None:
        for phase in ["intake", "implement"]:
            for _ in range(3):
                reader = JsonlReaderAdapter(self.sink_path)
                rr = reader.compute_rerun_round("347", phase)
                self._emit(phase, rr)

        reader = JsonlReaderAdapter(self.sink_path)
        events = reader.read_events()
        for phase in ["intake", "implement"]:
            rounds = [e["rerun_round"] for e in events if e["phase"] == phase]
            self.assertEqual(rounds, [0, 1, 2], f"Wrong rerun_rounds for phase {phase}")

    def test_read_events_returns_all_written_events(self) -> None:
        sink = JsonlSinkAdapter(self.sink_path)
        for i in range(3):
            uc = EmitC7EventUseCase(
                ticket_id="347",
                phase="intake",
                skill_basename="blueprint-sdd-step01-intake",
                owner_team="platform-ops",
                outcome="success",
                rerun_round=i,
                model_resolver=EnvVarModelResolver(),
            )
            sink.append(uc.build())

        reader = JsonlReaderAdapter(self.sink_path)
        events = reader.read_events()
        self.assertEqual(len(events), 3)
        for event in events:
            self.assertIn("event_id", event)
            self.assertEqual(event["emitter"], "local-cli")

    def test_empty_sink_returns_zero_rerun_round(self) -> None:
        reader = JsonlReaderAdapter(self.sink_path)
        self.assertEqual(reader.compute_rerun_round("347", "intake"), 0)


if __name__ == "__main__":
    unittest.main()
