# PR Context

## Summary
- Work item: issue-162-post-merge-behavioral-validation
- Objective: Add a behavioral validation gate to the blueprint consumer upgrade postcheck that detects silently dropped shell function definitions in `result=merged` scripts using `bash -n` syntax check and a grep-based symbol resolution heuristic.
- Scope boundaries: Gate logic module (new), postcheck orchestrator (additive), shell wrapper env-var forwarding + metric (additive), JSON schema (additive fields), docs (additive section). No changes to plan/apply engine, reconcile report, or consumer repo templates.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006
- Contract surfaces changed: `upgrade_postcheck.schema.json` (additive `behavioral_check` object + two summary fields); `upgrade_consumer_postcheck.py` CLI (additive `--skip-behavioral-check` flag); `upgrade_consumer_postcheck.sh` env contract (new `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK` var, new metric `blueprint_upgrade_postcheck_behavioral_check_failures_total`)

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — gate logic; `_EXCLUDED_TOKENS` set, depth-1 source resolver, grep heuristic
  - `scripts/lib/blueprint/upgrade_consumer_postcheck.py` — orchestrator integration; how `result=merged` .sh files are extracted and gate result feeds blocked_reasons
  - `scripts/bin/blueprint/upgrade_consumer_postcheck.sh` — env-var forwarding and metric emission
- High-risk files:
  - `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` — grep heuristic false-positive risk; mitigated by `_EXCLUDED_TOKENS` frozenset and comment-line exclusion

## Validation Evidence
- Required commands executed: pytest (24/24 passed), make quality-sdd-check (passed), make quality-hardening-review (passed)
- Result summary: 24/24 tests passing across test_upgrade_shell_behavioral_check.py (10), test_upgrade_postcheck.py (11), test_upgrade_consumer_wrapper.py (3). SDD and hardening gates pass. No local smoke required (no HTTP routes, no K8s targets in scope).
- Artifact references: `artifacts/blueprint/upgrade_postcheck.json` (runtime output), `specs/2026-04-23-issue-162-post-merge-behavioral-validation/`

## Risk and Rollback
- Main risks: Grep heuristic may produce false positives on function call patterns that match excluded tokens not yet in `_EXCLUDED_TOKENS`. Impact: false-positive gate failures blocking postcheck. Mitigation: `BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK=true` provides an immediate bypass, and `_EXCLUDED_TOKENS` is a frozenset that can be extended without interface changes.
- Rollback strategy: Revert the PR entirely. No persistent state, no schema migration, no consumer repo changes. The `behavioral_check` JSON key is additive and consumers that do not read it are unaffected.

## Deferred Proposals
- none
