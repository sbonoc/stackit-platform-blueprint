# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | SDD-C-001, SDD-C-007 | Artifact-seeding block in shell wrapper | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001, T-201 | ADR-issue-182 | log_info on seed |
| REQ-002 | SDD-C-001 | Seeding no-op guard | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-002, T-201 | ADR-issue-182 | log_info on skip |
| REQ-003 | SDD-C-008 | log_info call on seed | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001 | ADR-issue-182 | gate log output |
| REQ-004 | SDD-C-008 | log_info call on skip | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-002 | ADR-issue-182 | gate log output |
| REQ-005 | SDD-C-007 | Existing _cleanup_worktree EXIT trap | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-203, existing worktree cleanup tests | architecture.md | EXIT trap |
| REQ-006 | SDD-C-001 | _EXCLUDE_TOP_DIRS in Python module | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | existing test_compute_divergences_excludes_artifacts_dir | ADR-issue-182 | fresh_env_gate.json |
| REQ-007 | SDD-C-009 | Integration test: artifacts present | `tests/blueprint/test_upgrade_fresh_env_gate.py` | T-001 | — | — |
| REQ-008 | SDD-C-009 | Integration test: artifacts absent | `tests/blueprint/test_upgrade_fresh_env_gate.py` | T-002 | — | — |
| NFR-SEC-001 | SDD-C-011 | cp scoped to artifacts/blueprint/ only | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | code review | ADR-issue-182 | — |
| NFR-OBS-001 | SDD-C-008 | log_info messages on seed and skip | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001, T-002 | ADR-issue-182 | gate log output |
| NFR-REL-001 | SDD-C-004 | _cleanup_worktree EXIT trap (rm -rf) | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | existing worktree cleanup tests | architecture.md | EXIT trap |
| NFR-OPS-001 | SDD-C-008 | log_info includes source + dest paths | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001 | ADR-issue-182 | gate log output |
| AC-001 | SDD-C-002 | Gate exits 0 on successful upgrade | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001 | — | gate exit code |
| AC-002 | SDD-C-002 | Gate proceeds on absent artifacts | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-002 | — | gate exit code |
| AC-003 | SDD-C-007 | _cleanup_worktree EXIT trap | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | existing worktree cleanup tests | — | git worktree list |
| AC-004 | SDD-C-008 | log_info seeding message | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | T-001 | — | gate log output |
| AC-005 | SDD-C-001 | _EXCLUDE_TOP_DIRS excludes artifacts/ | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | existing test_compute_divergences_excludes_artifacts_dir | — | fresh_env_gate.json |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced:
  - REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: pending
- Result summary: pending
- Documentation validation: pending

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None identified.
