# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- ADR path: docs/platform/architecture/decisions/ADR-20260428-issue-234-literal-pairs-newline-format.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021, SDD-C-023, SDD-C-024
- Control exception rationale: SDD-C-018 not applicable — this work item IS the upstream fix; SDD-C-022 not applicable — no HTTP route or API endpoint changes

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
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
- Business outcome: Restore correct behavior for `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` when any value contains a comma, eliminating a silent failure cascade that prevents ESO secret reconciliation and breaks all app deployments in affected environments.
- Success metric: `parse_literal_pairs()` correctly parses a newline-separated entry whose value contains a comma (such as a data URI); existing comma-separated consumers with simple values continue to work unchanged.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST update `parse_literal_pairs()` in `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` to accept newline (`\n`) as the primary delimiter: when the input contains one or more newline characters, EXACTLY ONE splitting strategy SHALL be applied — split on newlines.
- FR-002 MUST preserve backward compatibility: when the input string contains no newline characters, `parse_literal_pairs()` SHALL split on commas (legacy format, safe only when values contain no commas).
- FR-003 MUST update documentation in `docs/platform/consumer/runtime_credentials_eso.md` and its bootstrap template copy to declare newline-separated format as the recommended format and mark comma-separated as a legacy format restricted to values without commas.
- FR-004 MUST update the `record_reconcile_issue` error message in `reconcile_eso_runtime_secrets.sh` to reference both accepted formats.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT truncate or split any value at internal commas; after the first `=` separator, the remainder of the pair string SHALL be treated as the value verbatim, preserving commas, base64 padding, and data-URI schemes intact.
- NFR-OBS-001 MUST continue to emit a structured reconcile issue via `record_reconcile_issue` on parse failure; the error message MUST describe the corrected format (newline-primary, comma-legacy).

## Normative Option Decision
- Option A: Newline-primary with comma fallback — when input contains `\n`, split on newlines; otherwise split on commas (backward-compatible with existing consumers whose values contain no commas).
- Option B: Newline-only strict — reject all comma-separated input, requiring every caller to migrate.
- Selected option: OPTION_A
- Rationale: The consumer workaround already uses newline-separated format. Option A converges existing workaround consumers and does not require a migration window. Option B breaks consumers that have not yet applied the workaround.

## Contract Changes (Normative)
- Config/Env contract: `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` — recommended format changes from `key=value,key2=value2` to newline-separated `key=value\nkey2=value2`; comma-separated remains valid when values contain no commas.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: `docs/platform/consumer/runtime_credentials_eso.md` and bootstrap template `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` MUST reflect the corrected format.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/234
- Temporary workaround path: `scripts/bin/platform/infra/provision_deploy_local_marketplace.sh` (consumer) — changed serializer to newline-separated output; `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` (consumer) — updated `parse_literal_pairs()` to accept both formats.
- Replacement trigger: Blueprint ships newline-primary `parse_literal_pairs()` in `reconcile_eso_runtime_secrets.sh`; consumer workaround patches become no-ops and can be removed.
- Workaround review date: 2026-07-28

## Normative Acceptance Criteria
- AC-001 MUST pass: a new test in `tests/infra/test_runtime_credentials_eso.py` exercises `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` with a newline-separated entry whose value contains a comma (e.g., `NUXT_OIDC_TOKEN_KEY=data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE=`); the reconcile MUST succeed and the rendered secret MUST contain the full value without truncation.
- AC-002 MUST pass: the existing test `test_dry_run_reconcile_writes_success_state_and_renders_source_secret` (comma-separated `username=dev-user,password=dev-password`) MUST continue to pass unchanged.
- AC-003 MUST pass: a unit-level shell test MUST assert that `parse_literal_pairs` called with a newline-separated string returns each `key=value` pair as a single output line, with the value preserved verbatim after the `=`.

## Informative Notes (Non-Normative)
- Context: The comma-in-value failure is silent — `parse_literal_pairs()` returns 1, `record_reconcile_issue` records it, but with `RUNTIME_CREDENTIALS_REQUIRED=false` (the default) the reconcile continues and marks the run as successful while the source secret was never created. All downstream ExternalSecrets then remain NotReady and ArgoCD cannot sync.
- Tradeoffs: Option A (chosen) calls `_quality_changed_paths` twice in degenerate git-failure cases (once in caller, once inside gate), but this is negligible compared to the correctness guarantee.
- Clarifications: none

## Explicit Exclusions
- Changing the env var name `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` — out of scope.
- Adding escaping support (e.g., `\,` to escape commas in the legacy format) — out of scope; newline-primary is the correct fix.
- Modifying `apply_optional_module_secret_from_literals` or `render_optional_module_secret_manifests` — they already accept variadic `key=value` arguments and are unaffected.
