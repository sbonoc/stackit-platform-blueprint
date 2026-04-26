# ADR-20260426-behavioral-check-extensible-exclusion: Extend shell behavioral check exclusion set via contract.yaml

## Metadata
- Status: proposed
- Date: 2026-04-26
- Owners: sbonoc
- Related spec path: specs/2026-04-26-issue-184-behavioral-check-extensible-exclusion/

## Business Objective and Requirement Summary
- Business objective: allow consumers to suppress project-specific false-positive unresolved-symbol warnings from the shell behavioral check without patching blueprint-managed code.
- Functional requirements summary:
  - read optional `spec.upgrade.behavioral_check.extra_excluded_tokens` array from `blueprint/contract.yaml`.
  - merge consumer tokens with the base `_EXCLUDED_TOKENS` set per invocation without mutating the base set.
  - expose `extra_excluded_count` in `ShellBehavioralCheckResult` for operability.
- Non-functional requirements summary:
  - absent or malformed field must degrade gracefully to base set (non-blocking).
  - token values are never executed; they are string identifiers only (no injection vector).
  - emit a `[BEHAVIORAL-CHECK]` log line when extra tokens are applied.
- Desired timeline: immediate.

## Decision Drivers
- Driver 1: `_EXCLUDED_TOKENS` is hardcoded; consumers with non-standard runtime helpers have no workaround.
- Driver 2: config surface must be consistent with existing upgrade-pipeline patterns (contract.yaml, not env vars).
- Driver 3: base set must remain immutable to prevent shared-state bugs.

## Options Considered
- Option A: read tokens from `blueprint/contract.yaml` `spec.upgrade.behavioral_check.extra_excluded_tokens` (schema-validated, version-controlled, consistent with existing pipeline config pattern).
- Option B: read tokens from a dedicated env var `BEHAVIORAL_CHECK_EXCLUDED_TOKENS` (simpler, but bypasses schema, invisible to the residual report, inconsistent with existing patterns).

## Recommended Option
- Selected option: Option A
- Rationale: contract.yaml is the single source of truth for all upgrade-pipeline consumer configuration; it is schema-validated and version-controlled. Env var approach would be invisible to schema validators and inconsistent with `skip_behavioral` and every other pipeline config field.

## Consequences
- Positive: consumers can suppress false positives without touching blueprint code; tokens are version-controlled alongside the contract.
- Negative: requires `contract_schema.py` additions (new optional nested key under `spec.upgrade`); the hand-rolled YAML parser must handle the new branch gracefully.
- Neutral: no change to the base `_EXCLUDED_TOKENS` set; all existing callers unaffected due to keyword-only default.
