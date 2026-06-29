# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | — | `architecture.md` § Bounded Contexts (loader); ADR-issue-373 § Component decisions | `scripts/lib/factory/orchestrator/core/loader.py` | T-101 | ADR-issue-373-orchestrator-core.md | DispatchMatrixError fields (NFR-OPS-001) |
| FR-002 | SDD-C-005 | — | `architecture.md` § High-Level Component Design; ADR-issue-373 § Component decisions | `scripts/lib/factory/orchestrator/core/convergence.py` | T-102 | ADR-issue-373-orchestrator-core.md | ConvergenceError (NFR-OPS-001) |
| FR-003 | SDD-C-005, SDD-C-024 | — | `architecture.md` § Bounded Contexts (schema validator); ADR-issue-373 § Component decisions | `scripts/lib/factory/orchestrator/core/validator.py` | T-103 | ADR-issue-373-orchestrator-core.md | SchemaValidationError fields (NFR-OPS-001) |
| FR-004 | SDD-C-005 | — | `architecture.md` § Bounded Contexts (predicate registry); ADR-issue-373 § Predicate field on MatrixRow | `scripts/lib/factory/orchestrator/core/predicates.py` | T-104 | ADR-issue-373-orchestrator-core.md | PredicateRegistryError fields (NFR-OPS-001) |
| NFR-SEC-001 | SDD-C-009 | — | `architecture.md` § Non-Functional Architecture Notes (Security) | All core module files — no credential/env/network access | T-103 (no-write assertion) | ADR-issue-373 § Consequences | N/A |
| NFR-OBS-001 | SDD-C-010 | — | `architecture.md` § Non-Functional Architecture Notes (Observability) | `scripts/lib/factory/orchestrator/core/exceptions.py` | T-103 (no stdout/stderr write) | ADR-issue-373 § Consequences | Caller (#361.2) owns log/metric emission |
| NFR-REL-001 | SDD-C-011 | — | `architecture.md` § Non-Functional Architecture Notes (Reliability) | Loader fail-fast; `_locked` flag in PredicateRegistry | T-101 (fail-fast), T-104 (immutability) | ADR-issue-373 § Consequences | N/A |
| NFR-OPS-001 | SDD-C-010 | — | `architecture.md` § Non-Functional Architecture Notes (Monitoring) | `context: dict` field on all four exception types | T-101, T-104 (exception context assertions) | ADR-issue-373 § Consequences | Operator diagnostic routing |
| NFR-A11Y-001 | — | N/A | N/A — headless library | N/A | T-A01 (N/A confirmed) | N/A | N/A |
| AC-001 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (loader) | `scripts/lib/factory/orchestrator/core/loader.py` | T-101 | — | — |
| AC-002 | SDD-C-012 | — | `architecture.md` § High-Level Component Design | `scripts/lib/factory/orchestrator/core/convergence.py` | T-102 | — | — |
| AC-003 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (schema validator) | `scripts/lib/factory/orchestrator/core/validator.py` | T-103 | — | — |
| AC-004 | SDD-C-012 | — | `architecture.md` § Bounded Contexts (predicate registry) | `scripts/lib/factory/orchestrator/core/predicates.py` | T-104 | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004

## Validation Summary
- Required bundles executed: pending (post-implementation)
- Result summary: pending
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Embedding-based deduplication — tracked in backlog `proposal(issue-368-factory-cost-telemetry-routing-fixture): embedding-based router implementation`.
