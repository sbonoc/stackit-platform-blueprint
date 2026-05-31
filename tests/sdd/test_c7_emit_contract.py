from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts.lib.sdd.c7_emit import (
    EmitC7EventUseCase,
    EnvVarModelResolver,
    JsonlReaderAdapter,
    JsonlSinkAdapter,
    LifecycleEvent,
)
from tests._shared.helpers import REPO_ROOT


def _load_c7_schema() -> dict:
    src = (
        REPO_ROOT / "docs/blueprint/autonomous-factory/design-contracts.md"
    ).read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)```", src, re.DOTALL)
    for block in blocks:
        if "FactoryLifecycleEventV1" in block:
            return json.loads(block)
    raise AssertionError("FactoryLifecycleEventV1 schema not found in design-contracts.md")


def _make_use_case(ticket_id: str, phase: str, rerun_round: int = 0) -> EmitC7EventUseCase:
    return EmitC7EventUseCase(
        ticket_id=ticket_id,
        phase=phase,
        skill_basename=f"blueprint-sdd-step01-intake",
        owner_team="platform-ops",
        outcome="success",
        rerun_round=rerun_round,
        model_resolver=EnvVarModelResolver(),
    )


class ContractValidationTests(unittest.TestCase):
    """AC-002: every emitted envelope MUST validate against C7 JSON Schema."""

    def setUp(self) -> None:
        self.schema = _load_c7_schema()

    def test_emitted_envelope_validates_against_c7_schema(self) -> None:
        import jsonschema
        event = _make_use_case("347", "intake").build()
        data = event.model_dump(exclude_none=False)
        jsonschema.validate(data, self.schema)

    def test_round_trip_preserves_all_eleven_required_fields(self) -> None:
        event = _make_use_case("347", "implement").build()
        serialized = event.model_dump_json()
        restored = json.loads(serialized)
        required = {
            "event_id", "ticket_id", "parent_ticket_id", "phase", "persona",
            "model", "timestamp", "outcome", "rerun_round", "owner_team", "emitter",
        }
        for field in required:
            self.assertIn(field, restored, f"Round-trip dropped required field: {field}")

    def test_execution_mode_preserved_on_round_trip(self) -> None:
        event = _make_use_case("347", "intake").build()
        data = json.loads(event.model_dump_json())
        self.assertEqual(data.get("execution_mode"), "human-assisted")

    def test_emitter_value_is_local_cli(self) -> None:
        event = _make_use_case("347", "intake").build()
        self.assertEqual(event.emitter, "local-cli")


class AppendOnlyWriteTests(unittest.TestCase):
    """FR-003: JsonlSinkAdapter is append-only."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.sink_path = self.tmp / "c7" / "test.jsonl"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_three_appends_produce_three_lines(self) -> None:
        sink = JsonlSinkAdapter(self.sink_path)
        for i in range(3):
            event = _make_use_case("347", "intake", rerun_round=i).build()
            sink.append(event)
        lines = self.sink_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)

    def test_each_line_is_valid_json(self) -> None:
        sink = JsonlSinkAdapter(self.sink_path)
        for i in range(3):
            event = _make_use_case("347", "intake", rerun_round=i).build()
            sink.append(event)
        for line in self.sink_path.read_text(encoding="utf-8").splitlines():
            json.loads(line)  # raises if not valid JSON

    def test_sink_creates_parent_dir(self) -> None:
        deep = self.tmp / "deep" / "nested" / "c7" / "test.jsonl"
        sink = JsonlSinkAdapter(deep)
        event = _make_use_case("347", "intake").build()
        sink.append(event)
        self.assertTrue(deep.exists())


if __name__ == "__main__":
    unittest.main()
