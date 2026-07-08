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
- Missing input blocker token: none
- ADR path: docs/platform/architecture/decisions/ADR-issue-394-kubeconfig-ttl.md
- ADR status: proposed
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-010, SDD-C-011, SDD-C-015
- Control exception rationale: SDD-C-004 through SDD-C-009 (API/event/Pact contracts) not applicable — this is a shell-script bug fix with no API surface or event schema change. SDD-C-012 through SDD-C-014 (frontend/accessibility) not applicable — no user-facing flow.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: bats_or_shell_unit
- Agent execution model: none
- Managed service preference: stackit-managed-first
- Managed service exception rationale: N/A — fix targets a shell script, not a managed-service module
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false <!-- inferred from intake: no UI/flow signals found — confirm before SPEC_READY -->
- E2E gate classification: N/A

## Objective
- Business outcome: `infra-stackit-foundation-refresh-kubeconfig` always produces a valid, non-expired kubeconfig — operators and CI pipelines no longer encounter silent `Unauthorized` failures more than ~1 hour after the last refresh.
- Success metric: Zero `Unauthorized` / credential errors from `kubectl` immediately after `make infra-stackit-foundation-refresh-kubeconfig` completes, regardless of elapsed time since the previous run.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST force-taint `stackit_ske_kubeconfig.foundation[0]` before every `terraform apply` in `stackit_foundation_fetch_kubeconfig.sh` when `tooling_is_execution_enabled` is true, so that Terraform always re-generates the kubeconfig resource and its client certificate.
- FR-002 MUST NOT taint the resource when `DRY_RUN=true` (i.e. when `tooling_is_execution_enabled` returns false) — the taint step MUST be unconditionally skipped in dry-run mode.
- FR-003 MUST log a structured `[INFO]` message before executing the taint so operators can observe the action in script output.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT introduce new credential-handling paths or write kubeconfig content to stdout; the existing `terraform output -raw ske_kubeconfig > "$kubeconfig_output"` redirect MUST remain the sole write path.
- NFR-OBS-001 MUST emit a `log_info` or `log_metric` call recording that the forced taint occurred, keyed by profile and stack, so the action is visible in `start_script_metric_trap` telemetry.
- NFR-REL-001 If `terraform taint` exits non-zero (e.g. resource address not found), the script MUST abort with `log_fatal` rather than silently continuing to `terraform output` with a stale kubeconfig.
- NFR-OPS-001 The fix MUST require no operator action beyond running `make infra-stackit-foundation-refresh-kubeconfig`; no manual taint, no environment variable opt-in.

## Normative Option Decision
- Option A: Force-taint `stackit_ske_kubeconfig.foundation[0]` before every refresh (`tooling_is_execution_enabled` guard).
- Option B: Check certificate expiry after `terraform output`; taint + re-apply only if `notAfter` is within a threshold.
- Option C: Switch to ServiceAccount token-based authentication with a longer or configurable TTL.
- Selected option: OPTION_A
- Rationale: Option A is the minimal correct fix — the resource carries an ephemeral ~1 h TTL by design, so force-tainting it is the correct lifecycle pattern (identical precedent already exists in `stackit_foundation_apply.sh` for `stackit_postgresflex_instance`). Option B adds `openssl x509` / `date` parsing that can fail on non-standard cert formats and still requires a second apply round-trip. Option C is a valid long-term direction but is a separate scope and requires STACKIT SA-token provider support.

## Contract Changes (Normative)
- Config/Env contract: none — no new env vars; `DRY_RUN` semantics unchanged.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: `make infra-stackit-foundation-refresh-kubeconfig` behaviour changes: the underlying `stackit_foundation_fetch_kubeconfig.sh` script now runs `terraform taint stackit_ske_kubeconfig.foundation[0]` before `terraform apply` when `DRY_RUN=false`.
- Docs contract: `docs/platform/consumer/troubleshooting.md` — add note about forced taint under the kubeconfig TTL section; `docs/platform/architecture/decisions/ADR-issue-394-kubeconfig-ttl.md` — new ADR (status: proposed → approved at merge).

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: `terraform taint stackit_ske_kubeconfig.foundation[0] && make infra-stackit-foundation-refresh-kubeconfig`
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [forced taint executes before apply in execute mode] — verified by T-101, which MUST assert that `terraform taint stackit_ske_kubeconfig.foundation[0]` is invoked before `terraform apply` when `tooling_is_execution_enabled` is true (confirmed via log output or mock inspection).
- AC-002 [taint is skipped in dry-run mode] — verified by T-102, which MUST assert that when `DRY_RUN=true` the script completes without invoking `terraform taint` and exits 0.
- AC-003 [script aborts if taint fails] — verified by T-103, which MUST assert that a non-zero exit from `terraform taint` causes the script to exit non-zero before reaching `terraform output`.
- AC-004 [log message emitted on taint] — verified by T-104, which MUST assert that a `log_info` or equivalent structured message containing the resource address appears in stdout/stderr when the taint step runs.

## Informative Notes (Non-Normative)
- Context: `stackit_ske_kubeconfig` is a Terraform-managed resource that the STACKIT provider regenerates on create/replace. Because Terraform's `apply` is idempotent when no config changes, it skips the resource on every refresh unless it is marked tainted. The existing precedent for forced taint on a provider resource is `stackit_foundation_apply_clear_transient_postgres_taint` / `stackit_postgresflex_instance.foundation[0]` in `stackit_foundation_apply.sh`.
- Tradeoffs: Force-tainting on every refresh destroys and recreates the kubeconfig resource, which is a Terraform API call to STACKIT. This is safe and fast (the resource has no data) but adds one extra API round-trip per refresh. The TTL design of the resource makes this the intended usage pattern.
- Clarifications: none

## Explicit Exclusions
- Certificate expiry check before output (Option B): out of scope — adds parsing complexity without correctness benefit over the force-taint approach.
- ServiceAccount token migration (Option C): out of scope — valid long-term direction, tracked as a deferred proposal below.
- Configurable TTL threshold env var: out of scope — no operator-facing knob is needed once force-taint is in place.

## Potential Deferred Proposals
- ServiceAccount token authentication: replace short-lived client-certificate kubeconfig with a `ServiceAccount` token of configurable duration; eliminates the Terraform resource TTL coupling entirely. Surfaces when STACKIT SKE SA-token provision is stable.
- Kubeconfig expiry pre-flight check in smoke scripts: add an `openssl x509 -checkend` guard in `make infra-smoke` to fail-fast with a clear error before attempting `kubectl` calls, as an operator-UX complement to this fix.
