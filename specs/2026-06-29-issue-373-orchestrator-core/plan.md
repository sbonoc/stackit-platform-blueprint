# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Zero-I/O constraint is the simplicity anchor — if any component needs a network call or env-secret read, it belongs in a sibling child, not here.
  - Four discrete components; no shared mutable state between them.
- Anti-abstraction gate:
  - Use `pathlib.Path.read_text()` directly — no I/O abstraction layer.
  - Use `jsonschema.validate()` directly — no wrapper around the validator.
  - Pydantic v2 models for `MatrixRow`, `WorkItemContext`, `ExpertVerdict`, `MergeResult` — use Pydantic's built-in coercion, not hand-rolled casting.
- Integration-first testing gate:
  - T-101 (loader contract) and T-104 (predicate registry) MUST be written as failing tests before the loader and registry are implemented.
  - Fixture `design-contracts.md` slices (valid + invalid rows) authored before production code.
- Positive-path filter/transform test gate:
  - The loader MUST have at least one test that asserts a matrix row with a valid `expert_slug_extension` value in the allowlist is ACCEPTED (not rejected), with the returned `MatrixRow.predicate` populated correctly.
  - The convergence engine MUST have at least one test that asserts a `parallel_then_merge` call with a `pass` verdict in the list returns a non-empty `MergeResult.aggregate_verdict` (not an empty or null result).
- Finding-to-test translation gate:
  - Any pre-PR finding from `make quality-sdd-check` or `uv run python3 -m pytest` MUST be translated to a failing test before the fix is authored.

## Delivery Slices

### Slice 1: Module scaffold + typed data models (red)
1. Create `scripts/lib/factory/orchestrator/core/__init__.py` with public re-exports.
2. Author Pydantic v2 models: `MatrixRow`, `WorkItemContext`, `ExpertVerdict`, `LensDelta`, `MergeResult`, `StructuredDisagreementResult`, `ValidationSuccess`, `ValidationFailure`.
3. Author exception types: `DispatchMatrixError`, `SchemaValidationError`, `PredicateRegistryError`, `ConvergenceError`.
4. Write failing tests for all models (field types, `predicate="none"` → `None` coercion, required field presence).
5. Gate: `uv run python3 -m pytest tests/factory/orchestrator/core/test_models.py` → all fail.

### Slice 2: Predicate registry (red → green)
1. Write failing T-104 assertions (always_true/false, immutability after first evaluate, PredicateRegistryError on unknown name).
2. Implement `PredicateRegistry`: dict store, lock flag, built-ins registered at `__init__`, `register`/`evaluate` methods.
3. Gate: T-104 passes.

### Slice 3: Dispatch matrix loader (red → green)
1. Author fixture `design-contracts.md` slices: one valid C3 table covering all 8 steps; variants with fabricated skill, fabricated expert slug, fabricated predicate name, valid extension allowlist slug.
2. Write failing T-101 assertions (all five AC-001 sub-cases).
3. Implement `DispatchMatrixLoader`: markdown table parser, skill-dir validator, expert-enum validator, predicate-name validator.
4. Gate: T-101 passes.

### Slice 4: Convergence engine (red → green)
1. Author verdict fixtures: pass/revise/block combinations with duplicate and non-duplicate finding texts; step05 ordered callables fixture; step08 conflicting block verdicts fixture.
2. Write failing T-102 assertions (all three AC-002 sub-cases).
3. Implement `ConvergenceEngine`: `parallel_then_merge` with precedence table and string-equality dedup; `sequential_lens` with delta-passing loop; `structured_disagreement` with category-conflict detection.
4. Gate: T-102 passes.

### Slice 5: Schema validator (red → green)
1. Author `tests/factory/orchestrator/core/fixtures/skill_with_schema/SKILL.md` containing a minimal `## Required Output Schema` block with a required field.
2. Write failing T-103 assertions (all three AC-003 sub-cases including stdout/stderr non-write assertion).
3. Implement `SchemaValidator`: `SKILL.md` reader, fenced-block extractor, JSON Schema compiler, `jsonschema.validate()` call, result branching.
4. Gate: T-103 passes.

### Slice 6: Quality gate pass
1. `uv run python3 -m pytest tests/factory/orchestrator/core/` → 0 failures, all T-101 through T-104 present.
2. `make quality-sdd-check` → pass.
3. Fix any violations before opening the Draft PR.

## Change Strategy
- Migration/rollout sequence: Pure new module; no existing code path is modified. Sibling children (#361.2, #361.3, #361.5) import after this child merges.
- Backward compatibility policy: N/A — no prior version exists.
- Rollback plan: N/A — pure new module; removal is a single `git rm -r scripts/lib/factory/orchestrator/core/` and `git rm -r tests/factory/orchestrator/core/`.

## Validation Strategy (Shift-Left)
- Unit checks: `uv run python3 -m pytest tests/factory/orchestrator/core/` — covers T-101 through T-104. Run per slice.
- Contract checks: T-101 asserts the loader accepts the live canonical `design-contracts.md` § C3 without raising — this is a contract test against the real source file.
- Integration checks: None in this child — zero I/O; no infrastructure stubs needed.
- E2E checks: N/A — no user-facing flow.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: This work item adds a pure-Python library module and test suite; no new Make targets are introduced.

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR-issue-373-orchestrator-core.md (authored at intake, Status: accepted at SPEC_READY).
- Consumer docs updates: None — this is a platform-internal library module; no consumer doc surface.
- Mermaid diagrams updated: Class diagram in `architecture.md` and flowchart in `architecture.md` (authored at intake).
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - Not applicable — this child introduces no HTTP routes, filter logic, or new API endpoints.
- Publish checklist:
  - include requirement/contract coverage (T-101 through T-104 coverage table)
  - include key reviewer files (`scripts/lib/factory/orchestrator/core/`, `tests/factory/orchestrator/core/`)
  - include validation evidence (pytest output + `make quality-sdd-check` pass)
  - include rollback notes

## Operational Readiness
- Logging/metrics/traces: None at this layer — all observability delegated to caller per NFR-OBS-001.
- Alerts/ownership: N/A — pure library module.
- Runbook updates: None — operator runbook for the orchestrator service is scoped to #361.3 (per parent FR-010 / `docs/blueprint/autonomous-factory/orchestrator.md` authoring).

## Risks and Mitigations
- Risk 1 — C3 table format drift → the loader's markdown parser breaks silently: mitigation — T-101 clause (d) asserts the loader accepts the LIVE canonical `design-contracts.md` § C3 without raising; this test runs against the real file and will fail immediately if anyone reformats the table header or breaks alignment.
- Risk 2 — `## Required Output Schema` fenced block absent from a future SKILL.md: mitigation — `SchemaValidationError` distinguishes `schema-block-missing` parse failure from `schema-validation-failed` validation failure; T-103 asserts both error cases with distinguishable error messages.
