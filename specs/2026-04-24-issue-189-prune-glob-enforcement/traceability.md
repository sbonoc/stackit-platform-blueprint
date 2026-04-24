# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | SDD-C-001, SDD-C-007 | _scan_prune_glob_violations reads globs from contract | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-001, T-004, T-201 | ADR-issue-189 | upgrade_validate.json prune_glob_check |
| REQ-002 | SDD-C-001, SDD-C-007 | Violations list + prune_glob_check section in report | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-001, T-002, T-004, T-201 | ADR-issue-189 | upgrade_validate.json |
| REQ-003 | SDD-C-002, SDD-C-007 | summary.status = failure when violation_count > 0 | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-004, T-201 | ADR-issue-189 | validate exit code |
| REQ-004 | SDD-C-008 | stderr emission loop: one line per violation | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-004, T-201 | ADR-issue-189 | stderr output |
| REQ-005 | SDD-C-001 | Skip when repo_mode != generated-consumer | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-003, T-201 | ADR-issue-189 | upgrade_validate.json status=skipped |
| REQ-006 | SDD-C-004 | Skip on contract load error; existing contract_load_error gate | `scripts/lib/blueprint/upgrade_consumer_validate.py` | code review | ADR-issue-189 | upgrade_validate.json status=skipped |
| REQ-007 | SDD-C-001, SDD-C-007 | Read prune_glob_check from validate payload; emit prune_glob_violations | `scripts/lib/blueprint/upgrade_consumer_postcheck.py` | T-005, T-201 | ADR-issue-189 | upgrade_postcheck.json |
| REQ-008 | SDD-C-002, SDD-C-007 | prune-glob-violations in blocked_reasons | `scripts/lib/blueprint/upgrade_consumer_postcheck.py` | T-005, T-201 | ADR-issue-189 | postcheck exit code |
| REQ-009 | SDD-C-014 | Required check step in skill runbook naming glob patterns | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | code review | SKILL.md (AC-005) | operator runbook |
| REQ-010 | SDD-C-009 | Unit test: positive violations (positive-path assertion) | `tests/blueprint/test_upgrade_consumer_validate.py` | T-001, T-201 | — | — |
| REQ-011 | SDD-C-009 | Unit test: empty violations | `tests/blueprint/test_upgrade_consumer_validate.py` | T-002, T-201 | — | — |
| REQ-012 | SDD-C-009 | Unit test: skipped for template-source | `tests/blueprint/test_upgrade_consumer_validate.py` | T-003, T-201 | — | — |
| REQ-013 | SDD-C-009 | Integration test: validate exits non-zero with violations | `tests/blueprint/test_upgrade_consumer_validate.py` | T-004, T-201 | — | — |
| REQ-014 | SDD-C-009 | Integration test: postcheck blocks on violations | `tests/blueprint/test_upgrade_consumer_postcheck.py` | T-005, T-201 | — | — |
| NFR-SEC-001 | SDD-C-011 | pathlib.rglob; symlink resolve check against repo_root | `scripts/lib/blueprint/upgrade_consumer_validate.py` | code review | ADR-issue-189 | — |
| NFR-OBS-001 | SDD-C-008 | stderr line per violation in canonical format | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-004, T-201 | ADR-issue-189 | stderr output |
| NFR-REL-001 | SDD-C-004 | status=skipped on contract load error; no additional failure | `scripts/lib/blueprint/upgrade_consumer_validate.py` | code review | ADR-issue-189 | upgrade_validate.json |
| NFR-OPS-001 | SDD-C-003 | remediation_hint names files and re-run command | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-001, T-004, T-201 | ADR-issue-189 | upgrade_validate.json |
| AC-001 | SDD-C-002 | validate fails + violations listed when ADR present | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-001, T-004, T-201 | — | validate exit code |
| AC-002 | SDD-C-002 | validate succeeds with empty violations | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-002, T-201 | — | validate exit code |
| AC-003 | SDD-C-002 | postcheck blocks with prune-glob-violations in blocked_reasons | `scripts/lib/blueprint/upgrade_consumer_postcheck.py` | T-005, T-201 | — | postcheck exit code |
| AC-004 | SDD-C-001 | prune_glob_check.status = skipped for template-source | `scripts/lib/blueprint/upgrade_consumer_validate.py` | T-003, T-201 | — | upgrade_validate.json |
| AC-005 | SDD-C-014 | SKILL.md names both glob patterns by value | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | code review | SKILL.md | operator runbook |

## Graph Linkage
- Graph file: `graph.json`
- Every `REQ-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009
  - REQ-010, REQ-011, REQ-012, REQ-013, REQ-014
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: pending
- Result summary: pending
- Documentation validation:
  - `make quality-docs-check-changed`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None identified.
