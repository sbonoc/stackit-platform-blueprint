# Tasks

## Gate Checks (Required Before Implementation)
- [x] G-001 Confirm `SPEC_READY=true` in `spec.md` — DONE 2026-06-18 (commit `e2270122`).
- [x] G-002 Confirm open questions and unresolved alternatives are `0` — DONE (commit `bdbff071` resolved Q-1..Q-4; spec gate reads 0 in both fields).
- [x] G-003 Confirm required sign-offs are approved — DONE (all 4 canonical phrases recorded in commit `e2270122`).
- [x] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs — DONE (spec.md declares 18 control IDs SDD-C-001 .. SDD-C-021 with exception rationale for the 7 not-applicable controls).
- [x] G-005 Confirm `Implementation Stack Profile` section is fully populated — DONE (all 11 profile fields populated in spec.md).

## Implementation
- [x] T-001 Author `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` per FR-014 (idempotent — files `#361.1`, `#361.2`, `#361.4`, `#361.5` via `gh issue create`; defers `#361.3` per Q-1). The human operator runs this script at parent merge time; this work item does NOT itself file the issues. — DONE: script authored in commit `20652736`; hardened with `check_preconditions` (gh auth + repo identity) + explicit gh-list failure detection in commit `c99de936`. Operator-run, not parent-PR-run.
- [x] T-002 Author `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` per FR-015 (idempotent — appends `after: issue-335` + `after: issue-336` entries to `AGENTS.backlog.md` so `#361.3` filing surfaces mechanically when blockers resolve). The human operator runs this script at parent merge time alongside T-001. — DONE: script authored in commit `20652736`; awk-based section injection (preserving pre-existing `### after: issue-336` entries; creating `### after: issue-335` if absent) implemented in commit `a8322199`.
- [x] T-003 Add the `## Integration Acceptance Criteria` section to the parent `#361` issue body with the 5 cross-child checkboxes from AC-005 .. AC-009 per Contract C4. The human operator updates the parent issue body at parent merge time. — DEFERRED to parent merge per `pr_context.md` operator runbook step 3 (post-merge operator action; ticked here because the deferral is the deliberate completion state for this task at the parent-PR-publish moment, not an outstanding work item).
- [x] T-004 Mark `AGENTS.backlog.md` entry for `#369` as `incorporated: issue-361.5` once `#361.5` merges (deferred to a follow-up document-sync pass). — DEFERRED to `#361.5` merge (months out); ticked here because the deferral itself is the completion state at parent-PR-publish moment, and the trigger (`#361.5` merge) is durably captured in this spec § Notes for Child Intake.
- [x] T-005 No blueprint orchestrator runtime code lands in THIS work item — every code/Helm/PERSONA.md change is owned by one of the 5 children. This parent coordination work item lands only `specs/`, the ADR, the two helper scripts (FR-014/FR-015), and their pytest (T-110). — DONE: confirmed via `git diff main...HEAD` — only `specs/`, ADR, 2 scripts, 1 pytest, and `test_pyramid_contract.json` classification row landed.

## Test Automation
- [x] T-101 N/A at parent level — orchestrator unit tests live in each child work item.
- [x] T-102 N/A at parent level — orchestrator contract tests live in each child work item.
- [x] T-103 N/A — no filter/payload-transform routes in this work item or in any child.
- [x] T-104 Translate any reproducible pre-PR smoke/`curl`/deterministic-check finding into a failing automated test first, then turn it green with the fix in the same child work item (or document deterministic exception in publish artifacts). — DONE: applied during commit `c99de936`'s set-e bug; the hardened-script issue was caught via standalone bash repro, the failing test case `test_file_children_aborts_on_gh_list_failure` was authored, then the script was fixed (stdout-token return) to make it green. Translated finding → failing test → fix discipline observed.
- [x] T-105 N/A at parent level — boundary/integration tests for orchestrator behavior live in each child work item (AC-005 .. AC-009 land in `#361.3` or `#361.4` or `#361.5`).
- [x] T-110 Author `tests/blueprint/test_issue_361_file_children_script.py` covering AC-010 + AC-011 + AC-013: stub `gh` CLI via `PATH` injection, assert `file_children.sh` first-run produces 4 issue-create calls with correct titles/bodies/labels and second-run produces zero; stub `AGENTS.backlog.md` via a temp file path, assert `add_deferred_triggers.sh` injects 2 entries beneath their `### after: issue-NNN` headers (creating the header if absent, preserving pre-existing entries if present) and second-run injects zero; AND assert no generated child body or backlog rationale text matches `(?i)\b(close[ds]?|fix(e[ds])?|resolve[ds]?)\s+#361\b` (AC-013 — no auto-close keyword targeting parent `#361`). — DONE: pytest authored in commit `20652736`; extended in `a8322199` (section-injection assertions), `719a4fea` (no-auto-close regex), `c99de936` (gh-list failure detection). 7 test cases, all green.
- [x] T-211 N/A at parent level — this is the cross-child integration test authored INSIDE `#361.3`'s own work item (per parent spec FR-016 + AC-012). The test MUST assert that after `#361.3` merges, neither `specs/2026-06-18-issue-361-orchestrator-service/file_children.sh` nor `specs/2026-06-18-issue-361-orchestrator-service/add_deferred_triggers.sh` exists on the working tree at `main`. The parent work item only records this requirement; the test itself is authored as part of `#361.3`'s implementation phase. — DEFERRED to `#361.3` implementation; ticked here because the parent-level obligation (record the requirement in spec FR-016 + AC-012) is complete.

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [x] T-A01 NFR-A11Y-001 is declared "N/A — headless orchestrator service with no UI surface; operator observability is via Grafana authored downstream by `#350`" in `spec.md`. — DONE: declared in spec.md NFR-A11Y-001 line.
- [x] T-A02 N/A — no UI surface; axe-core scan does not apply.
- [x] T-A03 N/A — no interactive elements; keyboard operability does not apply.
- [x] T-A04 N/A — no focused elements; focus indicator does not apply.
- [x] T-A05 N/A — no non-text content; programmatic labelling does not apply.

## Validation and Release Readiness
- [x] T-201 Run `make quality-sdd-check` and `make quality-hardening-review` on this parent coordination spec. — DONE: `quality-sdd-check` PASS across all 9 commits since branch open; `quality-hardening-review` PASS post-hardening_review.md authoring.
- [x] T-202 Attach the C7 lifecycle JSONL evidence to `traceability.md` once each child emits its phase-boundary events. — DEFERRED to each child's own SDD lifecycle; parent-level C7 JSONL evidence at `artifacts/c7/2026-06-18-issue-361-orchestrator-service.jsonl` (5 events: intake, resolve-questions, spec-complete, plan-slicer, implement) recorded in `traceability.md` § Evidence Manifest.
- [x] T-203 Confirm no stale unresolved-work markers / dead code / drift across the parent spec + ADR. — DONE: 4 keeper runs across this branch confirm 35-ID alignment spec ↔ graph ↔ traceability with zero deltas; no unresolved-work markers in spec.md (open-clarifications-count = 0 at gate).
- [x] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`). — DONE: docs-cross-reference-check PASS in `quality-hooks-fast` strict gate.
- [x] T-205 Run hardening review validation bundle (`make quality-hardening-review`). — DONE post-hardening_review.md authoring.

## Publish
- [x] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section. — DONE: 5 findings documented (auto-close keyword bug, gh-list error swallowing, backlog section injection, OpenHands "managed" wording, ADR/spec ceiling-exception contradiction); proposals-only section reads `- none`.
- [x] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes. — DONE: all 6 sections populated including 5-command validation evidence and 4-risk roll (R1–R4).
- [x] P-003 Ensure PR description follows repository template headings and references `pr_context.md`. — DONE: PR #372 body updated multiple times (last in commit set; cites `pr_context.md` operator runbook).

## App Onboarding Minimum Targets (Normative)
- [x] A-001 N/A — `apps-bootstrap` and `apps-smoke` are not affected by this work item (platform/factory infrastructure, not an app-delivery workload); declared `App onboarding impact: no-impact` in `plan.md`.
- [x] A-002 N/A — backend app lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are unaffected.
- [x] A-003 N/A — frontend app lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are unaffected.
- [x] A-004 N/A — aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are unaffected.
- [x] A-005 N/A — port-forward operational wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are unaffected; `#361.4` adds `infra-helm-orchestrator-*` targets under the existing `infra-helm-*` family.
