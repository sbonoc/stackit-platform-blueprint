from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

_EMITTER = "local-cli"
_EXECUTION_MODE = "human-assisted"
_PHASES = frozenset({
    "intake", "resolve-questions", "spec-complete", "plan-slicer",
    "implement", "document-sync", "pr-packager", "agent-pr-review",
})
_OUTCOMES = frozenset({"success", "rejected", "retried", "human-handoff"})


class LifecycleEvent(BaseModel):
    """C7 eleven-field minimum envelope for local-cli emissions."""

    event_id: str
    ticket_id: str
    parent_ticket_id: Optional[str]
    phase: str
    persona: str
    model: str
    timestamp: str
    outcome: str
    rerun_round: int = Field(ge=0)
    owner_team: str
    emitter: Literal["orchestrator", "webhook-handler", "local-cli"]

    # Extension field (additionalProperties: true permits it)
    execution_mode: Optional[str] = Field(default=None, exclude=False)

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Pure derivation function (FR-004)
# ---------------------------------------------------------------------------

def derive_event_id(ticket_id: str, phase: str, rerun_round: int, emitter: str) -> str:
    raw = f"{ticket_id}|{phase}|{rerun_round}|{emitter}".encode()
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Application layer
# ---------------------------------------------------------------------------

class EnvVarModelResolver:
    """FR-005: resolve model id from env var priority chain."""

    _CHAIN = ("CLAUDE_CODE_MODEL", "CODEX_MODEL", "CURSOR_MODEL")

    def resolve(self) -> str:
        for var in self._CHAIN:
            value = os.environ.get(var)
            if value:
                return value
        return "unknown"


class EmitC7EventUseCase:
    """Build a LifecycleEvent envelope for a single SDD step execution."""

    def __init__(
        self,
        *,
        ticket_id: str,
        phase: str,
        skill_basename: str,
        owner_team: str,
        outcome: str,
        rerun_round: int,
        model_resolver: EnvVarModelResolver,
        parent_ticket_id: Optional[str] = None,
    ) -> None:
        self._ticket_id = ticket_id
        self._phase = phase
        self._skill_basename = skill_basename
        self._owner_team = owner_team
        self._outcome = outcome
        self._rerun_round = rerun_round
        self._model_resolver = model_resolver
        self._parent_ticket_id = parent_ticket_id

    def build(self) -> LifecycleEvent:
        model = self._model_resolver.resolve()
        event_id = derive_event_id(
            self._ticket_id, self._phase, self._rerun_round, _EMITTER
        )
        return LifecycleEvent(
            event_id=event_id,
            ticket_id=self._ticket_id,
            parent_ticket_id=self._parent_ticket_id,
            phase=self._phase,
            persona=self._skill_basename,
            model=model,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            outcome=self._outcome,
            rerun_round=self._rerun_round,
            owner_team=self._owner_team,
            emitter=_EMITTER,
            execution_mode=_EXECUTION_MODE,
        )


# ---------------------------------------------------------------------------
# Infrastructure adapters
# ---------------------------------------------------------------------------

class JsonlSinkAdapter:
    """Append-only writer for artifacts/c7/<slug>.jsonl (FR-003)."""

    def __init__(self, sink_path: Path) -> None:
        self._path = sink_path

    def append(self, event: LifecycleEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.model_dump(exclude_none=False), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


class JsonlReaderAdapter:
    """Read committed events from the local JSONL sink (NFR-OPS-001)."""

    def __init__(self, sink_path: Path) -> None:
        self._path = sink_path

    def read_events(self) -> list[dict]:
        if not self._path.exists():
            return []
        events: list[dict] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
        return events

    def compute_rerun_round(self, ticket_id: str, phase: str) -> int:
        """Return the next rerun_round for (ticket_id, phase) based on prior events."""
        matching = [
            e for e in self.read_events()
            if e.get("ticket_id") == ticket_id and e.get("phase") == phase
            and e.get("emitter") == _EMITTER
        ]
        return len(matching)


# ---------------------------------------------------------------------------
# Opt-out audit use case (FR-007)
# ---------------------------------------------------------------------------

_OPT_OUT_ENV = "BLUEPRINT_SDD_C7_EMIT"
_OPT_OUT_REASON_ENV = "BLUEPRINT_SDD_C7_OPT_OUT_REASON"
_OPT_OUT_PHASE = "c7-emission-opted-out"


class OptOutAuditUseCase:
    """Emit exactly one opt-out audit event per work-item slug when BLUEPRINT_SDD_C7_EMIT=0.

    FR-007: subsequent SDD steps under the same opt-out scope (same work-item
    sink file) MUST NOT re-emit. The reader checks for any prior
    c7-emission-opted-out event in the JSONL sink and no-ops if one is found.
    """

    def __init__(
        self,
        *,
        ticket_id: str,
        phase: str,
        skill_basename: str,
        owner_team: str,
        sink: JsonlSinkAdapter,
        reader: JsonlReaderAdapter,
        model_resolver: EnvVarModelResolver,
    ) -> None:
        self._ticket_id = ticket_id
        self._phase = phase
        self._skill_basename = skill_basename
        self._owner_team = owner_team
        self._sink = sink
        self._reader = reader
        self._model_resolver = model_resolver

    @staticmethod
    def is_opted_out() -> bool:
        return os.environ.get(_OPT_OUT_ENV, "1") == "0"

    def _prior_opt_out_event_exists(self) -> bool:
        for event in self._reader.read_events():
            if (
                event.get("phase") == _OPT_OUT_PHASE
                and event.get("emitter") == _EMITTER
            ):
                return True
        return False

    def emit_audit_event(self) -> None:
        # FR-007: EXACTLY ONE c7-emission-opted-out event per work-item slug.
        if self._prior_opt_out_event_exists():
            return
        model = self._model_resolver.resolve()
        event_id = derive_event_id(
            self._ticket_id, _OPT_OUT_PHASE, 0, _EMITTER
        )
        kwargs: dict = dict(
            event_id=event_id,
            ticket_id=self._ticket_id,
            parent_ticket_id=None,
            phase=_OPT_OUT_PHASE,
            persona=self._skill_basename,
            model=model,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            outcome="rejected",
            rerun_round=0,
            owner_team=self._owner_team,
            emitter=_EMITTER,
            execution_mode=_EXECUTION_MODE,
        )
        reason = os.environ.get(_OPT_OUT_REASON_ENV, "").strip()
        if reason:
            kwargs["opt_out_reason"] = reason
        event = LifecycleEvent(**kwargs)
        self._sink.append(event)
