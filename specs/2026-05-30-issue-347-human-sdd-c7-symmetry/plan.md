# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - Single deterministic helper module (`scripts/lib/sdd/c7_emit.py`) + thin CLI entrypoint; no plugin architecture, no abstract emitter base class.
  - Uniform addendum text across seven skills (one string, seven Edit calls); no per-skill customization.
- Anti-abstraction gate:
  - Helper writes JSON Lines directly via `json.dumps`; no event-bus client library, no message-broker SDK.
  - Pydantic v2 model is one class with eleven fields + the extension; no inheritance hierarchy for the two emitter variants.
- Integration-first testing gate:
  - Contract tests assert the helper output validates against the C7 JSON Schema (using `jsonschema` library) — written BEFORE the helper implementation.
  - Note: #336 ingest integration test is deferred to follow-up #350 (blocked by #336 runtime).
- Positive-path filter/transform test gate:
  - Helper schema validation is filter logic — unit test MUST assert that a well-formed envelope returns the parsed record AND that the parsed record preserves all eleven required fields. Empty-result assertions MUST NOT satisfy this gate.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding from manual `python3 scripts/bin/sdd/c7_emit.py emit ...` invocations MUST be translated into a failing pytest test first; the fix MUST turn that test green in the same work item.
  - If no deterministic automation path exists for a finding, publish artifacts MUST record the exception rationale, owner, and follow-up trigger.

## Delivery Slices

1. **Slice 1 — Contract amendment + ADR (no runtime code).** Red: add a failing assertion in `tests/blueprint/test_design_contracts_schema.py` that the `emitter` enum contains `local-cli`. Green: amend `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C7 to widen `emitter.enum`, extend `persona`/`model` descriptions with `local-cli` sentinel rules, document `execution_mode` in the extension-field vocabulary, and document the four-input `event_id` derivation for `local-cli`. Re-sync bootstrap mirror via `scripts/lib/docs/sync_blueprint_template_docs.py`. Add the one-line "Extended by" cross-link to `ADR-issue-337-c7-emission-mechanism.md` § Local execution exemption. ADR `ADR-issue-347-human-sdd-c7-symmetry.md` is already authored at Step 01.
2. **Slice 2 — Helper module + CLI + unit tests.** Red: `tests/sdd/test_c7_emit_unit.py` asserts `EmitC7EventUseCase` produces an envelope passing JSON Schema validation; asserts `EnvVarModelResolver` returns priority-ordered model id; asserts `event_id` derivation matches `sha256(ticket_id|phase|rerun_round|emitter)` byte-for-byte. Green: implement `scripts/lib/sdd/c7_emit.py` + `scripts/bin/sdd/c7_emit.py`. Helper exposes CLI `emit --phase --skill [--outcome --ticket]`.
3. **Slice 3 — JSONL sink + opt-out audit + rerun_round + contract tests.** Red: `tests/sdd/test_c7_emit_contract.py` asserts append-only writes, asserts opt-out path emits EXACTLY ONE `c7-emission-opted-out` extension event per work-item slug, asserts `rerun_round` increments based on prior file contents. Green: wire `JsonlSinkAdapter`, `OptOutAuditUseCase`, `JsonlReaderAdapter` into the use-case.
4. **Slice 4 — Skill addendum + `.gitattributes` + pre-commit hook + `blueprint/contract.yaml`.** Red: extend `check_sdd_assets.py` with a uniform-addendum check that asserts the "## C7 Emission" section is byte-identical (modulo phase enum) across all seven step skills; add an `.pre-commit-config.yaml` schema-validation entry for `artifacts/c7/*.jsonl`. Green: add the addendum text via Edit to each of the seven `.agents/skills/blueprint-sdd-step*/SKILL.md`; add the `.gitattributes` rule; add the `c7_emission` block to `blueprint/contract.yaml`. Run the checker and the pre-commit hook to confirm green.
5. **Slice 5 — Docs sync + governance guide update.** Update `docs/blueprint/governance/sdd_execution_guide.md` with a new "## C7 Emission for Local SDD Sessions" section (documents `BLUEPRINT_SDD_C7_EMIT` env var, JSONL sink path, opt-out audit behavior, `rerun_round` semantics; notes subscriber-side ingest deferred to #350). Re-sync bootstrap mirror at `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/sdd_execution_guide.md` via the docs-sync helper. Add uniform "## C7 Emission" addendum to all seven consumer-side skill templates at `scripts/templates/consumer/init/.agents/skills/blueprint-sdd-stepXX-*/SKILL.md.tmpl`.

> **Deferred to follow-up #350** (blocked by #336 runtime): Slice 5 ingest handlers (T-040..T-043) and FR-008 `unknown`-model exemption (T-050..T-051) are out of scope for PR #348.

## Change Strategy
- Migration/rollout sequence:
  1. Merge this PR after sign-offs. The contract surface widens immediately; existing autonomous emissions continue unchanged.
  2. First new work item authored after merge becomes the first emitter under `local-cli`. The operator runs `make spec-scaffold` + the SDD step skills; the helper appends to `artifacts/c7/<slug>.jsonl`; the PR opens with the JSONL committed to the branch.
  3. Grafana dashboard will show `execution_mode: human-assisted` events once follow-up #350 ships the #336 PR-event ingest handlers. Until then the JSONL is committed to branch as the local audit trail.
- Backward compatibility policy: The eleven-field sealed minimum schema is unchanged — no nullable types, no new required field. Existing subscribers continue parsing events without code change; new subscribers wanting the `execution_mode` facet read it from `additionalProperties`. The `emitter` enum widening is additive — subscribers rejecting unknown enum values MUST be updated to accept `local-cli` (validated in Slice 1 contract test).
- Rollback plan: Single revert PR undoes contract amendment, ADR, helper module, CLI, skill addenda, `.gitattributes` rule, pre-commit hook entry, `contract.yaml` block, and #336 handler additions. No data migration is required because no historical JSONL state exists at rollback time. Helper files left on disk on operator workstations are inert without the skill addenda calling them.

## Validation Strategy (Shift-Left)
- Unit checks:
  - `tests/sdd/test_c7_emit_unit.py` — envelope construction, env-var model resolver, `event_id` derivation parity with orchestrator.
  - `tests/sdd/test_c7_emit_opt_out.py` — opt-out audit event emission semantics.
  - `tests/blueprint/test_design_contracts_schema.py` — `emitter` enum widening assertion (Slice 1 red).
- Contract checks:
  - `tests/sdd/test_c7_emit_contract.py` — every emitted envelope MUST validate against the C7 JSON Schema; round-trip through `json.loads(line)` MUST preserve all eleven required fields and `execution_mode`.
  - `scripts/bin/quality/check_sdd_assets.py` — uniform addendum text across seven step skills (Slice 4).
- Integration checks:
  - `tests/sdd/test_c7_emit_jsonl_round_trip.py` — write 10 envelopes via the helper, read them back via `JsonlReaderAdapter`, assert `rerun_round` increments correctly.
  - Note: `tests/webhook_handler/test_pr_event_c7_ingest.py` deferred to follow-up #350.
- E2E checks:
  - Manual rehearsal: on a throwaway test branch, run a full SDD lifecycle (Steps 01–07) on a stub work item; confirm 7 events in `artifacts/c7/<stub-slug>.jsonl`; open Draft PR; confirm JSONL is committed and hidden from PR diff by `.gitattributes`. Capture in `pr_context.md`. Bus/Grafana verification is deferred to #350.

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
- Notes: This work item changes SDD-lifecycle tooling (helper, skill addenda, contract surface, webhook handler). It does NOT add or change app-delivery make targets. Reaffirmed no-impact.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/autonomous-factory/design-contracts.md` — Contract C7 amendments (FR-010 scope).
  - `docs/blueprint/architecture/decisions/ADR-issue-347-human-sdd-c7-symmetry.md` — new ADR (advance Status: proposed → accepted on merge).
  - `docs/blueprint/architecture/decisions/ADR-issue-337-c7-emission-mechanism.md` — one-line "Extended by" cross-link at § Local execution exemption.
  - `docs/blueprint/governance/sdd_execution_guide.md` — document `BLUEPRINT_SDD_C7_EMIT`, JSONL sink path, opt-out audit behavior.
- Consumer docs updates:
  - Bootstrap mirror at `scripts/templates/blueprint/bootstrap/docs/blueprint/autonomous-factory/design-contracts.md` — re-sync.
  - Bootstrap mirror at `scripts/templates/blueprint/bootstrap/docs/blueprint/governance/sdd_execution_guide.md` — re-sync.
  - Consumer-side `scripts/templates/consumer/init/.agents/skills/blueprint-sdd-step01-intake/SKILL.md.tmpl` and the other six step skills' templates — uniform addendum.
- Mermaid diagrams updated:
  - ADR-issue-347 contains one `sequenceDiagram` showing the operator → LLM → skill → helper → JSONL sink → #336 → bus → Central Brain flow.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - This work item adds NO new HTTP routes, NO new query/filter handlers, and NO new public API endpoints. The webhook handler extension adds three new event-type dispatcher branches inside an existing webhook endpoint; this is worker-side processing, not a new HTTP route. Local-smoke gate is N/A.
  - If the implementation slice unexpectedly introduces a new HTTP surface, this section MUST be reopened and the deterministic smoke wrappers (`make infra-provision`, `make infra-deploy`, `make infra-port-forward-start`) MUST be invoked with positive-path `curl` assertions per changed endpoint.
- Publish checklist:
  - include requirement/contract coverage for FR-001..FR-007, FR-010..FR-015, NFR-SEC-001, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-004, AC-006, AC-007 (deferred: subscriber-side requirements tracked in #350)
  - include key reviewer files: design-contracts.md amendment, new ADR + ADR-337 annotation, helper module + CLI, skill addenda, `.gitattributes` rule, pre-commit hook, `contract.yaml` block, `check_sdd_assets.py` extension
  - include validation evidence (pytest unit + contract + round-trip; `make quality-sdd-check`; `make docs-build`; `make docs-smoke`; manual rehearsal screenshot showing 7+ events in JSONL)
  - include rollback notes (single-PR revert; no data migration)

## Operational Readiness
- Logging/metrics/traces:
  - Helper logs to stderr on failure; success path is silent (no log noise per SDD step).
  - Opt-out events (`c7-emission-opted-out`) appear in the local JSONL sink and will surface on Grafana once #350 ships the ingest path.
  - Grafana panel (`execution_mode` facet, `c7-emission-opted-out` panel) and #336 ingest structured logs are delivered by follow-up #350.
- Alerts/ownership:
  - Opt-out rate > 5% alert routes to `@sbonoc/factory-operations`.
  - Helper-failure pre-commit-hook rejections route to operator stderr (no central alert — local-first by design).
- Runbook updates:
  - `docs/blueprint/governance/sdd_execution_guide.md` § (new) "C7 emission for local SDD sessions" documents the JSONL sink path, the env var, the opt-out audit behavior, and the rerun_round semantics.

## Risks and Mitigations
- Risk 1 -> mitigation: Self-bootstrap paradox (this work item authors the helper but cannot use it for its own steps) -> mitigation: documented as explicit exclusion pending Q-3 resolution; emission obligatory from first work item post-merge.
- Risk 2 -> mitigation: Best-effort model ID returns `unknown` sentinel for assistants that do not expose a model env var -> mitigation: the reviewer-heterogeneity audit `unknown`-model exemption (deferred to #350) will mark such pairs `inconclusive` rather than failing; documented in ADR § Decision.
- Risk 3 -> mitigation: Skill addendum text drift across the seven step skills -> mitigation: extend `check_sdd_assets.py` with a byte-identical-modulo-phase-enum check; CI gate fails on drift.
- Risk 4 -> mitigation: Rebase / squash duplicates lines in `artifacts/c7/<slug>.jsonl` -> mitigation: deterministic `event_id` derivation means duplicates are identically-keyed; subscriber-side dedupe (#350) absorbs them; local file is append-only (helper never rewrites).
- Risk 5 -> mitigation: `.gitattributes` `diff=none` rule is per-clone configurable; some reviewers may still see the JSONL in their diff -> mitigation: cosmetic-only; documented in `pr_context.md` as a known edge case.
