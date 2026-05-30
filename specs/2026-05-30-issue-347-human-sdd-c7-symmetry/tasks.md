# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [x] G-002 Confirm open questions and unresolved alternatives are `0`
- [x] G-003 Confirm required sign-offs are approved (Product, Architecture, Security, Operations)
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation

### Slice 1 — Contract amendment + ADR
- [x] T-001 Amend `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 § Emission mechanism: widen `emitter` JSON Schema enum to `{orchestrator, webhook-handler, local-cli}`; widen FR-019 two-emitter prose to three-emitter prose; extend `persona.description` with `local-cli` skill-basename sentinel rule; extend `model.description` with `local-cli` best-effort-or-`unknown` sentinel rule; document `execution_mode` extension field vocabulary; document four-input `event_id` derivation for `local-cli`.
- [x] T-002 Re-sync bootstrap mirror `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` via `python3 scripts/lib/docs/sync_blueprint_template_docs.py`.
- [x] T-003 Annotate `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` § Local execution exemption with one-line "Extended by [`ADR-issue-347-human-sdd-c7-symmetry.md`](ADR-issue-347-human-sdd-c7-symmetry.md)" pointer.
- [x] T-004 Advance `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` Status from `proposed` to `accepted` on merge (last commit before PR ready-for-review).

### Slice 2 — Helper module + CLI + unit tests
- [x] T-010 Create `scripts/lib/sdd/c7_emit.py` with Pydantic v2 `LifecycleEvent` model (eleven required fields + `execution_mode` extension), `EmitC7EventUseCase`, `EnvVarModelResolver` (priority chain: `$CLAUDE_CODE_MODEL` → `$CODEX_MODEL` → `$CURSOR_MODEL` → `unknown` sentinel), and `event_id` derivation function (`sha256(ticket_id|phase|rerun_round|emitter)`).
- [x] T-011 Create `scripts/bin/sdd/c7_emit.py` CLI entrypoint exposing `emit --phase <enum> --skill <basename> [--outcome <enum>] [--ticket <id>]`.
- [x] T-012 Add `tests/sdd/test_c7_emit_unit.py` asserting envelope construction, env-var model resolver priority, `event_id` derivation byte-for-byte parity with the orchestrator's hash format.

### Slice 3 — JSONL sink + opt-out audit + contract tests
- [x] T-020 Implement `JsonlSinkAdapter` (`O_APPEND` semantics, creates `artifacts/c7/` on first write).
- [x] T-021 Implement `JsonlReaderAdapter` (reads prior committed events for `rerun_round` computation; tolerates missing file → returns 0).
- [x] T-022 Implement `OptOutAuditUseCase` (checks `BLUEPRINT_SDD_C7_EMIT=0`; on first invocation per work-item slug emits EXACTLY ONE `c7-emission-opted-out` extension event with `opt_out_reason` from `BLUEPRINT_SDD_C7_OPT_OUT_REASON` env var; subsequent invocations no-op).
- [x] T-023 Add `tests/sdd/test_c7_emit_contract.py` asserting every emitted envelope validates against the C7 JSON Schema (using `jsonschema` library); round-trip JSON parse preserves all eleven required fields + `execution_mode`.
- [x] T-024 Add `tests/sdd/test_c7_emit_opt_out.py` asserting opt-out path emits EXACTLY ONE `c7-emission-opted-out` extension event per work-item slug.
- [x] T-025 Add `tests/sdd/test_c7_emit_jsonl_round_trip.py` asserting `rerun_round` increments correctly across 10 sequential emissions for the same `(ticket_id, phase)` tuple.

### Slice 4 — Skill addendum + `.gitattributes` + pre-commit + `contract.yaml`
- [x] T-030 Add uniform "## C7 Emission" section (identical text modulo per-skill `phase` enum value) to all seven `.agents/skills/blueprint-sdd-stepXX-*/SKILL.md` runbooks.
- [x] T-031 Extend `scripts/bin/quality/check_sdd_assets.py` with a SKILL.md structural integrity scanner (FR-015): (a) assert every `.agents/skills/*/SKILL.md` contains `## Guardrails`, `## Workflow`, and `## Required Report Format`; (b) assert the "## C7 Emission" addendum is byte-identical (modulo per-skill `phase` enum value) across all seven `blueprint-sdd-step*/SKILL.md` files. Both checks run under the existing `make quality-sdd-check` target. Incorporates parked proposal `issue-247-step05-slice-done-gate`.
- [x] T-032 Add `.gitattributes` rule `artifacts/c7/*.jsonl  linguist-generated=true  diff=none`.
- [x] T-033 Add pre-commit hook entry in `.pre-commit-config.yaml` that schema-validates `artifacts/c7/<slug>.jsonl` on commit (uses the helper's schema-validation function).
- [x] T-034 Add `spec.spec_driven_development_contract.c7_emission` block to `blueprint/contract.yaml` declaring `BLUEPRINT_SDD_C7_EMIT` default + opt-out audit rule + JSONL sink path convention.

### Slice 5 — Docs sync + governance guide
- [x] T-052 Update `docs/blueprint/governance/sdd_execution_guide.md` with a new "## C7 Emission for Local SDD Sessions" section documenting `BLUEPRINT_SDD_C7_EMIT` env var, JSONL sink path, opt-out audit behavior, `rerun_round` semantics. MUST note that subscriber-side ingest onto the durable bus is delivered by follow-up issue #350 (blocked by #336).
- [x] T-053 Re-sync bootstrap mirror `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/sdd_execution_guide.md` via the docs-sync helper.
- [x] T-054 Add uniform addendum to consumer-side skill templates `scripts/templates/consumer/init/.agents/skills/blueprint-sdd-stepXX-*/SKILL.md.tmpl` (all seven).

> Deferred to follow-up issue #350 (blocked by #336): T-040..T-043 (#336 webhook handler ingest + integration test) and T-050..T-051 (FR-008 `unknown`-model exemption). PR #348 ships the producer side only; the subscriber side ships when #336 runtime exists.

### Cross-cutting
- [x] T-060 Verify design-contracts.md + ADR + sdd_execution_guide.md C7 section completeness (covered by T-001, T-011, T-052)
- [x] T-061 Verify consumer bootstrap mirrors + consumer skill templates reflect C7 addendum (covered by T-002, T-053, T-054)

## Test Automation
- [x] T-101 Unit tests: `tests/sdd/test_c7_emit_unit.py` + `tests/sdd/test_c7_emit_opt_out.py` (covered by T-012 + T-024)
- [x] T-102 Contract tests: `tests/sdd/test_c7_emit_contract.py` + `tests/sdd/test_c7_emit_jsonl_round_trip.py` (covered by T-023 + T-025)
- [x] T-103 Positive-path filter test: helper schema-validation function MUST return the parsed record (not just `True`/`False`) when an envelope is well-formed; unit test asserts the returned record preserves all eleven required fields + `execution_mode`. Evidence captured in `pr_context.md`.
- [x] T-104 Translate any reproducible pre-PR finding from manual `python3 scripts/bin/sdd/c7_emit.py emit ...` rehearsal into a failing pytest first; fix in same work item.

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 declared in `spec.md` as "N/A — this work item adds no UI surface."
- [x] T-A02 N/A — no UI surface; no axe-core scan required.
- [x] T-A03 N/A — no UI surface; no keyboard operability required.
- [x] T-A04 N/A — no UI surface; no focus indicator required.
- [x] T-A05 N/A — no UI surface; no programmatic label required.

## Validation and Release Readiness
- [x] T-201 Run required Make validation bundles: `make quality-sdd-check`, `make quality-hooks-run`, `make docs-build`, `make docs-smoke`. All MUST be green.
- [x] T-202 Attach validation evidence to `traceability.md` (per-FR SHA references, pytest output summary, docs validation summary).
- [x] T-203 Confirm no stale TODOs / dead code / drift. Run `scripts/bin/quality/check_sdd_assets.py` to confirm zero drift on the uniform addendum.
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`).
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`).

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section.
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence (incl. manual rehearsal screenshot for AC-005), and rollback notes.
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`.

## App Onboarding Minimum Targets (Normative)
- [x] A-001 `apps-bootstrap` — N/A: tooling-only work item; existing target unmodified
- [x] A-002 `apps-smoke` — N/A: tooling-only work item; existing target unmodified
- [x] A-003 Backend app lanes — `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — N/A: no app code changes
- [x] A-004 Frontend app lanes — `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — N/A: no frontend changes
- [x] A-005 Aggregate gates — `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — N/A: no app code changes
- [x] A-006 Port-forward wrappers — `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — N/A: no new port-forward targets
