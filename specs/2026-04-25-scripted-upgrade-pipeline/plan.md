# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate: each new script (resolver, coverage fetcher, mirror sync, doc checker, residual reporter) must be independently testable with fixture inputs; no shared global state between stages; the pipeline entry wrapper orchestrates by invoking scripts sequentially with no new framework or abstraction layer
- Anti-abstraction gate: Python stdlib only (no third-party libraries beyond what is already in the repo); bash for the entry wrapper; no wrapper layer around existing make targets — invoke them directly via subprocess/shell
- Integration-first testing gate: contract resolver tests use representative fixture conflict JSON inputs before implementation details; coverage gap detection tests use a minimal fixture consumer directory structure
- Positive-path filter/transform test gate: contract resolver must have at least one unit test asserting that name and repo_mode from consumer input are preserved (not overwritten by source content); empty-result-only assertions do not satisfy this gate — AC-002
- Finding-to-test translation gate: each observed failure mode (F-001–F-010) addressed by a new script stage must have a corresponding unit test asserting the fix; translate into failing tests first, then implement the fix

## Slice Dependency Map

```
Slice 1 ──────────────────────────────────────────┐
Slice 2 ─────────────────────────────────────────┐│
Slice 3 ────────────────────────────────────────┐││   all → Slice 7 → Slice 8
Slice 4 ───────────────────────────────────────┐│││
Slice 5 ──────────────────────────────────────┐││││
Slice 6 ─────────────────────────────────────┘┘┘┘┘
```

- Slices 1–6 have no inter-dependencies and MAY be implemented in parallel.
- Slice 7 (pipeline wiring) MUST start only after Slices 1–6 are complete.
- Slice 8 (validation) MUST start only after Slice 7 is complete.

Owner: sbonoc (all slices).

## Delivery Slices

1. **Slice 1 — Pre-flight validation helper (Stage 1)**
   - Requirements: FR-001, FR-002, FR-003
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Design note: pre-flight checks are extracted into a Python helper (`scripts/lib/blueprint/upgrade_preflight.py`) so they are independently testable via pytest. The bash entry wrapper (`upgrade_consumer.sh`) calls this helper as its first action and exits non-zero if it returns failure. This avoids bash-only unit testing.
   - Output: `scripts/lib/blueprint/upgrade_preflight.py` + stub `scripts/bin/blueprint/upgrade_consumer.sh`
   - Red→green TDD:
     1. Write `TestPreflightDirtyTree`, `TestPreflightInvalidRef`, `TestPreflightBadContract` — all fail (module not yet written).
     2. Implement `upgrade_preflight.py` — tests go green.
     3. Write stub `upgrade_consumer.sh` that calls the helper and exits on failure.
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "preflight"`

2. **Slice 2 — Contract resolver (Stage 3)**
   - Requirements: FR-005, FR-006, FR-007, FR-008; satisfies AC-002
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Output: `scripts/lib/blueprint/resolve_contract_upgrade.py` + fixtures under `tests/blueprint/fixtures/contract_resolver/`
   - Red→green TDD:
     1. Write fixture conflict JSON (consumer identity fields, mixed required_files, prune globs with matching and non-matching paths).
     2. Write `TestContractResolverIdentityPreservation`, `TestContractResolverRequiredFilesMerge`, `TestContractResolverPruneGlobDrop`, `TestContractResolverDecisionJSON` — all fail.
     3. Implement resolver — tests go green. Verify `name` and `repo_mode` preserved (AC-002 positive-path assertion).
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "ContractResolver"`

3. **Slice 3 — Coverage gap detection and file fetch (Stage 5)**
   - Requirements: FR-009, FR-010, NFR-SEC-001; satisfies AC-003
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Output: `scripts/lib/blueprint/upgrade_coverage_fetch.py` + minimal fixture source git repo under `tests/blueprint/fixtures/coverage_fetch/`
   - Red→green TDD:
     1. Write `TestCoverageGapDetection` (contract refs vs disk), `TestCoverageGapFileFetch` (absent file fetched via `git show`), `TestCoverageGapNoHTTP` (assert no http/https subprocess call) — all fail.
     2. Implement fetcher with broad-scope scan (Option B: any contract-referenced path absent from disk is fetched) — tests go green.
     3. Integration test against minimal fixture source repo (validates AC-003 end-to-end).
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "CoverageGap"`

4. **Slice 4 — Bootstrap template mirror sync (Stage 6)**
   - Requirements: FR-011
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Output: `scripts/lib/blueprint/upgrade_mirror_sync.py`
   - Red→green TDD:
     1. Write `TestMirrorSyncOverwrites` (modified workspace file with existing mirror → mirror overwritten), `TestMirrorSyncNoOp` (no mirror at path → no-op) — all fail.
     2. Implement sync — tests go green.
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "MirrorSync"`

5. **Slice 5 — Make target validation for new/changed docs (Stage 7)**
   - Requirements: FR-012
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Output: `scripts/lib/blueprint/upgrade_doc_target_check.py`
   - Red→green TDD:
     1. Write `TestDocTargetCheckKnownTarget` (target present in `.PHONY` → no warning), `TestDocTargetCheckMissingTarget` (target absent → warning in output), `TestDocTargetCheckNoAbort` (missing target → exit 0, not non-zero) — all fail.
     2. Implement checker — tests go green.
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "DocTargetCheck"`

6. **Slice 6 — Residual report (Stage 10)**
   - Requirements: FR-015, FR-016, FR-017, FR-018, FR-019
   - Owner: sbonoc | Depends on: none | Blocks: Slice 7
   - Output: `scripts/lib/blueprint/upgrade_residual_report.py`
   - Red→green TDD:
     1. Write fixture JSON inputs: decision report (dropped required_files, dropped prune globs), reconcile report (consumer-owned files), doc-check warnings (missing targets), pyramid gap list.
     2. Write `TestResidualReportAlwaysEmitted`, `TestResidualReportPrescribedActions`, `TestResidualReportConsumerOwned`, `TestResidualReportPyramidGaps` — all fail.
     3. Implement reporter — tests go green. Every item in output must have a prescribed action string matching FR-016 templates.
     4. Verify existing individual targets (`blueprint-upgrade-consumer-apply`, etc.) remain callable without modification (FR-019 regression guard, AC-006).
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "ResidualReport"`

7. **Slice 7 — Pipeline wiring + Makefile target**
   - Requirements: FR-004, FR-013, FR-014, FR-019, NFR-REL-001, NFR-OPS-001, NFR-OBS-001
   - Owner: sbonoc | Depends on: Slices 1–6 complete | Blocks: Slice 8
   - Output: complete `scripts/bin/blueprint/upgrade_consumer.sh`; `blueprint-upgrade-consumer` target in `make/blueprint.mk`; `SKILL.md` 6-step reduction
   - Wiring checklist:
     - Stage 1: call `upgrade_preflight.py`; abort on non-zero.
     - Stage 2: invoke `blueprint-upgrade-consumer-apply` with `BLUEPRINT_UPGRADE_ALLOW_DELETE=${BLUEPRINT_UPGRADE_ALLOW_DELETE:-true}`; capture exit code.
     - Stage 3: invoke `resolve_contract_upgrade.py`; capture exit code.
     - Stage 4: auto-resolve non-contract conflicts (existing apply behavior; no new code).
     - Stage 5: invoke `upgrade_coverage_fetch.py`.
     - Stage 6: invoke `upgrade_mirror_sync.py`.
     - Stage 7: invoke `upgrade_doc_target_check.py` (non-blocking; capture warnings only).
     - Stage 8: invoke `make quality-docs-sync-generated-reference`.
     - Stage 9: invoke `make infra-validate` then `make quality-hooks-run`; abort with structured error on first failure.
     - Stage 10: invoke `upgrade_residual_report.py` in a `trap ... EXIT` so it always runs even on abort.
     - Emit `[PIPELINE] Stage N: starting / complete` progress lines before and after each stage (NFR-OBS-001).
   - Red→green TDD:
     1. Write `TestIdempotency` (run pipeline twice on clean fixture → no file changes, exit 0 on second run) — fails (no entry wrapper yet).
     2. Write `TestProgressLines` (stdout contains stage-labeled lines for each stage).
     3. Write `TestNoConsumerSpecificHardcoding` (scan new script files for hardcoded consumer names/module lists/skill dirs).
     4. Complete wrapper implementation — tests go green.
   - Validation: `python3 -m pytest tests/blueprint/test_upgrade_pipeline.py -k "Idempotency or ProgressLines or NoConsumerSpecific"`; `make quality-hooks-fast`

8. **Slice 8 — Full validation and docs sync**
   - Requirements: AC-001, AC-004, AC-005, AC-006
   - Owner: sbonoc | Depends on: Slice 7 complete | Blocks: nothing
   - Actions:
     1. Run `make quality-docs-sync-generated-reference` — verify generated reference docs are current.
     2. Run `python3 -m pytest tests/blueprint/` — all new and existing tests pass (AC-006 no regression).
     3. Run `make quality-hooks-fast` and `make infra-contract-test-fast`.
     4. Update `references/manual_merge_checklist.md` to reference new residual report format.
     5. Populate `pr_context.md` with validation evidence.
   - Validation: all pytest, hooks, and contract-test commands exit 0; `make quality-sdd-check` still passes.

## Change Strategy
- Migration/rollout sequence: all existing individual make targets remain unchanged; `blueprint-upgrade-consumer` is a new additive target. No consumer migration needed.
- Backward compatibility policy: existing targets (`blueprint-upgrade-consumer-apply`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-preflight`, `blueprint-upgrade-consumer-postcheck`, `blueprint-upgrade-fresh-env-gate`) must pass their existing tests unmodified (AC-006).
- Rollback plan: the new entry wrapper and new scripts are additive; removing the `blueprint-upgrade-consumer` target and new scripts is a complete rollback with no effect on existing targets.

## Validation Strategy (Shift-Left)
- Unit checks: pytest for each new script (resolver, coverage fetcher, mirror sync, doc checker, residual reporter) with fixture inputs; aim for per-stage isolation.
- Contract checks: existing `infra-contract-test-fast` must pass without modification (AC-006).
- Integration checks: end-to-end test against a minimal fixture consumer directory exercising the full pipeline (AC-003); idempotency verification (NFR-REL-001).
- E2E checks: existing `blueprint-upgrade-fresh-env-gate` exercises the apply+delete path (AC-004); no new E2E infrastructure required.

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
- Notes: this work item adds Python scripts, shell orchestration, and Makefile targets only; no app delivery, build, or runtime changes.

## Documentation Plan (Document Phase)
- Blueprint docs updates: `docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md` (ADR, already drafted as proposed); `references/manual_merge_checklist.md` updated to reference new residual report format.
- Consumer docs updates: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` reduced from ~30-step runbook to 6-step flow (run command, read report, apply prescribed actions, re-run hooks, commit, PR).
- Mermaid diagrams updated: architecture.md pipeline flowchart.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file: `pr_context.md`
- Hardening review file: `hardening_review.md`
- Local smoke gate (HTTP route/filter changes): not applicable — no HTTP routes or new API endpoints introduced.
- Publish checklist:
  - include requirement/contract coverage (all FR/NFR/AC traced)
  - include key reviewer files (`resolve_contract_upgrade.py`, `upgrade_consumer.sh`, test fixtures)
  - include validation evidence (pytest output, `make quality-hooks-fast` result)
  - include rollback notes (additive only; rollback = remove new target + scripts)

## Operational Readiness
- Logging/metrics/traces: stage-labeled progress lines to stdout (NFR-OBS-001); JSON decision artifacts per stage; residual report always emitted.
- Alerts/ownership: no runtime alerting; gate chain exit code surfaces in make output.
- Runbook updates: `SKILL.md` reduced to 6-step flow; `references/manual_merge_checklist.md` updated.

## Risks and Mitigations
- Risk 1: Q-1 (Stage 5 fetch scope) and Q-2 (ALLOW_DELETE default) are open pending user decision → implementation of FR-004 and FR-010 is gated on those answers; all other slices can proceed independently.
- Risk 2: contract resolver fixture coverage may not include all production conflict JSON shapes → mitigation: collect real conflict JSON from the dhe-marketplace upgrade run as an additional fixture input.
