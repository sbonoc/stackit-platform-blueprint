# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
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
- ADR path: docs/platform/architecture/decisions/ADR-20260428-issue-234-literal-pairs-newline-format.md
- ADR status: approved

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
- Success metric: `parse_literal_pairs()` correctly parses a newline-separated entry whose value contains a comma (such as a data URI); comma-separated input is rejected with a visible diagnostic regardless of `RUNTIME_CREDENTIALS_REQUIRED` value.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST update `parse_literal_pairs()` in `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` to accept ONLY newline-separated `key=value` pairs; EXACTLY ONE pair-parsing/splitting strategy SHALL be applied for accepted input — split on newlines. Implementations are permitted to inspect the raw, unsplit input for commas or similar markers solely to detect and reject deprecated comma-separated input with diagnostics, but MUST NOT parse by splitting on commas or otherwise support comma-separated input.
- FR-002 MUST emit `log_warn` on any `parse_literal_pairs()` failure, in addition to `record_reconcile_issue`, so consumers who pass comma-separated input receive a visible diagnostic regardless of the `RUNTIME_CREDENTIALS_REQUIRED` setting.
- FR-003 MUST update documentation in `docs/platform/consumer/runtime_credentials_eso.md` and its bootstrap template copy to declare newline-separated as the ONLY accepted format and state that comma-separated input is no longer valid.
- FR-004 MUST update the `record_reconcile_issue` error message in `reconcile_eso_runtime_secrets.sh` to reference the newline-separated format as the sole accepted format.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT truncate or split any value at internal commas; after the first `=` separator, the remainder of the pair string SHALL be treated as the value verbatim, preserving commas, base64 padding, and data-URI schemes intact.
- NFR-OBS-001 MUST emit both `log_warn` and `record_reconcile_issue` on parse failure; the messages MUST identify the expected format (`key=value` newline-separated) so consumers have actionable diagnostics.

## Normative Option Decision
- Option A: Newline-primary with comma fallback — when input contains `\n`, split on newlines; otherwise split on commas (backward-compatible).
- Option B: Newline-only strict — accept only newline-separated input; comma-separated input is rejected; consumers must migrate.
- Selected option: OPTION_B
- Rationale: Comma-separated format is ambiguous and unsafe for any value containing a comma. A clean break eliminates the ambiguity permanently. Consumers who applied the workaround already use newline format. Consumers who have not yet migrated will receive a visible diagnostic (FR-002) rather than a silent failure.

## Contract Changes (Normative)
- Config/Env contract: `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` — **breaking change**: format changes from `key=value,key2=value2` to newline-separated ONLY (`key=value\nkey2=value2`); comma-separated input is no longer accepted.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: `docs/platform/consumer/runtime_credentials_eso.md` and bootstrap template `scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md` MUST declare newline-separated as the sole accepted format.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/234
- Temporary workaround path: `scripts/bin/platform/infra/provision_deploy_local_marketplace.sh` (consumer) — changed serializer to newline-separated output; `scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh` (consumer) — updated `parse_literal_pairs()` to accept both formats.
- Replacement trigger: Blueprint ships newline-only `parse_literal_pairs()` in `reconcile_eso_runtime_secrets.sh`; consumer workaround patches become no-ops and can be removed.
- Workaround review date: 2026-07-28

## Normative Acceptance Criteria
- AC-001 MUST pass: a new test in `tests/infra/test_runtime_credentials_eso.py` exercises `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` with a newline-separated entry whose value contains a comma (e.g., `NUXT_OIDC_TOKEN_KEY=data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE=`); the reconcile MUST succeed and the rendered secret MUST contain the full value without truncation.
- AC-002 MUST pass: a new test asserts that comma-separated input (`username=dev-user,password=dev-password`) is rejected by `parse_literal_pairs()` with a non-zero exit and a `log_warn` message visible in stderr.
- AC-003 MUST pass: a positive-path test asserts that `parse_literal_pairs` called with a newline-separated string returns each `key=value` pair as a single output line with the value preserved verbatim after the `=`.

## Informative Notes (Non-Normative)
- Context: The comma-in-value failure is silent by default — `parse_literal_pairs()` returns 1, `record_reconcile_issue` records it, but with `RUNTIME_CREDENTIALS_REQUIRED=false` the reconcile exits 0 and the source secret is never created. FR-002 ensures the failure is visible regardless of `REQUIRED` mode.
- Tradeoffs: Option B (chosen) is a breaking change; consumers using comma-separated format with simple values must update their env var serializer. The diagnostic from FR-002 makes the migration path clear.
- Clarifications: none

## Explicit Exclusions
- Changing the env var name `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` — out of scope.
- Adding escaping support for comma-separated values — out of scope; newline-only is the correct fix.
- Modifying `apply_optional_module_secret_from_literals` or `render_optional_module_secret_manifests` — they already accept variadic `key=value` arguments and are unaffected.
