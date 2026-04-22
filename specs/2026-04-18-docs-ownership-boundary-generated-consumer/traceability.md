# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | template-source strict sync for required seed files | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `docs/blueprint/architecture/decisions/ADR-20260418-generated-consumer-platform-docs-ownership-boundary.md` | `make quality-docs-check-platform-seed-sync` |
| FR-002 | SDD-C-005 | generated-consumer one-way ownership for platform docs | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/spec.md` | `make quality-docs-check-changed` |
| FR-003 | SDD-C-005 | generated-consumer template-orphan cleanup | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/plan.md` | `make blueprint-bootstrap` |
| FR-004 | SDD-C-005 | repo-mode-aware summary sync generators | `scripts/lib/docs/sync_runtime_identity_contract_summary.py`, `scripts/lib/docs/sync_module_contract_summaries.py`, `scripts/lib/docs/repo_mode.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `docs/blueprint/architecture/decisions/ADR-20260418-generated-consumer-platform-docs-ownership-boundary.md` | `make quality-docs-check-changed` |
| NFR-SEC-001 | SDD-C-009 | repo-root scoped cleanup and sync operations | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/architecture.md` | `make infra-validate` |
| NFR-OBS-001 | SDD-C-010 | deterministic orphan diagnostics and sync summaries | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/spec.md` | `make quality-hooks-fast` |
| NFR-REL-001 | SDD-C-011 | idempotent generated-consumer cleanup convergence | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/plan.md` | `make quality-hooks-fast` |
| NFR-OPS-001 | SDD-C-010 | deterministic remediation command in `--check` mode | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/spec.md` | `make quality-docs-check-platform-seed-sync` |
| AC-001 | SDD-C-012 | generated-consumer docs checks ignore template equality drift | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/spec.md` | `make quality-docs-check-changed` |
| AC-002 | SDD-C-012 | orphan detection/check + cleanup sync | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/plan.md` | `make blueprint-bootstrap` |
| AC-003 | SDD-C-012 | generated summary scripts skip template coupling | `scripts/lib/docs/sync_runtime_identity_contract_summary.py`, `scripts/lib/docs/sync_module_contract_summaries.py` | `python3 -m unittest tests.blueprint.test_quality_contracts` | `specs/2026-04-18-docs-ownership-boundary-generated-consumer/spec.md` | `make quality-docs-check-changed` |
| AC-004 | SDD-C-012 | template-source strict checks remain green | `scripts/lib/docs/sync_platform_seed_docs.py` | `python3 scripts/lib/docs/sync_platform_seed_docs.py --check` | `docs/blueprint/architecture/decisions/ADR-20260418-generated-consumer-platform-docs-ownership-boundary.md` | `make quality-docs-check-platform-seed-sync` |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_quality_contracts tests.docs.test_orchestrate_sync`
  - `python3 scripts/lib/docs/sync_platform_seed_docs.py --check`
  - `python3 scripts/lib/docs/sync_runtime_identity_contract_summary.py --check`
  - `python3 scripts/lib/docs/sync_module_contract_summaries.py --check`
  - `make infra-validate`
  - `make quality-hooks-fast`
  - `make quality-hooks-run`
  - `make quality-hardening-review`
  - `make docs-build`
  - `make docs-smoke`
- Result summary: all executed commands passed.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Issue #128 (`blueprint-upgrade-consumer-postcheck`) remains the next ownership/upgrade safety enhancement.
