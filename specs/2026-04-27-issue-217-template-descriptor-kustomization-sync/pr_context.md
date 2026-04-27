# PR Context

## Summary
- Work item: 2026-04-27-issue-217-template-descriptor-kustomization-sync
- Objective: add a descriptor-kustomization cross-check assertion to `template_smoke_assertions.py` so that any future drift between `apps/descriptor.yaml.tmpl` and the infra bootstrap kustomization template is caught at template-edit time; fixes the v1.8.0 `blueprint-template-smoke` failure that blocked `blueprint-upgrade-consumer-validate` for all consumers.
- Scope boundaries: single-file assertion addition in `template_smoke_assertions.py`; new unit tests for the assertion and template consistency; no consumer-facing contract or make target changes.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
- Acceptance criteria covered: AC-001, AC-002, AC-003
- Contract surfaces changed: `make blueprint-template-smoke` now explicitly fails on descriptor-kustomization filename drift (was implicitly failing via infra-validate; now also caught by Python assertion step with named error message)

## Key Reviewer Files
- Primary files to review first: `scripts/lib/blueprint/template_smoke_assertions.py` (assertion addition)
- High-risk files: none (assertion is additive; no existing logic removed or modified)

## Validation Evidence
- Required commands executed: deferred to implementation phase (SPEC_READY=false at intake)
- Result summary: intake-only; full validation evidence captured after implementation
- Artifact references: `traceability.md`, `evidence_manifest.json`

## Risk and Rollback
- Main risks: convention-default manifest path handling (components with no explicit `manifests:` block must use `{component_id}-{kind}.yaml` derivation to avoid false-positive drift errors)
- Rollback strategy: revert the assertion block in `template_smoke_assertions.py`; infra-validate continues to catch membership errors in consumer repos with no behavioral regression

## Deferred Proposals
- Proposal 1 (not implemented): extract a shared `assert_descriptor_kustomization_agreement` helper into a separate module for reuse in other smoke scenarios — deferred because no other caller exists; inline is sufficient for now.
