# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | `bootstrap_infra_static_templates()` — sed loop replaces hardcoded calls | `scripts/bin/infra/bootstrap.sh:197-200` | `tests/blueprint/test_quality_contracts.py::test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates` | architecture.md §Bootstrap | ADR §Consequences |
| FR-002 | SDD-C-005, SDD-C-007 | `validate_app_runtime_conformance()` — dynamic derivation | `scripts/lib/blueprint/template_smoke_assertions.py` | `tests/blueprint/test_template_smoke_assertions.py::test_validate_app_runtime_conformance_dynamic_derivation` | architecture.md §Smoke Validation | ADR §Consequences |
| FR-003 | SDD-C-005, SDD-C-008 | `_extract_kustomization_resources()` — stdlib parser | `scripts/lib/blueprint/template_smoke_assertions.py` | `tests/blueprint/test_template_smoke_assertions.py::test_extract_kustomization_resources_*` | ADR §Decision | — |
| NFR-SEC-001 | SDD-C-009 | No secrets/network access; local file reads only | both changed files | code inspection | spec.md §NFR-SEC-001 | — |
| NFR-OBS-001 | SDD-C-010 | FATAL on missing template; AssertionError on empty resources | `bootstrap.sh` log_fatal; `template_smoke_assertions.py` AssertionError | `test_template_smoke_assertions.py::test_extract_kustomization_empty` | spec.md §NFR-OBS-001 | log output |
| NFR-REL-001 | SDD-C-012 | No regression; rollback via git revert | both changed files; existing tests | all pre-existing generated-consumer-smoke tests green | spec.md §NFR-REL-001 | — |
| NFR-OPS-001 | SDD-C-010 | No consumer-side changes required | none | pre-existing test suite green | spec.md §NFR-OPS-001 | — |
| AC-001 | SDD-C-012 | validate_app_runtime_conformance passes on consumer-named manifests | `scripts/lib/blueprint/template_smoke_assertions.py` | `test_template_smoke_assertions.py::test_validate_app_runtime_conformance_dynamic_derivation` | — | — |
| AC-002 | SDD-C-012 | No hardcoded seed names in bootstrap_infra_static_templates | `scripts/bin/infra/bootstrap.sh` | `test_quality_contracts.py::test_no_hardcoded_app_manifest_names_in_bootstrap_infra_static_templates` | — | — |
| AC-003 | SDD-C-012 | _extract_kustomization_resources parses correctly | `scripts/lib/blueprint/template_smoke_assertions.py` | `test_template_smoke_assertions.py::test_extract_kustomization_resources_parses_resources_section` | — | — |
| AC-004 | SDD-C-012 | All pre-existing scenarios pass | all changed files | full test suite green | — | — |
| AC-005 | SDD-C-012 | make infra-validate and quality-hooks-fast pass | all changed files | CI validation output | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make infra-validate`, `make quality-hardening-review`, `make docs-build`, `make docs-smoke`
- Result summary: all passed — 8 new unit tests green in `test_template_smoke_assertions.py`; 1 new regression guard green in `test_quality_contracts.py`; `make infra-validate` passed; `make quality-hardening-review` passed; `make docs-build` and `make docs-smoke` passed.
- Documentation validation:
  - `make docs-build` — passed
  - `make docs-smoke` — passed

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: After #206 lands (contract schema for consumer-owned workload names), validate that the dynamic derivation in `validate_app_runtime_conformance()` still correctly reads from the consumer's kustomization (no contract-layer change needed, but regression check recommended).
