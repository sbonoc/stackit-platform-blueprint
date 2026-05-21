# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-008 | — | port_forward.sh library: start_port_forward call | `scripts/bin/infra/local_workflows_smoke.sh` | AC-001: smoke passes without manual port-forward | — | — |
| FR-002 | SDD-C-008 | — | port_forward.sh library: wait_for_local_port call | `scripts/bin/infra/local_workflows_smoke.sh` | AC-001: smoke passes without manual port-forward | — | — |
| FR-003 | SDD-C-008 | — | port_forward.sh library: stop_port_forward on exit | `scripts/bin/infra/local_workflows_smoke.sh` | AC-003: pgrep returns 0 after smoke | — | — |
| FR-004 | SDD-C-013 | — | README "DAG Development Setup" section (Python Version + Repository Structure subsections) | `docs/platform/modules/local-workflows/README.md` | AC-005: Python version subsection present; AC-010: repo structure subsection present | AC-005, AC-006, AC-010 | — |
| FR-005 | SDD-C-005, SDD-C-011 | — | infra-local-workflows-dags-venv make target | `scripts/bin/blueprint/render_makefile.sh`, `scripts/bin/infra/local_workflows_dags_venv.sh` | AC-007: .venv-dags at Python 3.12 created | — | — |
| NFR-A11Y-001 | — | — | N/A — no UI surfaces | — | — | — | — |
| NFR-SEC-001 | — | — | N/A — no auth/secrets surfaces | — | — | — | — |
| NFR-OBS-001 | — | — | N/A — no new observability surfaces | — | — | — | — |
| NFR-REL-001 | — | — | N/A — port_forward.sh handles idempotency | — | — | — | — |
| NFR-OPS-001 | SDD-C-010 | — | no PID in state file | `scripts/bin/infra/local_workflows_smoke.sh` | AC-004: state file has no PID field | — | — |
| NFR-OPS-002 | SDD-C-010 | — | state file contract unchanged | `scripts/bin/infra/local_workflows_smoke.sh` | AC-004: status=passed in state file | — | — |
| NFR-OPS-003 | SDD-C-011 | — | WORKFLOWS_LOCAL_ENABLED=false guard | `scripts/bin/infra/local_workflows_smoke.sh`, `scripts/bin/infra/local_workflows_dags_venv.sh` | AC-002, AC-008: skip exit 0 verified by running scripts directly with WORKFLOWS_LOCAL_ENABLED=false | — | — |
| AC-001 | SDD-C-008 | — | — | — | manual smoke with running stack | — | — |
| AC-002 | SDD-C-011 | — | — | — | `make infra-local-workflows-smoke` with env false | — | — |
| AC-003 | SDD-C-008 | — | — | — | pgrep check post-smoke | — | — |
| AC-004 | SDD-C-010 | — | — | — | cat state file post-smoke | — | — |
| AC-005 | SDD-C-013 | — | — | — | grep "DAG Development Setup" README; verify Python Version subsection | AC-005 | — |
| AC-006 | SDD-C-013 | — | — | — | diff README vs bootstrap template DAG Development Setup section | AC-006 | — |
| AC-007 | SDD-C-005, SDD-C-011 | — | — | — | `.venv-dags/bin/python --version` = 3.12 | — | — |
| AC-008 | SDD-C-011 | — | — | — | `make infra-local-workflows-dags-venv` with env false | — | — |
| AC-009 | — | — | — | — | `make quality-hooks-fast` exit 0 | — | — |
| AC-010 | SDD-C-013 | — | — | — | grep "Repository Structure" README; verify /dags/ example and subpath sync note | AC-010 | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005
  - NFR-A11Y-001, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-OPS-002, NFR-OPS-003
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010

## Validation Summary
- Required bundles executed: quality-hooks-fast, quality-hardening-review, skip-path smoke, skip-path dags-venv
- Result summary: All automated gates pass. AC-002 (WORKFLOWS_LOCAL_ENABLED=false smoke skip) and AC-008 (WORKFLOWS_LOCAL_ENABLED=false dags-venv skip) verified. AC-001, AC-003, AC-004, AC-007 require a running local-workflows stack; deferred to post-merge smoke.
- Documentation validation:
  - `make docs-build`: deferred (requires running docs server)
  - `make docs-smoke`: deferred (requires running docs server)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: RESOLVED — README "DAG Development Setup / Python Version" subsection documents `uv python install 3.12` as the prerequisite step if Python 3.12 is not yet available to uv.
