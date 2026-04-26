# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | DD-003: contract.yaml config surface | `upgrade_consumer_postcheck.py` reads `spec.upgrade.behavioral_check.extra_excluded_tokens` | `TestPostcheckReadsExtraTokensFromContract` | `blueprint/contract.yaml` example field | — |
| FR-002 | SDD-C-005 | DD-001: frozenset merge per-invocation | `run_behavioral_check`: `effective_excluded = _EXCLUDED_TOKENS \| extra_excluded_tokens` | `TestExtraExcludedTokens.test_extra_token_suppresses_unresolved_symbol` | architecture.md DD-001 | — |
| FR-003 | SDD-C-005 | DD-002: keyword-only param | `run_behavioral_check(extra_excluded_tokens: frozenset[str] = frozenset())` | `TestExtraExcludedTokens.test_absent_extra_tokens_preserves_baseline_behaviour` | spec.md FR-003 | — |
| FR-004 | SDD-C-005 | DD-002 | param docstring in `run_behavioral_check` | AC-003 test | — | — |
| FR-005 | SDD-C-005 | DD-006: non-blocking validation | token filter loop in `run_behavioral_check` | `TestExtraExcludedTokens.test_invalid_token_skipped_gracefully` | — | stderr log |
| FR-006 | SDD-C-005 | DD-004: contract_schema dataclasses | `BehavioralCheckUpgradeContract`, `UpgradeContract` in `contract_schema.py` | `TestPostcheckReadsExtraTokensFromContract` | — | — |
| FR-007 | SDD-C-005 | DD-003 | `blueprint/contract.yaml` example comment | — | contract.yaml | — |
| NFR-SEC-001 | SDD-C-009 | tokens are string identifiers only, never executed | `run_behavioral_check` — tokens used only for set membership test | no execution path in tests | architecture.md | — |
| NFR-OBS-001 | SDD-C-010 | DD-005: stderr log line | `print(f"[BEHAVIORAL-CHECK] applying {n} consumer extra excluded tokens", file=sys.stderr)` | `TestExtraExcludedTokens.test_obs_log_emitted_when_tokens_applied` | — | stderr |
| NFR-REL-001 | SDD-C-011 | DD-006 | absent/malformed key → `frozenset()` default | `TestPostcheckReadsExtraTokensFromContract.test_absent_key_yields_empty_frozenset` | — | — |
| NFR-OPS-001 | SDD-C-012 | DD-005: `extra_excluded_count` in result | `ShellBehavioralCheckResult.extra_excluded_count` | `TestExtraExcludedTokens.test_extra_excluded_count_in_result` | — | postcheck log |
| AC-001 | SDD-C-012 | DD-001, DD-002 | `run_behavioral_check(extra_excluded_tokens=frozenset({"my_custom_helper"}))` | `test_extra_token_suppresses_unresolved_symbol` | — | — |
| AC-002 | SDD-C-012 | DD-001 | absent extra tokens → base set only | `test_absent_extra_tokens_preserves_baseline_behaviour` | — | — |
| AC-003 | SDD-C-012 | DD-002 | no-arg call identical to current | existing test suite passes | — | — |
| AC-004 | SDD-C-012 | DD-001 | extra token suppresses call site | `test_extra_token_suppresses_unresolved_symbol` | — | — |
| AC-005 | SDD-C-012 | DD-006 | invalid entry skipped | `test_invalid_token_skipped_gracefully` | — | — |
| AC-006 | SDD-C-012 | DD-005 | `extra_excluded_count` field | `test_extra_excluded_count_in_result` | — | — |
| AC-007 | SDD-C-012 | NFR-OBS-001 | stderr log | `test_obs_log_emitted_when_tokens_applied` | — | — |

## Graph Linkage
- Graph file: `graph.json`
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: (to be filled post-implementation)
- Result summary: (to be filled post-implementation)
- Documentation validation: `make docs-build`, `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Value-based template scanning (parked, trigger: on-scope: blueprint) — not related to this work item.
