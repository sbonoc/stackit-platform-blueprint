# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | | `touchpoints-test-unit-pre-push` stanza in template | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | ADR-issue-358 | |
| FR-002 | SDD-C-005, SDD-C-008 | | `touchpoints-test-contracts-pre-push` stanza in template | same file | T-102 | ADR-issue-358 | |
| FR-003 | SDD-C-005, SDD-C-008 | | `backend-test-unit-pre-push` stanza in template | same file | T-103 | ADR-issue-358 | |
| FR-004 | SDD-C-005 | | `always_run: false` + file-glob on all three hooks | same file | T-104 | | |
| FR-005 | SDD-C-011 | | Blueprint upgrade flow; template as seeded source | upgrade process | T-105 | upgrade release notes / backport note | |
| NFR-SEC-001 | SDD-C-009 | | N/A — all three hooks invoke local make targets only; no credential surface | none | | | |
| NFR-OBS-001 | SDD-C-010 | | N/A — terminal output only | none | | | |
| NFR-A11Y-001 | | | N/A — no user interface; template file modification only | none | | | |
| NFR-REL-001 | SDD-C-012 | | `always_run: false`; absent-directory guard if needed | `make/platform.mk` (consumer) | T-106 (if finding) | | |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | | Upgrade documentation | `docs/blueprint/consumer/upgrade_summary.md` or equivalent | | upgrade notes | |
| AC-001 | SDD-C-012 | | touchpoints-unit hook presence + all field values | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | | |
| AC-002 | SDD-C-012 | | touchpoints-contracts hook presence + all field values | same file | T-102 | | |
| AC-003 | SDD-C-012 | | backend-unit hook presence + all field values | same file | T-103 | | |
| AC-004 | SDD-C-012 | | `always_run: false`; `stages: [pre-push]` only on all hooks | same file | T-104 | | |
| AC-005 | SDD-C-012 | | Drift check exit 0 | `make quality-validate-bootstrap-template-drift` | T-105 | | |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
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

## Validation Summary
- Required bundles executed: (to be completed during implementation)
- Result summary: (to be completed during implementation)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Verify that all three make targets (`touchpoints-test-unit`, `touchpoints-test-contracts`, `backend-test-unit`) exit 0 when their respective test directory is absent; if any does not, add an absent-directory guard and translate to a failing test per SDD-C-024 (T-106).
- Follow-up 2: Document `backend-test-contracts-pre-push` and `touchpoints-test-integration-pre-push` as Deferred Proposals if consumers report integration or contract regressions on the backend lane.
