# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-011 | — | Environment Variables table | `docs/platform/modules/identity-aware-proxy/README.md` | AC-003: README has env var table | AC-003 | — |
| FR-002 | SDD-C-011 | — | Make Targets table | `docs/platform/modules/identity-aware-proxy/README.md` | AC-004: README has make targets table | AC-004 | — |
| FR-003 | SDD-C-011 | — | Provisioning Lifecycle section | `docs/platform/modules/identity-aware-proxy/README.md` | AC-005: README has provisioning lifecycle section | AC-005 | — |
| FR-004 | SDD-C-009, SDD-C-011 | — | Security section | `docs/platform/modules/identity-aware-proxy/README.md` | AC-006: README has security section | AC-006 | — |
| FR-005 | SDD-C-011 | — | Teardown section | `docs/platform/modules/identity-aware-proxy/README.md` | AC-007: README has teardown section | AC-007 | — |
| FR-006 | SDD-C-011 | — | Bootstrap template mirror | `scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md` | AC-002: quality-docs-check-changed exits 0 | AC-002 | — |
| NFR-SEC-001 | SDD-C-009 | — | No secret keys in state file; Security section prose | `scripts/bin/infra/identity_aware_proxy_plan.sh`, `scripts/bin/infra/identity_aware_proxy_smoke.sh` | AC-006: security section documents non-persistence | — | — |
| NFR-A11Y-001 | — | — | N/A — no UI surfaces | — | — | — | — |
| NFR-OBS-001 | — | — | N/A — no new observability surfaces | — | — | — | — |
| NFR-REL-001 | — | — | `IDENTITY_AWARE_PROXY_ENABLED=false` guard on all 5 scripts | `scripts/bin/infra/identity_aware_proxy_{plan,apply,deploy,smoke,destroy}.sh` | AC-008, AC-009: skip exit 0 verified | — | — |
| NFR-OPS-001 | SDD-C-010 | — | State file key contract in Make Targets table | `docs/platform/modules/identity-aware-proxy/README.md` | AC-004: make targets table documents state keys | AC-004 | — |
| AC-001 | — | — | — | — | `make quality-hooks-fast` exits 0 | — | — |
| AC-002 | SDD-C-011 | — | — | — | `make quality-docs-check-changed` exits 0 | AC-002 | — |
| AC-003 | SDD-C-011 | — | — | — | grep env var table in README | AC-003 | — |
| AC-004 | SDD-C-010, SDD-C-011 | — | — | — | grep make targets table in README | AC-004 | — |
| AC-005 | SDD-C-011 | — | — | — | grep provisioning lifecycle section in README | AC-005 | — |
| AC-006 | SDD-C-009, SDD-C-011 | — | — | — | grep security section in README | AC-006 | — |
| AC-007 | SDD-C-011 | — | — | — | grep teardown section in README | AC-007 | — |
| AC-008 | — | — | — | — | `IDENTITY_AWARE_PROXY_ENABLED=false make infra-identity-aware-proxy-plan` exits 0 | — | — |
| AC-009 | — | — | — | — | `IDENTITY_AWARE_PROXY_ENABLED=false make infra-identity-aware-proxy-smoke` exits 0 | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006
  - NFR-SEC-001, NFR-A11Y-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles: quality-hooks-fast, quality-docs-check-changed, skip-path plan, skip-path smoke
- Result summary: pending — to be populated in T-306

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- None at intake time.
