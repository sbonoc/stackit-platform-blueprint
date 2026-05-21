# PR Context

## Summary
Refactoring of the branch naming convention. `codex/` was hardwired as the default prefix for all AI-driven SDD branches, replacing semantic information (what the change is) with actor information (who created it). This PR restores the github-flow semantic model by making `feature/` the default and retiring `codex/`/`copilot/` from the registered prefix list (compat shim kept so old consumer branches remain valid). Also fixes `upgrade/` in the consumer upgrade skill, which was unregistered and would have failed `infra-validate --branch-only`.

## Requirement and Contract Coverage

| Requirement | Implementation | Evidence |
|---|---|---|
| REQ-001 — semantic prefix required | `blueprint/contract.yaml` + bootstrap mirror: removed `codex/`, `copilot/`; `default_prefix: feature/` | AC-001: `test_scaffold_creates_dedicated_branch_by_default` passes with `feature/` branch |
| REQ-002 — compat shim retained | `validate_contract.py:51` `COMPAT_BRANCH_PURPOSE_PREFIXES` unchanged | `infra-validate` passes on main branch (passive check) |
| REQ-003 — default prefix is `feature/` | `blueprint/contract.yaml:default_prefix: feature/` | AC-001 |
| REQ-004 — no hardcoded `codex/` in scaffold | `spec_scaffold.py:_resolve_branch_prefix()` — hardcoded fallback removed | AC-003: 3 spec_scaffold tests pass |
| REQ-005 — upgrade skill uses `chore/` | `blueprint-consumer-upgrade/SKILL.md` command sequence updated | `quality-hooks-fast` pass |

## Key Reviewer Files
- `blueprint/contract.yaml` — `purpose_prefixes` and `default_prefix` change
- `scripts/bin/blueprint/spec_scaffold.py` — `_resolve_branch_prefix()` — 2 lines removed
- `AGENTS.md` step 4 — updated default branch example
- `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` — AUTO-SCAFFOLD block updated
- `.agents/skills/blueprint-consumer-upgrade/SKILL.md` — `upgrade/` → `chore/` in command sequence
- `tests/blueprint/test_spec_scaffold.py` — expected branch name updated from `codex/` to `feature/`

## Validation Evidence
- `python3 -m pytest tests/blueprint/test_spec_scaffold.py -x -q` — 3 passed
- `make quality-hooks-fast` — all 10 checks pass (shellcheck, quality-sdd-check-all, quality-docs-check-changed, infra-validate, infra-contract-test-fast, and 5 others)
- No behaviour change: `validate_contract.py` compat shim unchanged; existing `codex/` and `copilot/` branches on consumer repos continue to pass `infra-validate --branch-only`

## Risk and Rollback
- Risk: very low — no runtime, infra, or application code changed. Only tooling convention and documentation updated.
- Rollback: revert the commit. Restore `codex/` and `copilot/` to `purpose_prefixes` in both contracts, restore `default_prefix: codex/`, restore the `codex/`-first fallback in `_resolve_branch_prefix()`.
- Consumer impact: none — the compat shim in `validate_contract.py` ensures old `codex/` branches on all consumer repos remain valid.

## Deferred Proposals (Not Implemented)
- none
