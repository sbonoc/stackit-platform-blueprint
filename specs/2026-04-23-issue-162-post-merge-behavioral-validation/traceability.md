# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | SDD-C-005 | bash -n gate in upgrade_shell_behavioral_check.py | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON behavioral_check.syntax_errors |
| REQ-002 | SDD-C-005 | grep-based symbol resolver in upgrade_shell_behavioral_check.py | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON behavioral_check.unresolved_symbols |
| REQ-003 | SDD-C-005 | per-finding structured output (file, symbol, line) | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON behavioral_check |
| REQ-004 | SDD-C-005 | integration hook in upgrade_consumer_postcheck.py | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON summary |
| REQ-005 | SDD-C-005, SDD-C-006 | opt-out flag BLUEPRINT_UPGRADE_SKIP_BEHAVIORAL_CHECK | scripts/lib/blueprint/upgrade_consumer_postcheck.py, scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON behavioral_check.skipped |
| REQ-006 | SDD-C-005, SDD-C-010 | behavioral_check JSON section in postcheck report | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | postcheck JSON schema docs | artifacts/blueprint/upgrade_postcheck.json |
| REQ-007 | SDD-C-005 | blocked_reasons appended in upgrade_consumer_postcheck.py | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | postcheck JSON summary.blocked_reasons |
| REQ-008 | SDD-C-005 | env var forwarding in upgrade_consumer_postcheck.sh | scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests/blueprint/test_upgrade_consumer_wrapper.py | docs/blueprint/ upgrade postcheck reference | shell wrapper env contract |
| REQ-009 | SDD-C-010 | log_metric call in upgrade_consumer_postcheck.sh | scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests/blueprint/test_upgrade_consumer_wrapper.py | docs/blueprint/ upgrade postcheck reference | blueprint_upgrade_postcheck_behavioral_check_failures_total |
| REQ-010 | SDD-C-005 | grep/regex heuristic in upgrade_shell_behavioral_check.py | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | architecture.md exclusions | N/A |
| REQ-011 | SDD-C-012 | positive/negative fixture shell scripts | tests/blueprint/fixtures/ | tests/blueprint/test_upgrade_postcheck.py | N/A | N/A |
| NFR-SEC-001 | SDD-C-009 | bash -n syntax-only; no shell execution | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ security notes | N/A |
| NFR-OBS-001 | SDD-C-010 | behavioral_check JSON + metric + log_warn | scripts/lib/blueprint/upgrade_consumer_postcheck.py, scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | artifacts/blueprint/upgrade_postcheck.json |
| NFR-REL-001 | SDD-C-011 | no working tree mutation on failure; idempotent check | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | N/A |
| NFR-OPS-001 | SDD-C-012 | per-finding structured output (file, symbol, line) | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | docs/blueprint/ upgrade postcheck reference | artifacts/blueprint/upgrade_postcheck.json |
| AC-001 | SDD-C-012 | syntax error in merged .sh => hard failure | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | N/A | postcheck JSON behavioral_check.syntax_errors |
| AC-002 | SDD-C-012 | dropped function def in merged .sh => hard failure | scripts/lib/blueprint/upgrade_shell_behavioral_check.py | tests/blueprint/test_upgrade_postcheck.py | N/A | postcheck JSON behavioral_check.unresolved_symbols |
| AC-003 | SDD-C-012 | all merged .sh files pass => postcheck success | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | N/A | postcheck JSON summary.status=success |
| AC-004 | SDD-C-012 | opt-out => skip with warning | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | N/A | postcheck JSON behavioral_check.skipped=true |
| AC-005 | SDD-C-012 | blocked_reasons contains behavioral-check-failure iff status=fail | scripts/lib/blueprint/upgrade_consumer_postcheck.py | tests/blueprint/test_upgrade_postcheck.py | N/A | postcheck JSON summary.blocked_reasons |
| AC-006 | SDD-C-012 | behavioral_check_failures_total metric correctness | scripts/bin/blueprint/upgrade_consumer_postcheck.sh | tests/blueprint/test_upgrade_consumer_wrapper.py | N/A | metric emission log |

## Graph Linkage
- Graph file: `graph.json`
- Every `REQ-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed:
  - `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py` — 10/10 passed
  - `pytest tests/blueprint/test_upgrade_postcheck.py` — 11/11 passed (5 pre-existing + 6 new behavioral tests)
  - `pytest tests/blueprint/test_upgrade_consumer_wrapper.py` — 3/3 passed (1 pre-existing + 2 new metric emission tests)
  - `make quality-sdd-check` — passed
- Result summary: 24/24 tests passing across all three test files. SDD governance gates pass. No local smoke required (no HTTP routes, no K8s targets in scope).
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Evaluate deepening source-chain resolution beyond depth-1 if false negatives are observed in practice (tracked as potential Phase 3 extension).
