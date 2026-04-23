# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | Worktree creation from upgrade branch HEAD | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` |
| FR-002 | SDD-C-005, SDD-C-007 | Target execution inside worktree with inherited env | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` |
| FR-003 | SDD-C-005, SDD-C-007, SDD-C-008 | Diff worktree file state vs working tree on failure | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` (divergences field) |
| FR-004 | SDD-C-005, SDD-C-007 | EXIT trap for `git worktree remove --force` | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `git worktree list` post-run |
| FR-005 | SDD-C-005, SDD-C-007 | Hard failure on worktree creation error | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` (status=error) |
| FR-006 | SDD-C-005, SDD-C-010, SDD-C-012 | JSON report + inline stdout | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`, `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` |
| NFR-SEC-001 | SDD-C-009 | Worktree created from committed HEAD only; env inheritance accepted | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | ADR rationale | `artifacts/blueprint/fresh_env_gate.json` |
| NFR-OBS-001 | SDD-C-010 | JSON artifact schema + `blueprint_upgrade_fresh_env_gate_status_total` metric | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`, `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | metric emission in CI |
| NFR-REL-001 | SDD-C-008 | Idempotent gate; EXIT trap; no working-tree mutation | `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | ADR tradeoffs | `git worktree list` post-run |
| NFR-OPS-001 | SDD-C-010, SDD-C-012 | Actionable failure output with file, reason, exit code | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` | `docs/blueprint/` upgrade skill reference | `artifacts/blueprint/fresh_env_gate.json` (divergences) |
| AC-001 | SDD-C-012 | Gate fails when bootstrap-managed file absent in fresh env | `tests/blueprint/test_upgrade_fresh_env_gate.py` (negative fixture) | pytest pass | — | `fresh_env_gate.json` status=fail |
| AC-002 | SDD-C-012 | Gate passes when all files reproduce correctly from scratch | `tests/blueprint/test_upgrade_fresh_env_gate.py` (positive fixture) | pytest pass | — | `fresh_env_gate.json` status=pass |
| AC-003 | SDD-C-012 | Gate fails with status=error on worktree creation failure | `tests/blueprint/test_upgrade_fresh_env_gate.py` (error fixture) | pytest pass | — | `fresh_env_gate.json` status=error |
| AC-004 | SDD-C-012 | EXIT trap removes worktree on SIGINT/SIGTERM | `tests/blueprint/test_upgrade_fresh_env_gate.py` (interrupt fixture) | pytest pass | — | `git worktree list` |
| AC-005 | SDD-C-012 | Worktree absent from `git worktree list` after successful run | `tests/blueprint/test_upgrade_fresh_env_gate.py` (positive fixture) | pytest pass | — | `git worktree list` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed:
  - `pytest tests/blueprint/test_upgrade_fresh_env_gate.py` — 16 passed in 2.44s (8 unit, 8 integration)
  - `make quality-sdd-check` — clean
  - `make infra-validate` — clean (make/blueprint.generated.mk and blueprint/contract.yaml validated)
  - `make quality-hardening-review` — clean
  - `make quality-docs-check-changed` — clean after regenerating core_targets.generated.md and classifying test file in test_pyramid_contract.json
- Result summary: all 16 tests pass; no TODO/FIXME/dead code in touched scope; no stale artifacts
- Documentation validation:
  - `make docs-build` — see T-405 (pending live docs build)
  - `make docs-smoke` — see T-406 (pending live docs smoke)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: If worktree overhead causes meaningful friction on slow machines, introduce a configurable timeout (separate work item).
- Follow-up 2: If false negatives (env-var-driven divergences not caught by file diff) are observed, deepen the divergence detection strategy (separate work item).
