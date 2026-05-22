# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: bonos
- Architecture sign-off: bonos
- Security sign-off: N/A — no runtime or security surface changed
- Operations sign-off: N/A — no operational surface changed
- Missing input blocker token: none
- ADR path: none — refactor of tooling convention; no new architecture decision required
- ADR status: N/A
- SPEC_READY_EXCEPTION: refactor
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002
- Control exception rationale: SDD-C-003 through SDD-C-021 not applicable — no new feature, no new API surface, no new runtime behaviour.

## Implementation Stack Profile (Normative)
- Backend stack profile: N/A — tooling / governance files only
- Frontend stack profile: N/A
- Test automation profile: pytest (spec_scaffold unit tests updated)
- Managed-service profile: N/A
- Local-first profile: N/A

## Work Item Summary
- Slug: branch-naming-semantic
- Type: refactor
- Issue: N/A (emerged from post-merge review in session)
- Scope: `blueprint/contract.yaml`, `scripts/bin/blueprint/spec_scaffold.py`, `AGENTS.md`, skill runbooks, test

## Problem Statement
`codex/` was hardwired as the default branch prefix for all AI-driven SDD work items, regardless of whether the change was a feature, fix, refactor, or chore. This replaced semantic information (what the change is) with actor information (who created the branch), making the branch list unreadable at a glance and inconsistent with the github-flow model declared in the contract.

Additionally, `upgrade/` was used in `blueprint-consumer-upgrade/SKILL.md` but was not registered in `purpose_prefixes`, meaning upgrade branches would fail `infra-validate --branch-only`.

## Requirements (Normative)
- REQ-001: Branch names MUST use a semantic purpose prefix that matches the change type (`feature/`, `fix/`, `docs/`, `chore/`, `refactor/`, etc.).
- REQ-002: `codex/` and `copilot/` MUST be retained in `validate_contract.py`'s compat shim so existing consumer repos with old branches continue to pass infra-validate.
- REQ-003: The default prefix for auto-generated SDD branches MUST be `feature/`.
- REQ-004: `spec_scaffold.py` MUST NOT hardcode `codex/` as a preferred fallback; it MUST honour `default_prefix` from the contract, then fall back to `allowed_prefixes[0]`.
- REQ-005: `blueprint-consumer-upgrade/SKILL.md` MUST use `chore/blueprint-upgrade-<tag>` instead of `upgrade/blueprint-<tag>`.

## Acceptance Criteria (Normative)
- AC-001: `make spec-scaffold SPEC_SLUG=<slug>` creates a branch with prefix `feature/` when no `--branch` override is given.
- AC-002: `infra-validate --branch-only` MUST pass on branches with any registered semantic prefix.
- AC-003: `tests/blueprint/test_spec_scaffold.py` passes with the updated expected branch name (`feature/...`).
- AC-004: `quality-hooks-fast` exits 0 after all changes.
