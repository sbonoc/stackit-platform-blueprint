# Architecture

## Context
- Work item: 2026-04-26-issue-184-behavioral-check-extensible-exclusion
- Owner: bonos
- Date: 2026-04-26

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `_EXCLUDED_TOKENS` in `upgrade_shell_behavioral_check.py` is a hardcoded frozenset. Consumers with project-specific runtime helpers get false-positive "unresolved symbol" warnings with no workaround short of patching blueprint-managed code.
- Scope boundaries: Python and YAML changes only. No HTTP routes, managed services, or external APIs touched. All changes local to the upgrade pipeline bounded context.
- Out of scope: Removing/replacing base tokens, automated discovery of consumer helpers, UI config surface.

## Bounded Contexts and Responsibilities
- upgrade pipeline: owns `upgrade_shell_behavioral_check.py`, `upgrade_consumer_postcheck.py`, `contract_schema.py`; reads `blueprint/contract.yaml` at runtime.
- consumer repo: declares `spec.upgrade.behavioral_check.extra_excluded_tokens` in their copy of `blueprint/contract.yaml`.

## High-Level Component Design

Integration flow:
```
blueprint/contract.yaml
  └─► upgrade_consumer_postcheck.py     (reads spec.upgrade.behavioral_check.extra_excluded_tokens)
        └─► run_behavioral_check(extra_excluded_tokens=frozenset({...}))
              └─► _find_unresolved_call_sites(content, available_defs, excluded)
                    ← _EXCLUDED_TOKENS | extra_excluded_tokens  (merged per-invocation, base set unchanged)
```

Key design decisions:
- DD-001 frozenset merge, not mutation: `_EXCLUDED_TOKENS` stays a module-level constant; `effective_excluded = _EXCLUDED_TOKENS | extra_excluded_tokens` is computed locally per invocation.
- DD-002 keyword-only parameter with frozenset default: `extra_excluded_tokens: frozenset[str] = frozenset()` — all existing callers unaffected.
- DD-003 contract.yaml as the sole config surface (not env var): consistent with `skip_behavioral` and every other upgrade-pipeline config.
- DD-004 contract_schema.py additions: `BehavioralCheckUpgradeContract(extra_excluded_tokens: list[str])` + `UpgradeContract(behavioral_check: BehavioralCheckUpgradeContract)`; `BlueprintContract.upgrade` field added; absent key yields graceful default.
- DD-005 `ShellBehavioralCheckResult.extra_excluded_count: int = 0` added for operability (NFR-OPS-001 / AC-006).
- DD-006 non-blocking token validation: invalid entries (non-string, empty) silently skipped with stderr log.

## Integration and Dependency Edges
- Upstream dependencies: `blueprint/contract.yaml` consumer field (optional, absent = empty list).
- Downstream dependencies: `run_behavioral_check` result consumed by `upgrade_consumer_postcheck.py` and written to residual report.
- Data/API/event contracts touched: `contract.yaml` schema extended with optional `spec.upgrade.behavioral_check.extra_excluded_tokens`.

## Non-Functional Architecture Notes
- Security: token values are never executed; they are only compared against string identifiers extracted from shell scripts. No injection vector.
- Observability: `[BEHAVIORAL-CHECK] applying N consumer extra excluded tokens` emitted to stderr when N > 0 (NFR-OBS-001).
- Reliability and rollback: absent or malformed field degrades gracefully to base set (NFR-REL-001); pipeline never blocked by this feature.
- Monitoring/alerting: `extra_excluded_count` in `ShellBehavioralCheckResult` visible in postcheck log output.

## Risks and Tradeoffs
- Risk 1: `contract_schema.py` uses a hand-rolled YAML parser; adding `spec.upgrade` as a new top-level key under `spec` requires the loader to handle an optional new branch. Mitigated by making `upgrade` key optional with graceful default in the load function.
- Tradeoff 1: contract-yaml approach requires more files changed vs. an env var; the benefit is schema visibility, version control, and consistency with established patterns.
