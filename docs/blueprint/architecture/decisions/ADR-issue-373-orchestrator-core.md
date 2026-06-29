# ADR-issue-373 — Orchestrator Core: Pure-Python Domain/Application Layer (Child 1 of #361)

- Status: proposed
- Date: 2026-06-29
- Deciders: bonos (solo operator)
- Work item: issue #373 — `feature/2026-06-29-issue-373-orchestrator-core`

## Context

Issue #373 is Child 1 of the orchestrator-service decomposition (#361) under the autonomous-software-factory epic (#332). The parent spec decomposes the orchestrator along `architectural-layer` boundaries; this child owns the `domain/application — pure-Python core, no I/O` layer.

The four components in scope (dispatch matrix loader, convergence engine, schema validator, predicate registry) have no external dependencies beyond `pathlib` and `jsonschema`. Authoring them as a distinct child allows:

1. Full unit-test coverage without any infrastructure stub or container.
2. Early lock-down of the typed Python API that #361.2, #361.3, and #361.5 depend on.
3. `agent-ready` at filing time (no blockers — #360 closed 2026-06-03, so all `SKILL.md` `## Required Output Schema` blocks exist).

## Decision

Ship the four core components as a pure-Python importable module at `scripts/lib/factory/orchestrator/core/`. Zero runtime I/O constraint is **non-negotiable** — any I/O in this module would couple it to infrastructure and break the sibling-child isolation contract.

### Component decisions

| Component | Key design decision |
|---|---|
| Dispatch matrix loader | Markdown table parser anchored to the canonical header string; validates skill dirs, expert enums, and predicate names at parse time; fail-fast on any violation |
| Convergence engine | Three separate methods (`parallel_then_merge`, `sequential_lens`, `structured_disagreement`); no global state; naive string-equality dedup for v1 |
| Schema validator | Extracts YAML from `` ```yaml jsonschema `` fenced blocks; compiles draft-07 JSON Schema; returns typed success/failure objects; no write side effects |
| Predicate registry | Dict-based; immutable after first evaluate call; ships `always_true` + `always_false` built-ins; callers register real predicates before passing to loader |

### Predicate field on MatrixRow

`MatrixRow.predicate` is typed `str | None` in Pydantic v2. The literal string `"none"` is coerced to Python `None` by a field validator at parse time. Non-`"none"` strings are registry names validated at load time (not at dispatch time). This decision shifts the error surface from runtime dispatch to startup, matching the loader's fail-fast invariant.

### Why Option A (dict-based predicate registry) over Option B (entry-point registry)

- This child ships only fixture predicates. The first real predicate (`ui-fidelity-or-a11y`) ships in #361.5, which calls `registry.register(...)` before passing the registry to the loader. Entry-point packaging is premature.
- Entry-point registration introduces global installed-package state that complicates test isolation.
- The dict-based API is open-closed: callers add predicates; the registry never changes shape.

## Consequences

- **Positive:** every sibling child (#361.2 emission path, #361.3 work-loop, #361.5 predicate wiring) can depend on a stable typed Python API from day one.
- **Positive:** unit-test suite has no infrastructure stubs — all four components are testable with `pytest` in-process.
- **Neutral:** naive string-equality dedup ships at v1; embedding-based upgrade is tracked in backlog.
- **Negative (accepted):** callers must wire observability — the module surfaces no log lines. This is the intended contract per Clean Architecture (inner layer emits no side effects).

## References

- Parent spec: `specs/2026-06-18-issue-361-orchestrator-service/spec.md` FR-002, FR-003, FR-004, FR-012
- ADR-issue-364-expert-persona-model.md § 4.1 (DispatchTableRow schema), § 4.2 (step02 routing), § 5 (convergence modes)
- `docs/blueprint/autonomous-factory/design-contracts.md` § C3 (C3 matrix), § C7 F-12 (expert_slug sub-enums)
- Issue #361 Notes for Child Intake: fixture-predicate test strategy
