# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-023, SDD-C-024 | Newline-only parsing strategy in `parse_literal_pairs()` | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — `parse_literal_pairs()` | `tests/infra/test_runtime_credentials_eso.py` — new comma-in-value test | `docs/platform/consumer/runtime_credentials_eso.md` | reconcile artifact `_reconcile_state` |
| FR-002 | SDD-C-005, SDD-C-010 | `log_warn` on parse failure (visible diagnostic regardless of REQUIRED setting) | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — `parse_literal_pairs()` + `log_warn` calls | `tests/infra/test_runtime_credentials_eso.py` — test asserts comma-separated input is rejected with log_warn | none | stderr log output |
| FR-003 | SDD-C-011 | Format documentation update | `docs/platform/consumer/runtime_credentials_eso.md`; `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` | `make docs-build && make docs-smoke` | both doc files | none |
| FR-004 | SDD-C-010 | Error message references newline-separated as sole accepted format | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — `record_reconcile_issue` call | `tests/infra/test_runtime_credentials_eso.py` — error path test | none | `artifacts/infra/runtime_credentials/_reconcile_issues.json` |
| NFR-SEC-001 | SDD-C-009 | Value verbatim preservation after `=` sign | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` — `value="${pair#*=}"` (greedy strip from left) | new comma-in-value test asserts full value in rendered secret manifest | none | Kubernetes Secret `runtime-credentials-source` |
| NFR-OBS-001 | SDD-C-010 | `record_reconcile_issue` call preserved on parse failure | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | `test_required_mode_fails_on_invalid_literal_contract` | none | `artifacts/infra/runtime_credentials/_reconcile_issues.json` |
| AC-001 | SDD-C-012, SDD-C-023, SDD-C-024 | New positive-path test for comma-in-value | `tests/infra/test_runtime_credentials_eso.py` | new test passes | none | none |
| AC-002 | SDD-C-012, SDD-C-023 | Comma-separated input rejected with non-zero exit and log_warn | `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` | new test asserts comma-separated input returns non-zero and emits log_warn | none | none |
| AC-003 | SDD-C-012, SDD-C-023 | Positive-path assertion: full value preserved verbatim | `tests/infra/test_runtime_credentials_eso.py` | new test asserts rendered secret contains full value (including comma) base64-encoded | none | none |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001
  - AC-001, AC-002, AC-003

## Validation Summary
- Required bundles executed: pending implementation
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
- Follow-up 1: Consumer workaround in `provision_deploy_local_marketplace.sh` becomes a no-op after this fix ships; consumer can remove the workaround patches in a follow-up cleanup.
- Follow-up 2: `docs/platform/consumer/troubleshooting.md` usage examples for `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` may also reference comma-separated format — update in Document phase if found.
