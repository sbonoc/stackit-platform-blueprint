# ADR: SDD scaffold placeholder guard in check_sdd_assets.py (Issue #152)

- **Date**: 2026-04-22
- **Status**: accepted
- **Issue**: #152

## Context

`make quality-hardening-review` runs `check_sdd_assets.py` to validate SDD work-item artifacts. After PR #151 it was found that `architecture.md` and `context_pack.md` can ship with all fields at scaffold placeholder values (empty after the colon) and the gate still passes. `check_sdd_assets.py` checked `context_pack.md` only for non-emptiness and section presence; `architecture.md` was not checked at all. Both scaffold templates satisfy those checks without any content filled in.

## Decision

Extend `check_sdd_assets.py` to validate required fields in `context_pack.md` and `architecture.md` using a **required-field allowlist declared in `blueprint/contract.yaml`**. For each document, a list of required field names is declared in the contract. The validator reads those lists and asserts each field has a non-empty value. A value of "none" is accepted; only a completely blank value triggers a violation.

## Options Considered

**Option A — required-field allowlist (selected)**: declare required field names per document in `blueprint/contract.yaml`; validator reads the list and asserts each has a non-empty value after the colon. Precise, extensible, no false positives on intentionally sparse documents.

**Option B — heuristic line-scan**: scan for lines ending with a bare `:` (scaffold placeholder pattern). Simpler but risks false positives on documents that intentionally use short or blank trailing values, and is harder to extend cleanly.

## Consequences

- `make quality-hardening-review` now fails when required fields are empty, giving a violation message that names the document path and the specific field.
- Required field lists are declared in `blueprint/contract.yaml` under the SDD contract, so they can be extended without modifying the validator.
- No impact on existing valid work-item documents — all populated fields (including "none") satisfy the check.
