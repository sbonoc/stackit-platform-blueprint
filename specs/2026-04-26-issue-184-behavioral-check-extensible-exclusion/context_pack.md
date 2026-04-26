# Work Item Context Pack

## Context Snapshot
- Work item: 2026-04-26-issue-184-behavioral-check-extensible-exclusion
- Track: blueprint
- SPEC_READY: true
- ADR path: none
- ADR status: n/a

## Problem
`_EXCLUDED_TOKENS` in `upgrade_shell_behavioral_check.py` is a hardcoded frozenset of ~80 shell builtins/runtime helpers. Consumers with project-specific runtime helpers (e.g. `setup_my_db`) get false-positive "unresolved symbol" warnings with no workaround except patching blueprint-managed code.

## Solution Summary
Add optional `spec.upgrade.behavioral_check.extra_excluded_tokens: []` array to `blueprint/contract.yaml`. The postcheck reads this field and passes it as `extra_excluded_tokens: frozenset[str]` to `run_behavioral_check`. Inside that function, `effective_excluded = _EXCLUDED_TOKENS | extra_excluded_tokens` is computed per-invocation (base set never mutated).

## Key Files
| File | Role |
|---|---|
| `scripts/lib/blueprint/upgrade_shell_behavioral_check.py` | Add `extra_excluded_tokens` param + `extra_excluded_count` to result |
| `scripts/lib/blueprint/upgrade_consumer_postcheck.py` | Read contract field, pass to `run_behavioral_check` |
| `scripts/lib/blueprint/contract_schema.py` | Add `BehavioralCheckUpgradeContract`, `UpgradeContract`, extend `BlueprintContract` |
| `blueprint/contract.yaml` | Add example commented field |
| `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | Add callout in postcheck step |
| `tests/blueprint/test_upgrade_shell_behavioral_check.py` | Add `TestExtraExcludedTokens` + `TestPostcheckReadsExtraTokensFromContract` |

## Critical Implementation Detail
`_find_unresolved_call_sites` currently reads `_EXCLUDED_TOKENS` directly from module scope. The `run_behavioral_check` function must pass the merged `effective_excluded` set into `_find_unresolved_call_sites` — this requires adding an `excluded` parameter to that private function, or computing the union before calling it and using a local variable. Check the actual call path before assuming which approach is simpler.

## Guardrail Controls
- Applicable control IDs: SDD-C-001 through SDD-C-021

## Required Commands
- `make quality-sdd-check`
- `make quality-hooks-run`
- `pytest tests/blueprint/test_upgrade_shell_behavioral_check.py`

## Artifact Index
- `architecture.md`
- `spec.md`
- `plan.md`
- `tasks.md`
- `traceability.md`
- `graph.json`
- `evidence_manifest.json`
- `pr_context.md`
- `hardening_review.md`
