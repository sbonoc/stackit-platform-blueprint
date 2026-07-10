# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 (clauses a–d incl. model_per_expert validation) | SDD-C-005, SDD-C-024 | — | `architecture.md` § Bounded Contexts (loader) + § High-Level Component Design (class diagram MatrixRow.model_per_expert); ADR-issue-373 § Component decisions + § `model_per_expert` carried on MatrixRow | `scripts/lib/factory/orchestrator/core/loader.py`, `scripts/lib/factory/orchestrator/core/models.py` (MatrixRow) | T-101 (six sub-cases a–f covering skill, expert blueprint enum, extension allowlist accept, step-set, model_per_expert pairing, missing routing-key) | ADR-issue-373-orchestrator-core.md | DispatchMatrixError fields (NFR-OPS-001) |
| FR-002 (three convergence modes + provenance + co_reporters + stable sort) | SDD-C-005 | — | `architecture.md` § High-Level Component Design (class diagram including Finding/MergeResult/ConflictPair); ADR-issue-373 § Component decisions + § Provenance preservation through merge | `scripts/lib/factory/orchestrator/core/convergence.py`, `scripts/lib/factory/orchestrator/core/models.py` (Finding, ExpertVerdict, MergeResult, LensDelta, ConflictPair, StructuredDisagreementResult) | T-102 (three sub-cases a–c covering parallel-then-merge with expert_slug provenance + co_reporters + stable sort, sequential-lens immutability, structured-disagreement ConflictPair shape) | ADR-issue-373-orchestrator-core.md | ConvergenceError (NFR-OPS-001) |
| FR-003 (two failure paths: parse/compile raises, validation returns) | SDD-C-005, SDD-C-024 | — | `architecture.md` § Bounded Contexts (schema validator); ADR-issue-373 § Schema validator — two distinct failure paths | `scripts/lib/factory/orchestrator/core/validator.py` | T-103 (four sub-cases a–d covering schema-block-missing raise, payload validation return, success return, no-stdout/stderr/file-write assertion) | ADR-issue-373-orchestrator-core.md | SchemaValidationError fields (NFR-OPS-001) |
| FR-004 (predicate registry + MatrixRow.predicate coercion) | SDD-C-005 | — | `architecture.md` § Bounded Contexts (predicate registry); ADR-issue-373 § Predicate field on MatrixRow | `scripts/lib/factory/orchestrator/core/predicates.py`, `scripts/lib/factory/orchestrator/core/models.py` (WorkItemContext, MatrixRow.predicate field validator) | T-104 (five sub-cases a–e covering always_true/false, none coercion, load-time registry hit, load-time registry miss raises DispatchMatrixError) | ADR-issue-373-orchestrator-core.md | PredicateRegistryError fields (NFR-OPS-001) |
| NFR-SEC-001 | SDD-C-009 | — | `architecture.md` § Non-Functional Architecture Notes (Security) | All core module files — no credential/env/network access; only `design-contracts.md` + `.agents/skills/*/SKILL.md` reads | T-103(d) (no-write assertion patches builtins.open/sys.stdout/sys.stderr) | ADR-issue-373 § Consequences | N/A |
| NFR-OBS-001 | SDD-C-010 | — | `architecture.md` § Non-Functional Architecture Notes (Observability) | `scripts/lib/factory/orchestrator/core/exceptions.py` (DispatchMatrixError, SchemaValidationError, PredicateRegistryError, ConvergenceError each carry `detail: str` + `context: dict`) | T-103(d) (no stdout/stderr/file write) | ADR-issue-373 § Consequences | Caller (#361.2) owns log/metric emission per spec § Data Models exception block |
| NFR-REL-001 | SDD-C-011 | — | `architecture.md` § Non-Functional Architecture Notes (Reliability) | Loader fail-fast in `loader.py`; `_locked` flag in `predicates.py`; idempotent `validate()` in `validator.py` | T-101(a, f) (fail-fast on first violation), T-104 (immutability after first evaluate) | ADR-issue-373 § Consequences | N/A |
| NFR-OPS-001 | SDD-C-010 | — | `architecture.md` § Non-Functional Architecture Notes (Monitoring) | `context: dict` field on all four exception types + SchemaValidationError.kind: Literal[...] | T-101 (exception context with failing step/value), T-104 (registered_names list on PredicateRegistryError) | ADR-issue-373 § Consequences | Operator diagnostic routing |
| NFR-A11Y-001 | — | N/A | N/A — headless library | N/A | T-A01 (N/A confirmed in tasks.md) | N/A | N/A |
| AC-001 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (loader) | `scripts/lib/factory/orchestrator/core/loader.py` | `tests/factory/orchestrator/core/test_loader.py::T-101` | — | — |
| AC-002 | SDD-C-012 | — | `architecture.md` § High-Level Component Design | `scripts/lib/factory/orchestrator/core/convergence.py` | `tests/factory/orchestrator/core/test_convergence.py::T-102` | — | — |
| AC-003 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (schema validator) | `scripts/lib/factory/orchestrator/core/validator.py` | `tests/factory/orchestrator/core/test_validator.py::T-103` | — | — |
| AC-004 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (predicate registry) | `scripts/lib/factory/orchestrator/core/predicates.py` | `tests/factory/orchestrator/core/test_predicates.py::T-104` | — | — |

## Public API surface coverage (locked Pydantic v2 models — spec § Data Models)

The following Pydantic v2 models are imported and constructed by sibling children (#361.2 emission, #361.3 work-loop, #361.5 predicate wiring). They are this child's public API contract; drift on their field sets is a breaking change for siblings.

| Model | Defined in | Tested by | Linked from |
|---|---|---|---|
| `MatrixRow` | spec § Data Models; impl `models.py` | T-101(a–f), T-104(c) (predicate field coercion) | FR-001, FR-004 |
| `Finding` | spec § Data Models; impl `models.py` | T-102(a) (expert_slug + co_reporters + stable sort) | FR-002 |
| `ExpertVerdict` | spec § Data Models; impl `models.py` | T-102(a) (verdict envelope provenance source) | FR-002 |
| `MergeResult` | spec § Data Models; impl `models.py` | T-102(a) (all five fields) | FR-002 |
| `LensDelta` | spec § Data Models; impl `models.py` | T-102(b) (immutability across sequential rounds) | FR-002 |
| `ConflictPair` | spec § Data Models; impl `models.py` | T-102(c) (expert_a/expert_b lex sort + category) | FR-002 |
| `StructuredDisagreementResult` | spec § Data Models; impl `models.py` | T-102(c) (all three fields) | FR-002 |
| `WorkItemContext` (extra="allow") | spec § Data Models; impl `models.py` | T-104(a, b) (changed_paths + has_user_facing_flow) | FR-004 |
| `ValidationSuccess` / `ValidationFailure` | spec FR-003 + § Data Models; impl `models.py` | T-103(b, c) | FR-003 |
| Exception family (`DispatchMatrixError`, `SchemaValidationError`, `PredicateRegistryError`, `ConvergenceError`) | spec § Data Models; impl `exceptions.py` | T-101, T-103, T-104 (context/detail field assertions) | NFR-OBS-001, NFR-OPS-001 |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Every public Pydantic v2 model from § Data Models MUST have a `DataModel` node in `graph.json` with edges from the FR(s) that introduce it.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004
  - MODEL-MatrixRow, MODEL-Finding, MODEL-ExpertVerdict, MODEL-MergeResult, MODEL-LensDelta, MODEL-ConflictPair, MODEL-StructuredDisagreementResult, MODEL-WorkItemContext

## Validation Summary
- Required bundles executed: `make quality-sdd-check` — pass (post-intake state; implementation gates run at step05+)
- Result summary: spec/ADR/architecture/traceability/graph artifacts validate against the readiness gate; zero open clarification markers; SPEC_READY/SPEC_PRODUCT_READY remain `false` per intake gate
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Embedding-based deduplication — tracked in backlog `proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation`.
- Follow-up 2: `WorkItemContext.extra="allow"` extensibility — #361.5's `ui-fidelity-or-a11y` predicate is expected to extend the context; if it adds required (non-optional) fields, those become a new constraint on every other predicate consumer and should be documented in #361.5's spec.
- Follow-up 3: `MatrixRow.predicate` parsing depends on the `Predicate` column in C3 being authored by #361.5; this child's loader treats `predicate=None` for rows without the column (backward-compatible). If #361.5 ships before this child merges, no action needed; if it slips, this child still loads cleanly against the pre-amendment C3.
