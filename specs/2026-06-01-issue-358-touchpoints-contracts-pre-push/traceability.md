# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | | `touchpoints-test-unit-pre-push` stanza in template | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | ADR-issue-358 | |
| FR-002 | SDD-C-005, SDD-C-008 | | `touchpoints-test-contracts-pre-push` stanza in template; files pattern covers TS source, api-client, and tests/touchpoints/contracts/*.py | same file | T-102 | ADR-issue-358 | |
| FR-003 | SDD-C-005, SDD-C-008 | | `backend-test-unit-pre-push` stanza in template | same file | T-103 | ADR-issue-358 | |
| FR-004 | SDD-C-005 | | `always_run: false` + file-glob on all five hooks | same file | T-104 | ADR-issue-358 D-2; `consumer_quality_gates.md` backport note | |
| FR-005 | SDD-C-011 | | Blueprint upgrade flow; template as seeded source | upgrade process | T-105 | upgrade release notes / backport note | |
| FR-006 | SDD-C-005, SDD-C-008 | | `backend-test-contracts-pre-push` stanza in template | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-108 | ADR-issue-358 D-5 | |
| FR-007 | SDD-C-005, SDD-C-008 | | `touchpoints-test-integration-pre-push` stanza in template | same file | T-109 | ADR-issue-358 D-5 | |
| NFR-SEC-001 | SDD-C-009 | | N/A — all five hooks invoke local make targets only; no credential surface | none | | | |
| NFR-OBS-001 | SDD-C-010 | | N/A — terminal output only | none | | | |
| NFR-A11Y-001 | | | N/A — no user interface; template file modification only | none | | | |
| NFR-REL-001 | SDD-C-012 | | `always_run: false`; absent-directory guard if needed | `make/platform.mk` (consumer) | T-106 (if finding) | | |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | | Upgrade documentation | `docs/platform/consumer/consumer_quality_gates.md` | | backport note added | |
| AC-001 | SDD-C-012 | | touchpoints-unit hook presence + all field values | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | ADR-issue-358 | |
| AC-002 | SDD-C-012 | | touchpoints-contracts hook presence + all field values | same file | T-102 | ADR-issue-358 | |
| AC-003 | SDD-C-012 | | backend-unit hook presence + all field values | same file | T-103 | ADR-issue-358 | |
| AC-004 | SDD-C-012 | | `always_run: false`; `stages: [pre-push]` only on all five hooks | same file | T-104 | ADR-issue-358 D-2 | |
| AC-005 | SDD-C-012 | | Drift check exit 0 | `make quality-validate-bootstrap-template-drift` | T-105 | | |
| AC-006 | SDD-C-012 | | backend-contracts hook presence + all field values | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-108 | ADR-issue-358 D-5 | |
| AC-007 | SDD-C-012 | | touchpoints-integration hook presence + all field values | same file | T-109 | ADR-issue-358 D-5 | |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - FR-007
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-A11Y-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007

## Validation Summary
- Required bundles executed: `make quality-validate-bootstrap-template-drift` (T-105, exit 0), `make quality-sdd-check` (exit 0), `make blueprint-test-unit` (passed), `make quality-hooks-run` (strict phase all pass)
- Result summary: All test assertions pass (52/52 — T-101 through T-104, T-108, T-109). Drift check clean. SDD check clean. All five make targets exit 0 when test directory absent (T-004, no guards needed, T-106 contingency not triggered).
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: All five make targets verified exit 0 when test directory absent (T-004 complete; T-106 contingency not triggered). No open action.
- Follow-up 2: Resolved — `backend-test-contracts-pre-push` (FR-006) and `touchpoints-test-integration-pre-push` (FR-007) promoted to normative scope and implemented in this PR.
