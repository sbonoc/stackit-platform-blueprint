# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- ADR path: docs/blueprint/architecture/decisions/ADR-20260426-behavioral-check-extensible-exclusion.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: none
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Consumers can suppress project-specific false-positive function-resolution warnings from the shell behavioral check without patching blueprint-managed code. This unblocks adoption of the upgrade pipeline for repos with non-standard runtime helpers.
- Success metric: A consumer can declare `extra_excluded_tokens` in `blueprint/contract.yaml` and the behavioral check omits those tokens without any other code change; zero new false positives in existing repos (tokens not in the list are unaffected).

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST read the optional array field `spec.upgrade.behavioral_check.extra_excluded_tokens` from `blueprint/contract.yaml` at behavioral-check runtime; if absent or empty, behaviour is identical to the current baseline.
- FR-002 MUST merge `extra_excluded_tokens` with `_EXCLUDED_TOKENS` before running symbol resolution so that any token present in the base set or the extra set is treated as resolved; the base set MUST NOT be mutated.
- FR-003 MUST pass `extra_excluded_tokens` as a parameter to `run_behavioral_check`; the function signature extension MUST be backward-compatible (keyword-only with a frozenset default of `frozenset()`).
- FR-004 MUST add `extra_excluded_tokens` as a keyword-only parameter to `run_behavioral_check` with default `frozenset()` and document it in the docstring.
- FR-005 MUST validate that each token in `extra_excluded_tokens` is a non-empty string; invalid entries MUST be silently skipped (non-blocking, logged to stderr).
- FR-006 MUST support schema-level access via `contract_schema.py`: add `BehavioralCheckUpgradeContract` dataclass with `extra_excluded_tokens: list[str]` and wire it into `BlueprintContract` under `upgrade.behavioral_check`.
- FR-007 MUST update `blueprint/contract.yaml` in the blueprint source repo to document the optional field with an empty list default as a reference example for consumers.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT allow `extra_excluded_tokens` to widen scope beyond symbol name strings; no shell execution or file read is triggered by the token values.
- NFR-OBS-001 MUST emit a `[BEHAVIORAL-CHECK]` prefixed log line listing the count of consumer extra tokens applied when the list is non-empty.
- NFR-REL-001 MUST NOT fail the pipeline if `extra_excluded_tokens` is missing, malformed, or contains invalid entries; the check MUST degrade gracefully to the base exclusion set.
- NFR-OPS-001 MUST surface `extra_excluded_tokens` count in the behavioral check result dict / ShellBehavioralCheckResult so operators can confirm tokens were applied.

## Normative Option Decision
- Option A: Read tokens from `blueprint/contract.yaml` `spec.upgrade.behavioral_check.extra_excluded_tokens` (structured config, schema-validated, consistent with existing contract pattern).
- Option B: Read tokens from a dedicated env var `BEHAVIORAL_CHECK_EXCLUDED_TOKENS` (simpler short-term, but not persisted in contract, invisible to schema validators).
- Selected option: OPTION_A
- Rationale: Contract-yaml is the established single source of truth for consumer configuration in this codebase; it is schema-validated, version-controlled, and surfaced in the upgrade pipeline automatically. Env var approach would bypass schema and be invisible to the residual report.

## Contract Changes (Normative)
- Config/Env contract: `blueprint/contract.yaml` gains an optional `spec.upgrade.behavioral_check.extra_excluded_tokens` array field (default: absent = empty list). No required env var changes.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — `make blueprint-upgrade-consumer` is unaffected; Stage 9 postcheck reads the contract automatically.
- Docs contract: `blueprint-consumer-upgrade` SKILL.md postcheck step gains a callout describing how to add consumer exclusion tokens.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: given a `.sh` file that calls a consumer function `my_custom_helper`, with `extra_excluded_tokens: [my_custom_helper]` in contract.yaml, the behavioral check result contains zero unresolved symbols for that token.
- AC-002 MUST: given the same `.sh` file but with `extra_excluded_tokens` absent from contract.yaml, the behavioral check flags `my_custom_helper` as unresolved — confirming the base set is unchanged.
- AC-003 MUST: `run_behavioral_check` called with no `extra_excluded_tokens` argument produces identical results to the current baseline for all existing tests.
- AC-004 MUST: `run_behavioral_check` called with `extra_excluded_tokens=frozenset({"my_fn"})` and a script containing only `my_fn` as a call site produces `status="pass"` and zero unresolved symbols.
- AC-005 MUST: an invalid (non-string) entry in `extra_excluded_tokens` is skipped without raising an exception; the remaining valid tokens are applied.
- AC-006 MUST: `ShellBehavioralCheckResult` exposes `extra_excluded_count: int` equal to `len(extra_excluded_tokens)` (after filtering invalids) so operators can verify.
- AC-007 MUST: `NFR-OBS-001` — when extra tokens are applied, a log line `[BEHAVIORAL-CHECK] applying N consumer extra excluded tokens` appears on stderr.

## Informative Notes (Non-Normative)
- Context: `_EXCLUDED_TOKENS` is a frozenset of ~80 shell builtins, OS commands, and blueprint runtime helpers hardcoded in `upgrade_shell_behavioral_check.py`. Consumers with project-specific runtime helpers (e.g. `setup_my_db`) get false-positive "unresolved symbol" warnings that block adoption without any workaround short of patching blueprint code.
- Tradeoffs: Contract-yaml approach requires `contract_schema.py` changes; env-var approach would be simpler but invisible to schema and inconsistent with existing patterns.
- Clarifications: Token validation is intentionally minimal (non-empty string) — semantic validation (e.g. valid shell identifier) would add complexity for marginal safety gain given these tokens are never executed.

## Explicit Exclusions
- Removing or replacing any token from the base `_EXCLUDED_TOKENS` set is out of scope; this issue is additive only.
- Automated discovery of consumer helpers from source files is out of scope.
- UI or HTTP surface for configuring excluded tokens is out of scope.
