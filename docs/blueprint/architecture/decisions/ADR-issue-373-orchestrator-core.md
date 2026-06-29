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
| Dispatch matrix loader | Markdown table parser anchored to the canonical header string; validates skill dirs, expert enums, predicate names, AND that every expert in `expert_panel` has a corresponding entry in `model_per_expert`; fail-fast on any violation. `extension_allowlist` is supplied by the caller (loader performs no contract.yaml I/O). |
| Convergence engine | Three separate methods (`parallel_then_merge`, `sequential_lens`, `structured_disagreement`); no global state. `parallel_then_merge` annotates findings with source `expert_slug` from the verdict envelope (ADR-364 § 5.1 step 2), applies naive string-equality dedup with `co_reporters` carry-forward (step 3), severity escalation (step 4), and stable sort `(severity desc, category asc, expert_slug asc)` (step 5). `MergeResult.findings` returns the deduped + sorted payload (not just counts) so #361.2 has the C7 `evidence_uri` artifact body. `structured_disagreement` accepts the `MergeResult` from a prior `parallel_then_merge` and returns `ConflictPair` rows naming the colliding experts and shared category. |
| Schema validator | Extracts YAML from `` ```yaml jsonschema `` fenced blocks; compiles draft-07 JSON Schema; returns typed success/failure objects; no write side effects |
| Predicate registry | Dict-based; immutable after first evaluate call; ships `always_true` + `always_false` built-ins; callers register real predicates before passing to loader. `WorkItemContext` model uses `extra="allow"` so downstream predicates (e.g., #361.5's `ui-fidelity-or-a11y`) can extend the context without amending this child's exported schema. |

### Public API surface — Pydantic v2 models

The module exports `MatrixRow`, `Finding`, `ExpertVerdict`, `MergeResult`, `LensDelta`, `ConflictPair`, `StructuredDisagreementResult`, `WorkItemContext`, `ValidationSuccess`, `ValidationFailure`, plus four exception types. Field sets are locked in the spec § Data Models section and are the authoritative contract for sibling children. Why this matters: each sibling (#361.2 emission, #361.3 work-loop, #361.5 predicate wiring) constructs these models to interact with the core. Leaving any model under-specified would force a sibling to either re-invent the schema (drift) or come back to amend this child's API (a breaking change after merge). Locking the schemas HERE is the contract this child exists to deliver.

### Provenance preservation through merge

ADR-364 § 5.1 step 2 mandates that the merger preserves each finding's `expert_slug` provenance. The incoming `ExpertVerdict.findings[]` per § 6 schema do NOT carry `expert_slug` (the schema omits it from the Finding object); the merger MUST add it from the verdict envelope before any other merge step. Without this, downstream Brain (#343) Journey A queries ("which expert raised finding X") cannot be answered. The `co_reporters: list[str]` field (also added by the merger during dedup per § 5.1 step 3) preserves co-attribution when duplicates collapse.

### `model_per_expert` carried on MatrixRow

ADR-364 § 4.1's `DispatchTableRow` schema includes `model_per_expert` as a required field. #361.2's C7 emitter populates `outcome_details.routing_keys[]` (per the parent spec routing-key emission requirement) from this map. If the loader omitted the field, #361.2 would need a second C3 parser — violating parent FR-002's "MUST NOT hardcode the matrix in service code" rule. The field is locked into MatrixRow here, with loader-side validation that every expert in `expert_panel` has a corresponding routing-key entry.

### Predicate field on MatrixRow

`MatrixRow.predicate` is typed `str | None` in Pydantic v2. The literal string `"none"` is coerced to Python `None` by a field validator at parse time. Non-`"none"` strings are registry names validated at load time (not at dispatch time). This decision shifts the error surface from runtime dispatch to startup, matching the loader's fail-fast invariant.

**Schema gap vs ADR-issue-364 § 4.1:** The `DispatchTableRow` JSON Schema in ADR-364 § 4.1 does not include a `predicate` property. The new `Predicate` column in the C3 matrix is authored by `#361.5` (per parent FR-012), which also carries the `#339` sign-off cycle to amend ADR-364 § 4.1. This child (`#361.1`) implements the `MatrixRow.predicate` field and registry-validation logic in advance; the field is nullable so it is backward-compatible with a matrix that has no `Predicate` column (rows without the column parse as `predicate=None`). ADR-364 § 4.1 amendment is a `#361.5` deliverable.

### Schema validator — two distinct failure paths

`SchemaValidator` distinguishes two failure paths to avoid the raise-then-return contradiction:

- **Parse/compile failure** (missing fenced block, malformed YAML, invalid schema document): raises `SchemaValidationError(kind=..., detail=..., context=...)`. Caller does not receive a return value.
- **Payload validation failure** (payload does not satisfy the compiled schema): returns `ValidationFailure(skill, evidence_ref, field_path, error_message)`. Does not raise.
- **Success**: returns `ValidationSuccess(skill)`. Does not raise.

The caller (#361.2) handles `SchemaValidationError` by logging the parse/compile failure and raising to the work-loop error handler; it handles `ValidationFailure` by constructing the C7 `outcome: rejected` event with `rejection_reason: schema-validation-failure`.

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
