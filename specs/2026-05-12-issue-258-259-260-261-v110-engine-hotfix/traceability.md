# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-024 | N/A | Context A — Contract coverage audit | `blueprint/contract.yaml` (`init_managed`, `conditional_scaffold` entries); `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` (mirror) | `tests/infra/test_upgrade_contract_coverage_issue_258.py` | N/A (tooling fix; no user-facing behavior change) | `make infra-validate` PASS |
| FR-002 | SDD-C-005, SDD-C-024 | N/A | Context B — Validate target filtering | `scripts/lib/blueprint/upgrade_consumer_validate.py` (`_get_effective_validation_targets`, `_GENERATED_CONSUMER_SKIP_TARGETS`) | `tests/infra/test_upgrade_consumer_validate_issue_260.py` | `docs/blueprint/architecture/execution_model.md` (behavioral check section); `docs/platform/consumer/troubleshooting.md` (v1.10.0 entry) | `make quality-hooks-fast` PASS |
| FR-003 | SDD-C-005, SDD-C-024 | N/A | Context C — Volatile artifact names | `scripts/lib/blueprint/upgrade_fresh_env_gate.py` (`_VOLATILE_ARTIFACT_NAMES` addition) | `tests/infra/test_upgrade_fresh_env_gate_issue_261.py` | `docs/blueprint/architecture/execution_model.md` (fresh-env-gate volatile set description); `docs/platform/consumer/troubleshooting.md` (v1.10.0 entry) | `make quality-hooks-fast` PASS |
| FR-004 | SDD-C-005, SDD-C-024 | N/A | Context D — Transitive behavioral check | `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` (`_collect_defined_functions_transitive`, `_EXCLUDED_TOKENS` additions) | `tests/infra/test_upgrade_shell_behavioral_check_issue_259.py` (3 fixture classes) | `docs/blueprint/architecture/execution_model.md` (transitive BFS + `uv`/`validate` exclusions); `docs/platform/consumer/troubleshooting.md` (v1.10.0 entry) | `make quality-hooks-fast` PASS |
| NFR-SEC-001 | SDD-C-009 | N/A | N/A — no security surface | N/A | N/A | N/A | N/A |
| NFR-OBS-001 | SDD-C-010 | N/A | All four fixed modules | Existing WARNING/ERROR log lines preserved; JSON schemas unchanged | Verified by full pytest suite (no schema-breaking assertions fail) | N/A | N/A |
| NFR-REL-001 | SDD-C-008 | N/A | All four fixed modules | Backward-compatible changes only; no existing passing check made failing | Full `tests/infra/` pytest suite PASS (324 tests) | N/A | N/A |
| NFR-OPS-001 | SDD-C-010 | N/A | All regression tests | All tests use pytest fixtures; no network or cluster access | `uv run python3 -m pytest tests/infra/` with no external dependencies | N/A | N/A |
| AC-001 | SDD-C-012 | N/A | Context A | `blueprint/contract.yaml` + `audit_source_tree_coverage` | `tests/infra/test_upgrade_contract_coverage_issue_258.py` PASS | N/A | `audit_source_tree_coverage` returns `uncovered_source_files_count=0` |
| AC-002 | SDD-C-012 | N/A | Context B | `upgrade_consumer_validate.py` filter | `tests/infra/test_upgrade_consumer_validate_issue_260.py` PASS | N/A | `VALIDATION_TARGETS` excludes `blueprint-template-smoke` for `generated-consumer` mode |
| AC-003 | SDD-C-012 | N/A | Context C | `upgrade_fresh_env_gate.py` volatile set | `tests/infra/test_upgrade_fresh_env_gate_issue_261.py` PASS | N/A | `compute_artifact_checksum_divergences` returns `[]` for path-only diff |
| AC-004 | SDD-C-012 | N/A | Context D | `upgrade_shell_behavioral_check.py` transitive resolver | `tests/infra/test_upgrade_shell_behavioral_check_issue_259.py` PASS (3 fixtures) | N/A | `behavioral_check_failures_total=0` for blueprint-managed scripts |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004

## Validation Summary
- Required bundles executed: 2026-05-12
- Result summary:
  - `make infra-validate` → PASS (contract validation passed, no drift)
  - `make quality-hooks-run` → PASS except `blueprint-template-smoke` (pre-existing bash 3 vs bash 4 `declare -A` incompatibility on macOS; verified pre-existing on main branch; no new failures introduced)
  - `uv run python3 -m pytest tests/infra/` → PASS (324 tests, 0 failures)
  - `make docs-build` → PASS
  - `make docs-smoke` → PASS
  - `make quality-hardening-review` → PASS
- Documentation validation:
  - `make docs-build` → PASS (2026-05-12)
  - `make docs-smoke` → PASS (2026-05-12)

## File Checksums (SHA-256, 2026-05-12)
| File | SHA-256 |
|---|---|
| `tests/infra/test_upgrade_contract_coverage_issue_258.py` | `3d211596c94ce3b7fd552128da94d0176d416846274938a9dd689d403e5b2629` |
| `tests/infra/test_upgrade_consumer_validate_issue_260.py` | `7354499cf5a01fd478057a3d69e39d6e7ac4af030af8c38442ce7ee669aed5db` |
| `tests/infra/test_upgrade_fresh_env_gate_issue_261.py` | `d3259ce322f99092fdd4b29ded3b5280218c1187d1912e9f13d78ef2187addd2` |
| `tests/infra/test_upgrade_shell_behavioral_check_issue_259.py` | `f8e6892513e1bebc576834ffc04321d20e18c6c4117a99efcd8b7f053a1e3319` |
| `scripts/lib/blueprint/upgrade_consumer_validate.py` | `4ac9df635819965f789eda2a45e7993ceefc6aef15b2edebee8d78cb2dafad35` |
| `scripts/lib/blueprint/upgrade_fresh_env_gate.py` | `0a27d866d0989f25b22cfdf4c6d66799248c7571bfbf7a1221e52436a072daa4` |
| `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` | `85d79d60c0e1a924cfca182fe3aa9c4e1c3e30e48f4cd336b5aa7af13054f91a` |
| `blueprint/contract.yaml` | `0d8f6032006586102f006b61704235773fe6d4c9d01a3ac1a163c92c97dc42cf` |
| `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` | `0d8f6032006586102f006b61704235773fe6d4c9d01a3ac1a163c92c97dc42cf` |

Note: `blueprint/contract.yaml` and its bootstrap template have identical checksums — confirming template drift was resolved.

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consumers currently relying on the workarounds in their `blueprint/contract.yaml` (`extra_excluded_tokens`, local patches) MUST remove them after adopting the fixed blueprint version. No automated migration is provided — the workaround removal is documented in the consumer upgrade runbook.
