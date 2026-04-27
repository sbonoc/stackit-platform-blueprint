# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-009 | Descriptor-kustomization cross-check assertion | `scripts/lib/blueprint/template_smoke_assertions.py` (extended `main()`) | `tests/blueprint/test_template_smoke_assertions.py` (drift detection tests) | architecture.md | `make blueprint-template-smoke` exit code |
| FR-002 | SDD-C-005, SDD-C-012 | Template content consistency guarantee | `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl`; `scripts/templates/infra/bootstrap/infra/gitops/platform/base/apps/kustomization.yaml` | template consistency unit test (AC-003) | this spec; ADR | `make blueprint-template-smoke` |
| NFR-SEC-001 | SDD-C-009 | File I/O constrained to repo_root | `template_smoke_assertions.py` (all reads via `repo_root / path`) | no new I/O paths introduced (code review) | architecture security note | smoke exit |
| NFR-OBS-001 | SDD-C-010 | Per-filename AssertionError messages | `template_smoke_assertions.py` assertion message format | failing assertion test checks message content includes filename and both paths | none | CI log output |
| NFR-REL-001 | SDD-C-012 | Fail-fast on drift | `template_smoke_assertions.py` (raises AssertionError; Python smoke step non-zero exit) | drift-detection unit test asserts non-zero (AC-001) | none | `make blueprint-template-smoke` exit code |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | No operator action required | tooling-only change; no consumer config change needed | no consumer-facing contract change | none | none |
| AC-001 | SDD-C-012 | Smoke fails on drift | `template_smoke_assertions.py` assertion block | unit test: descriptor with absent filename raises AssertionError naming missing file and both paths | none | CI failure log |
| AC-002 | SDD-C-012 | Smoke passes on consistent templates | `template_smoke_assertions.py` assertion block + current consistent templates | unit test: consistent descriptor+kustomization pair passes without AssertionError | none | `make blueprint-template-smoke` exit 0 |
| AC-003 | SDD-C-005, SDD-C-012 | Template file content agreement | `descriptor.yaml.tmpl`; `kustomization.yaml` (infra bootstrap template) | template consistency unit test reads both files and asserts filename sets are equal | none | `make blueprint-template-smoke` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003

## Validation Summary
- Required bundles executed: pytest unit suite (21/21 pass), `make quality-sdd-check`, `make quality-docs-check-changed`, bootstrap template mirror sync (all skipped: already synchronized)
- Result summary: all 21 tests green (7 new: DescriptorKustomizationCrossCheckTests × 6, TemplateConsistencyTests × 1); SDD asset compliance verified; no blueprint docs changes required (tooling-only change, no new consumer-facing contract)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: once v1.8.1 is released and dhe-marketplace upgrades, close issue #217 and remove the workaround note from their upgrade PR description.
