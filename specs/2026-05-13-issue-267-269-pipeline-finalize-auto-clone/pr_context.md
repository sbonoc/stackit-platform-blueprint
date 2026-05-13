# PR Context

## Summary

Issues #267 and #269 address two independent but related gaps in the `make blueprint-upgrade-consumer` pipeline. Issue #269 fixes a fatal-exit bug: when `BLUEPRINT_UPGRADE_SOURCE` is a URL (the canonical form in consumer docs), Stages 1b and 5 fail because they expect a local `.git` path. The pipeline now auto-clones URL-form sources into a tmp dir before Stage 1b, registers a combined EXIT trap (clone cleanup + residual report), and reassigns `upgrade_source` to the local clone. The upgrade engine (`upgrade_consumer.py`) also gains a skip-clone guard to avoid a redundant internal clone when it already receives a pre-cloned local path. Issue #267 adds `make blueprint-upgrade-consumer-finalize` — a canonical, idempotent post-apply quality-convergence target with a sync pass (aggregated, no fail-fast) followed by a verify pass (fail-fast, summary banner on first failure). Pipeline Stages 8+9 are replaced by a single finalize invocation. Both issues are delivered as one PR with TDD slices (red → green) and 25 new unit tests.

## Requirement Coverage

| Requirement ID | Implementation File(s) | Test Evidence |
|---|---|---|
| FR-001 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (URL normalization block) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_normalizes_url_source_before_stage_1b` |
| FR-002 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (combined EXIT trap) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_has_exit_trap_for_clone_cleanup` |
| FR-003 | `scripts/lib/blueprint/upgrade_consumer.py` (skip-clone guard) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_engine_skips_clone_when_source_is_pre_cloned` |
| FR-004 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (local-path fast-path) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_local_path_does_not_trigger_auto_clone` |
| FR-005 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeTargetExistenceTests` |
| FR-006 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (sync pass) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeSyncPassTests` |
| FR-007 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (verify pass + summary banner) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeVerifyPassTests` |
| FR-008 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (Stages 8+9 replaced) | `tests/infra/test_pipeline_finalize_issue_267.py::PipelineIntegrationTests::test_pipeline_invokes_finalize_as_post_stage2_tail` |
| FR-009 | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` (Step 7 updated) | `tests/infra/test_pipeline_finalize_issue_267.py::SkillRunbookTests` |
| NFR-IDM-001 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (idempotent make targets) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeVerifyPassTests::test_finalize_verify_pass_is_fail_fast` |
| NFR-OBS-001 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (`[finalize]` log lines) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeObservabilityTests` |
| NFR-REL-001 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (EXIT trap after clone) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_has_exit_trap_for_clone_cleanup` |
| NFR-SEC-001 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (URL prefix allowlist) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_url_prefix_allowlist` |
| NFR-OPS-001 | Usage blocks in pipeline + finalize scripts | `make quality-sdd-check` |
| NFR-A11Y-001 | N/A — CLI tool with no browser-rendered UI surface | T-A01 (N/A) |
| AC-001 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeTargetExistenceTests::test_finalize_script_exists` |
| AC-002 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeVerifyPassTests::test_finalize_verify_pass_is_fail_fast` |
| AC-003 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (sync_errors counter) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeSyncPassTests::test_finalize_sync_pass_aggregates_failures` |
| AC-004 | `scripts/bin/blueprint/upgrade_consumer_finalize.sh` (_finalize_verify helper) | `tests/infra/test_pipeline_finalize_issue_267.py::FinalizeVerifyPassTests` |
| AC-005 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_finalize_issue_267.py::PipelineIntegrationTests::test_pipeline_invokes_finalize_as_post_stage2_tail` |
| AC-006 | `tests/infra/test_pipeline_finalize_issue_267.py` (synthetic scenario) | `tests/infra/test_pipeline_finalize_issue_267.py` |
| AC-007 | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | `make quality-sdd-check` |
| AC-008 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` (auto-clone + EXIT trap) | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_has_exit_trap_for_clone_cleanup` |
| AC-009 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_normalizes_url_source_before_stage_1b` |
| AC-010 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py::test_pipeline_local_path_does_not_trigger_auto_clone` |
| AC-011 | `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` | `tests/infra/test_pipeline_auto_clone_issue_269.py` (URL-form integration test) |

## Key Reviewer Files

- Primary files to review first:
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — core change: URL normalization block, combined EXIT trap, Stages 8+9 replacement; all three NFR-SEC/REL/OBS requirements land here
  - `scripts/bin/blueprint/upgrade_consumer_finalize.sh` — new file: owns the two-pass finalize logic (sync aggregated + verify fail-fast); the single canonical post-apply convergence command
  - `scripts/lib/blueprint/upgrade_consumer.py` — skip-clone guard: boolean check prevents redundant clone when pipeline pre-clones; verify `temp_dir=None` path in `finally` block
- High-risk files:
  - `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` — combined EXIT trap: if `rm -rf` guard condition is wrong, tmp dir leaks; `|| true` on residual report must not swallow real failures
  - `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` — template source for the new make target; `.PHONY` and target definition must be consistent with existing patterns
  - `tests/infra/test_pipeline_auto_clone_issue_269.py` — 7 static source tests; regex patterns must match (and not over-match) the pipeline source
  - `tests/infra/test_pipeline_finalize_issue_267.py` — 18 static source tests; `PipelineIntegrationTests` splits on "USAGE" to avoid matching the usage block text — verify this is robust
  - `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — consumer-facing skill runbook: Step 7 and Stage 8+9 table updated; consumer agents will read this on next upgrade
  - `docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md` — Mermaid diagram and Dependency 4 updated; confirm diagram matches implementation

## Validation Evidence

```
# make infra-contract-test-fast (post all slices)
141 passed, 0 failures (2026-05-13)
— includes 25 new tests: 7 auto-clone + 18 finalize

# make quality-hooks-fast
PASS — all hooks green (SDD check, docs drift, test pyramid, ACR)

# make docs-build
PASS

# make docs-smoke
PASS

# make quality-hardening-review
PASS (run post publish artifact fill)

# Pre-existing failures (not caused by this work item):
# blueprint-template-smoke: FAIL — declare -A Bash 3.2 incompatibility
#   in prune_codex_skills.sh; file unchanged from main branch
# 8 tests in test_optional_modules, test_python_helper_extractions,
#   test_runtime_credentials_eso: pre-existing, unrelated to changed files
```

Artifact references:
- `specs/2026-05-13-issue-267-269-pipeline-finalize-auto-clone/traceability.md` — full requirement-to-delivery mapping with test counts
- `specs/2026-05-13-issue-267-269-pipeline-finalize-auto-clone/hardening_review.md` — repository-wide findings, architecture compliance, deferred proposals
- `artifacts/blueprint/upgrade-residual.md` — always-emitted residual report (runtime artifact, not committed)

## Risk and Rollback

Main risks:
- **Combined EXIT trap**: single `trap` block handles both clone cleanup and residual report. If `rm -rf` fails silently, the tmp dir leaks. Mitigation: `[[ -n "$cloned_source_dir" ]] &&` guard ensures the rm only runs when a clone was made; `|| true` on the residual report prevents trap abort.
- **Engine skip-clone guard**: `source_is_pre_cloned` check uses `Path.is_dir()` and `.git` subdir presence. If the pre-cloned dir is in a detached state, `_resolve_commit` still works (it calls `git rev-parse HEAD`). No correctness risk identified.
- **Blast radius**: changes are additive (new script, new make target) or replace a broken path (URL normalization). Existing local-path callers are unaffected by the normalization block (fast-path). Individual make targets remain independently callable.

Rollback strategy:
1. Revert `scripts/bin/blueprint/upgrade_consumer_pipeline.sh` to pre-PR state (removes URL normalization block and combined EXIT trap; Stages 8+9 return to direct target calls).
2. Delete `scripts/bin/blueprint/upgrade_consumer_finalize.sh`.
3. Revert `scripts/lib/blueprint/upgrade_consumer.py` to remove skip-clone guard.
4. Revert `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and regenerate `make/blueprint.generated.mk`.
5. Revert `.agents/skills/blueprint-consumer-upgrade/SKILL.md` Step 7 to previous wording.
All rollback steps are local file operations with no database migrations or infra state changes.

## Deferred Proposals

- Proposal 1 (not implemented): Deepen clone for ancestry traversal — current `--depth 1` clone sufficient for Stage 5 `git show` but would fail if a future stage needs `git log`. Deferred: no current stage requires ancestry; deferral avoids unnecessary network cost. Status: TBD — pending triage.
- Proposal 2 (not implemented): Standalone finalize precondition guard — `blueprint-upgrade-consumer-finalize` aborts with an unhelpful postcheck failure when called before Stage 3–7 artifacts exist. A `--skip-postcheck` flag or artifact-presence check would improve standalone UX. Deferred: usage block documents the precondition; out-of-scope for this work item. Status: TBD — pending triage.
- Proposal 3 (not implemented): Sync pass target expansion — dynamic discovery of sync targets vs. current explicit three-target list. Deferred: current list is complete; expansion tracked as follow-up. Status: TBD — pending triage.
