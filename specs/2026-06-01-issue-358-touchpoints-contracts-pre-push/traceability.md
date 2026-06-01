# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-008 | | Hook stanza in template YAML | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | ADR-issue-358-touchpoints-contracts-pre-push.md | |
| FR-002 | SDD-C-005, SDD-C-008 | | `always_run: false` field; file-glob trigger | same file | T-102 | | |
| FR-003 | SDD-C-011 | | Blueprint upgrade flow; template as seeded source | upgrade process | T-103 | upgrade release notes / backport note | |
| NFR-SEC-001 | SDD-C-009 | | N/A — no secret/credential surface | none | | | |
| NFR-OBS-001 | SDD-C-010 | | N/A — terminal output only | none | | | |
| NFR-REL-001 | SDD-C-012 | | `always_run: false`; absent-directory guard in make target if needed | `make/platform.mk` (consumer) | T-104 (if finding) | | |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | | Upgrade documentation | `docs/blueprint/consumer/upgrade_summary.md` or equivalent | | upgrade notes | |
| AC-001 | SDD-C-012 | | Hook presence + all required field values | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | T-101 | | |
| AC-002 | SDD-C-012 | | `always_run: false`; `stages: [pre-push]` only | same file | T-102 | | |
| AC-003 | SDD-C-012 | | Drift check exit code | `make quality-validate-bootstrap-template-drift` | T-103 (make exit 0) | | |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003

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
- Follow-up 1: Verify whether `touchpoints-test-unit-pre-push` is absent from the current template (grep confirmed absent at intake); if it should be present, open a separate work item.
- Follow-up 2: If `make touchpoints-test-contracts` does not exit 0 cleanly when contracts directory is absent, add a guard in the make target and translate to a failing test per SDD-C-024.
