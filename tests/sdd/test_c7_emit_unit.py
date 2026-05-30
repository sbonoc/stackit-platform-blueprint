from __future__ import annotations

import hashlib
import os
import unittest
from pathlib import Path
from unittest.mock import patch

# Import under test (will fail until Slice 2 implementation exists)
from scripts.lib.sdd.c7_emit import (
    EmitC7EventUseCase,
    EnvVarModelResolver,
    LifecycleEvent,
    derive_event_id,
)


class DeriveEventIdTests(unittest.TestCase):
    """FR-004: four-input event_id for local-cli parity with orchestrator hash."""

    def test_four_input_hash_matches_sha256(self) -> None:
        ticket_id = "347"
        phase = "intake"
        rerun_round = 0
        emitter = "local-cli"
        raw = f"{ticket_id}|{phase}|{rerun_round}|{emitter}".encode()
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(derive_event_id(ticket_id, phase, rerun_round, emitter), expected)

    def test_rerun_round_changes_event_id(self) -> None:
        id0 = derive_event_id("347", "implement", 0, "local-cli")
        id1 = derive_event_id("347", "implement", 1, "local-cli")
        self.assertNotEqual(id0, id1)

    def test_emitter_changes_event_id(self) -> None:
        id_local = derive_event_id("347", "intake", 0, "local-cli")
        id_orch = derive_event_id("347", "intake", 0, "orchestrator")
        self.assertNotEqual(id_local, id_orch)

    def test_returns_hex_string_64_chars(self) -> None:
        result = derive_event_id("347", "intake", 0, "local-cli")
        self.assertEqual(len(result), 64)
        int(result, 16)  # raises ValueError if not hex


class EnvVarModelResolverTests(unittest.TestCase):
    """FR-005: priority-ordered model id from env vars."""

    def test_claude_code_model_takes_priority(self) -> None:
        with patch.dict(os.environ, {
            "CLAUDE_CODE_MODEL": "claude-sonnet-4-6",
            "CODEX_MODEL": "gpt-4o",
            "CURSOR_MODEL": "cursor-model",
        }):
            self.assertEqual(EnvVarModelResolver().resolve(), "claude-sonnet-4-6")

    def test_codex_model_second_priority(self) -> None:
        env = {"CODEX_MODEL": "gpt-4o", "CURSOR_MODEL": "cursor-model"}
        with patch.dict(os.environ, env, clear=False):
            # ensure CLAUDE_CODE_MODEL is absent
            env_clean = {k: v for k, v in os.environ.items()
                         if k != "CLAUDE_CODE_MODEL"}
            with patch.dict(os.environ, env_clean, clear=True):
                self.assertEqual(EnvVarModelResolver().resolve(), "gpt-4o")

    def test_cursor_model_third_priority(self) -> None:
        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CLAUDE_CODE_MODEL", "CODEX_MODEL")}
        env_clean["CURSOR_MODEL"] = "cursor-model"
        with patch.dict(os.environ, env_clean, clear=True):
            self.assertEqual(EnvVarModelResolver().resolve(), "cursor-model")

    def test_unknown_sentinel_when_no_env_var(self) -> None:
        env_clean = {k: v for k, v in os.environ.items()
                     if k not in ("CLAUDE_CODE_MODEL", "CODEX_MODEL", "CURSOR_MODEL")}
        with patch.dict(os.environ, env_clean, clear=True):
            self.assertEqual(EnvVarModelResolver().resolve(), "unknown")


class LifecycleEventSchemaTests(unittest.TestCase):
    """FR-002, AC-002: envelope passes JSON Schema validation."""

    def _make_event(self, **overrides: object) -> LifecycleEvent:
        defaults = dict(
            event_id="abc123",
            ticket_id="347",
            parent_ticket_id=None,
            phase="intake",
            persona="blueprint-sdd-step01-intake",
            model="unknown",
            timestamp="2026-05-30T00:00:00Z",
            outcome="success",
            rerun_round=0,
            owner_team="platform-ops",
            emitter="local-cli",
        )
        defaults.update(overrides)
        return LifecycleEvent(**defaults)

    def test_all_eleven_required_fields_present(self) -> None:
        event = self._make_event()
        data = event.model_dump()
        required = {
            "event_id", "ticket_id", "parent_ticket_id", "phase", "persona",
            "model", "timestamp", "outcome", "rerun_round", "owner_team", "emitter",
        }
        for field in required:
            self.assertIn(field, data, f"Missing required field: {field}")

    def test_event_passes_jsonschema_validation(self) -> None:
        import json
        import jsonschema
        from tests._shared.helpers import REPO_ROOT

        schema_src = (
            REPO_ROOT / "docs/blueprint/autonomous-factory/design-contracts.md"
        ).read_text(encoding="utf-8")
        # Extract the JSON schema block
        import re
        match = re.search(r"```json\n(\{.*?\"FactoryLifecycleEventV1\".*?\})\n```",
                          schema_src, re.DOTALL)
        self.assertIsNotNone(match, "Could not find JSON schema in design-contracts.md")
        schema = json.loads(match.group(1))

        event = self._make_event()
        data = event.model_dump(exclude_none=False)
        jsonschema.validate(data, schema)  # raises if invalid

    def test_execution_mode_extension_field_accepted(self) -> None:
        event = self._make_event()
        data = event.model_dump()
        data["execution_mode"] = "human-assisted"
        # schema has additionalProperties: true — should not raise
        import json
        import jsonschema
        from tests._shared.helpers import REPO_ROOT
        import re
        schema_src = (
            REPO_ROOT / "docs/blueprint/autonomous-factory/design-contracts.md"
        ).read_text(encoding="utf-8")
        match = re.search(r"```json\n(\{.*?\"FactoryLifecycleEventV1\".*?\})\n```",
                          schema_src, re.DOTALL)
        schema = json.loads(match.group(1))
        jsonschema.validate(data, schema)  # must not raise

    def test_emitter_local_cli_is_valid_enum_value(self) -> None:
        event = self._make_event(emitter="local-cli")
        self.assertEqual(event.emitter, "local-cli")


class EmitC7EventUseCaseTests(unittest.TestCase):
    """FR-002: use case produces a schema-valid envelope."""

    def test_emit_returns_lifecycle_event(self) -> None:
        use_case = EmitC7EventUseCase(
            ticket_id="347",
            phase="intake",
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=0,
            model_resolver=EnvVarModelResolver(),
        )
        event = use_case.build()
        self.assertIsInstance(event, LifecycleEvent)

    def test_emit_event_id_matches_derivation(self) -> None:
        use_case = EmitC7EventUseCase(
            ticket_id="347",
            phase="intake",
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=0,
            model_resolver=EnvVarModelResolver(),
        )
        event = use_case.build()
        expected_id = derive_event_id("347", "intake", 0, "local-cli")
        self.assertEqual(event.event_id, expected_id)

    def test_emit_persona_is_skill_basename(self) -> None:
        use_case = EmitC7EventUseCase(
            ticket_id="347",
            phase="implement",
            skill_basename="blueprint-sdd-step05-implement",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=0,
            model_resolver=EnvVarModelResolver(),
        )
        event = use_case.build()
        self.assertEqual(event.persona, "blueprint-sdd-step05-implement")

    def test_emit_emitter_is_local_cli(self) -> None:
        use_case = EmitC7EventUseCase(
            ticket_id="347",
            phase="intake",
            skill_basename="blueprint-sdd-step01-intake",
            owner_team="platform-ops",
            outcome="success",
            rerun_round=0,
            model_resolver=EnvVarModelResolver(),
        )
        event = use_case.build()
        self.assertEqual(event.emitter, "local-cli")


if __name__ == "__main__":
    unittest.main()
