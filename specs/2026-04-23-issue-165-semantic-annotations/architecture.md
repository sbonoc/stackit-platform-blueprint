# Architecture

## Context
- Work item: issue-165-semantic-annotations
- Owner: blueprint maintainer
- Date: 2026-04-23

## Stack and Execution Model
- Backend stack profile: python_scripting_plus_bash (pure Python stdlib; no FastAPI/Pydantic)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent (bounded change within the upgrade plan generation pipeline)

## Problem Statement
- What needs to change and why: `merge-required` plan entries carry only `path` and `reason`. Consumers must read raw diffs or changelogs to understand what changed and what to verify after merging — there is no in-plan guidance. A new `semantic` annotation object is added to `UpgradeEntry` and populated at both `merge-required` creation sites in `upgrade_consumer.py` via static diff analysis (baseline content vs. upgrade source content). The annotation surfaces in `upgrade_plan.json`, `upgrade_summary.md`, and `upgrade_apply.json`.
- Scope boundaries: New standalone module `upgrade_semantic_annotator.py`; `UpgradeEntry` and `ApplyResult` dataclasses in `upgrade_consumer.py` extended; both `merge-required` creation sites updated; summary markdown renderer updated; both JSON schemas updated.
- Out of scope: Source directive chain traversal beyond depth 0; non-shell file type-specific annotations (structural-change fallback applies); reconcile report and postcheck report rendering; new Make targets or CLI flags.

## Bounded Contexts and Responsibilities

### Context A — Annotation logic (`scripts/lib/blueprint/upgrade_semantic_annotator.py`, new)
- Accepts `baseline_content: str` and `source_content: str` for a single file.
- Computes line-by-line diff; applies detection patterns in fixed priority order: `function-added` → `function-removed` → `variable-changed` → `source-directive-added` → `structural-change` (fallback).
- Returns `SemanticAnnotation(kind, description, verification_hints)` (frozen dataclass).
- Raises on unrecoverable encoding error; caller applies per-entry try/except.
- No I/O, no subprocess calls, no global state — pure function.
- Special case: when baseline is absent (additive file path), annotator receives `baseline_content=""` and produces `kind: structural-change` with a fixed "additive file — no ancestor diff available" description.

### Context B — UpgradeEntry / ApplyResult extension (`scripts/lib/blueprint/upgrade_consumer.py`, extended)
- `UpgradeEntry` gains `semantic: SemanticAnnotation | None` field (None for non-merge-required actions).
- 3-way merge creation site (lines ~640–652): calls `annotate(baseline_content, source_content)` inside a per-entry try/except; structural-change fallback on any exception.
- Additive file creation site (lines ~606–622): `baseline_content_available=False`; calls `annotate("", source_content)` which returns structural-change by design.
- `UpgradeEntry.as_dict()` serialises `semantic` as nested dict or omits key if `None`.
- `ApplyResult` gains optional `semantic: SemanticAnnotation | None` carry-through from the corresponding plan entry; serialised in `as_dict()`.
- Plan generation logs annotation coverage: auto-annotated count (kind ≠ structural-change), structural-change fallback count.
- Summary markdown renderer updated to render `semantic.description` and `verification_hints` for each merge-required entry.

### Context C — JSON schema updates
- `scripts/lib/blueprint/schemas/upgrade_plan.schema.json`: optional `semantic` property added to plan entry items (not in `required`).
- `scripts/lib/blueprint/schemas/upgrade_apply.schema.json`: optional `semantic` property added to result items (not in `required`).
- Schema changes are additive and backward-compatible.

### Context D — Test coverage
- New: `tests/blueprint/test_upgrade_semantic_annotator.py` — unit tests for each `kind`, fallback, and error path.
- Extended: `tests/blueprint/test_upgrade_consumer.py` — assert `semantic` present on merge-required entries from both creation sites; plan JSON includes populated `semantic`; summary markdown renders annotations; apply result carries `semantic`.
- New fixtures: `tests/blueprint/fixtures/semantic_annotator/`.

## High-Level Component Design
- Domain layer: `upgrade_semantic_annotator.py` — pure diff analysis logic, accepts explicit inputs, returns structured result.
- Application layer: `upgrade_consumer.py` — orchestrates annotation at plan generation time; merges result into entry dataclass.
- Infrastructure adapters: none — baseline and source content already resolved before annotation call; no new I/O.
- Presentation/API/workflow boundaries: `upgrade_plan.json` artifact; `upgrade_summary.md` artifact; `upgrade_apply.json` artifact.

## Integration and Dependency Edges
- Upstream dependencies: `baseline_content` (resolved from git via `baseline_cache` before entry creation) and `source_content` (read from source path before comparison) — both already available as local variables at both creation sites; no new I/O required.
- Downstream dependencies: `upgrade_plan.json` consumed by preflight, reconcile report, and consumers; `upgrade_summary.md` rendered to terminal and CI; `upgrade_apply.json` consumed by postcheck (`result=merged` entries checked by behavioral gate in #162).
- Data/API/event contracts touched: `upgrade_plan.schema.json` (additive optional `semantic`); `upgrade_apply.schema.json` (additive optional `semantic`).

## Non-Functional Architecture Notes
- Security: Pure static analysis — no subprocess calls, no file content execution. Regex patterns applied to strings only. No network access, no secrets in scope.
- Observability: One log statement per plan generation run reporting annotation coverage counts (auto-annotated vs. structural-change fallback). One warning log per entry where annotator raised an exception.
- Reliability and rollback: Per-entry try/except ensures annotation failures never abort plan generation. Schema additions are optional (not in `required`), so existing consumers ignoring unknown fields are unaffected. Rollback = revert this work item; no schema migration, no persistent state, no consumer repo impact.
- Monitoring/alerting: No new metrics. Existing plan generation artifacts and CI lanes are unaffected.

## Risks and Tradeoffs
- Risk 1: Regex heuristics produce false negatives for complex diffs (large refactors, heredoc-embedded assignments, dynamically constructed function names) — annotation silently falls back to `structural-change`.
- Tradeoff 1: `structural-change` fallback is always actionable and honest; detection coverage can be extended incrementally (new patterns, new file types) without changing the annotation contract or schema. MVP scope accepted; false negatives documented in spec exclusions.
