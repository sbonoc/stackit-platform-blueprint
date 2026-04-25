# PR Context

## Summary
- Work item: 2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness
- Objective: Eliminate six behavioral correctness bugs in blueprint upgrade tooling so that upgrade gates produce accurate, actionable outputs and generated CI workflows enforce least-privilege GITHUB_TOKEN posture.
- Scope boundaries: Python scripting and shell tooling in scripts/lib/blueprint/ and scripts/bin/blueprint/; contract.yaml coverage additions; generated ci.yml permissions block. No Kubernetes, Crossplane, or managed-service components touched.

## Requirement Coverage
- Requirement IDs covered: FR-001–FR-016 (issues #179, #180, #181, #185, #186, #187)
- Acceptance criteria covered: AC-001–AC-004 (reconcile report markers), AC for case-label/array false positives, _EXCLUDED_TOKENS completeness, source-tree hard-fail audit, artifact checksum divergence detection, ci.yml permissions block
- Contract surfaces changed: blueprint/contract.yaml (required_files, source_only, init_managed, conditional_scaffold, blueprint_managed_roots, observability/langfuse module scaffolding_mode); scripts/templates/blueprint/bootstrap/blueprint/contract.yaml (synced); .github/workflows/ci.yml (permissions block)

## Key Reviewer Files
- Primary files to review first:
  - scripts/lib/blueprint/upgrade_reconcile_report.py
  - scripts/lib/blueprint/upgrade_shell_behavioral_check.py
  - scripts/lib/blueprint/upgrade_consumer.py
  - scripts/lib/blueprint/upgrade_fresh_env_gate.py
  - scripts/lib/quality/render_ci_workflow.py
- High-risk files: blueprint/contract.yaml (47 new required_files, 8 source_only, observability/langfuse conditional scaffold additions); scripts/bin/blueprint/upgrade_fresh_env_gate.sh (exit-code logic updated for checksum divergence gate)

## Validation Evidence
- Required commands executed: python3 -m pytest tests/blueprint/ -q; make quality-hooks-fast
- Result summary: 392 tests pass (up from 385 before slices 5–6); 7 pre-existing failures unchanged (test_bootstrap_templates x2, test_contract_bootstrap_surface, test_contract_init_governance, test_upgrade_preflight x2, test_upgrade_postcheck); quality-hooks-fast passes after test_pyramid_contract.json update for test_upgrade_reconcile_report.py; audit_source_tree_coverage reports 0 uncovered files
- Artifact references: specs/2026-04-24-issue-179-180-181-185-186-187-upgrade-correctness/

## Risk and Rollback
- Main risks: (1) blueprint/contract.yaml additions may need re-audit if upstream blueprint adds new files not covered by the new categories — mitigated by hard-fail audit gate in the planner; (2) artifact checksum divergence gate may flag non-deterministic artifacts — mitigated by scoping comparison to stable paths under artifacts/blueprint/
- Rollback strategy: git revert <merge-commit> on blueprint main; consumer repos that regenerated ci.yml would need a follow-up upgrade run to revert permissions block, but the block is benign/beneficial

## Deferred Proposals
- none — no new proposals surfaced during implementation; follow-on issues #183 (stale reconcile report detection) and #184 (consumer-extensible exclusion set) are pre-existing backlog items tracked in AGENTS.backlog.md
