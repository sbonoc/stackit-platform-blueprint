# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Module scaffold + typed data models
- [ ] T-001 Create `scripts/lib/factory/orchestrator/core/__init__.py` with public API re-exports
- [ ] T-002 Author Pydantic v2 models: `MatrixRow` (with `predicate: str | None` field validator coercing `"none"` → `None`), `WorkItemContext`, `ExpertVerdict`, `LensDelta`, `MergeResult`, `StructuredDisagreementResult`, `ValidationSuccess`, `ValidationFailure`
- [ ] T-003 Author exception types: `DispatchMatrixError`, `SchemaValidationError`, `PredicateRegistryError`, `ConvergenceError` — each with `detail: str` and `context: dict` fields

### Slice 2 — Predicate registry
- [ ] T-004 Implement `PredicateRegistry` with `always_true`/`always_false` built-ins, `register`, `evaluate`, and post-first-evaluate immutability lock

### Slice 3 — Dispatch matrix loader
- [ ] T-005 Author fixture `design-contracts.md` slices: valid 8-step C3 table; variants for fabricated skill basename, fabricated expert slug, fabricated predicate name, valid extension allowlist slug
- [ ] T-006 Implement `DispatchMatrixLoader.load(design_contracts_path, skills_dir, extension_allowlist, registry)` with markdown-table parser, skill-dir validator, expert-enum validator, predicate-name validator; fail-fast on any violation

### Slice 4 — Convergence engine
- [ ] T-007 Author verdict fixtures: mixed pass/revise/block list with duplicate findings; step05 ordered-callables fixture; step08 conflicting block verdicts fixture
- [ ] T-008 Implement `ConvergenceEngine.parallel_then_merge` with precedence table (`block > revise > pass`) and naive string-equality deduplication
- [ ] T-009 Implement `ConvergenceEngine.sequential_lens` with ordered-callable invocation passing each callable's `LensDelta` to the next
- [ ] T-010 Implement `ConvergenceEngine.structured_disagreement` with per-`finding_category` conflict detection and `severity_escalation_events` counter

### Slice 5 — Schema validator
- [ ] T-011 Author `tests/factory/orchestrator/core/fixtures/skill_with_schema/SKILL.md` with a minimal `## Required Output Schema` block declaring one required field
- [ ] T-012 Implement `SchemaValidator.validate(payload, skill_basename, skills_dir)`: fenced-block extractor, draft-07 JSON Schema compiler, `jsonschema.validate()` call, `ValidationSuccess`/`ValidationFailure` branching, `SchemaValidationError` on parse/compile failure

## Test Automation

- [ ] T-101 Write T-101 test: dispatch matrix loader — all five AC-001 sub-cases (fabricated skill, fabricated expert, extension allowlist acceptance, fabricated predicate, live canonical C3 coverage)
- [ ] T-102 Write T-102 test: convergence engine — all three AC-002 sub-cases (parallel-then-merge with block aggregate, sequential-lens invocation order, structured-disagreement escalation count)
- [ ] T-103 Write T-103 test: schema validator — all three AC-003 sub-cases (raises SchemaValidationError, returns ValidationFailure, no stdout/stderr write)
- [ ] T-104 Write T-104 test: predicate registry — all four AC-004 sub-cases (always_true, always_false, predicate="none" coercion, load-time registry miss raises DispatchMatrixError)

## Accessibility Testing (N/A — headless pure-Python library)
- [ ] T-A01 NFR-A11Y-001 declared as N/A in spec.md — confirmed ✓

## Validation and Release Readiness
- [ ] T-201 `uv run python3 -m pytest tests/factory/orchestrator/core/` → 0 failures (all T-101 through T-104 present and passing)
- [ ] T-202 `make quality-sdd-check` → pass
- [ ] T-203 Confirm no stale TODOs or dead code in `scripts/lib/factory/orchestrator/core/` or `tests/factory/orchestrator/core/`
- [ ] T-204 `make docs-build` and `make docs-smoke` → pass
- [ ] T-205 `make quality-hardening-review` → pass

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with T-101–T-104 coverage table, key reviewer files, pytest + quality-sdd-check evidence, rollback notes; confirm `Tracks #361` (NOT `Closes #361`) in PR body
- [ ] P-003 PR description uses canonical template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 `apps-bootstrap` — no-impact (confirmed: no new app lanes)
- [ ] A-002 `apps-smoke` — no-impact
- [ ] A-003 `backend-test-unit` — no-impact (pure library module; tests run via existing pytest suite)
- [ ] A-004 `backend-test-integration` — no-impact
- [ ] A-005 `backend-test-contracts` — no-impact
- [ ] A-006 `backend-test-e2e` — no-impact
- [ ] A-007 `touchpoints-test-unit` — N/A (no frontend stack)
- [ ] A-008 `touchpoints-test-integration` — N/A
- [ ] A-009 `touchpoints-test-contracts` — N/A
- [ ] A-010 `touchpoints-test-e2e` — N/A
- [ ] A-011 `test-unit-all` — no-impact
- [ ] A-012 `test-integration-all` — no-impact
- [ ] A-013 `test-contracts-all` — no-impact
- [ ] A-014 `test-e2e-all-local` — no-impact
- [ ] A-015 `infra-port-forward-start` — N/A (no runtime service)
- [ ] A-016 `infra-port-forward-stop` — N/A
- [ ] A-017 `infra-port-forward-cleanup` — N/A
