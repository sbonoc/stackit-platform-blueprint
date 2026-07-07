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
- Security sign-off: bonos
- Operations sign-off: bonos
- Missing input blocker token: none
- ADR path: none
- ADR status: none
- SPEC_READY_EXCEPTION: bug-fix
- authorized-by: bonos

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002
- Control exception rationale: Bug-fix bypass track; script-only changes with no API, contract, or schema impact.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: none
- Agent execution model: none
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none
- Has user-facing flow: false
- E2E gate classification: N/A

## Objective
- Business outcome: Four P1 infrastructure bugs fixed on the v1.12.x release branch so consumers on v1.12.0 can pick up v1.12.1 without upgrading to a future minor/major version.
- Success metric: All four bugs closed; fresh STACKIT SKE bootstrap succeeds end-to-end with no manual taint, no duplicate-key error, no DNS resolution failure, and no cert-manager field-manager conflict.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST correct the STACKIT object storage endpoint hostname from `object-storage.<region>.onstackit.cloud` to `object.storage.<region>.onstackit.cloud` in `scripts/lib/infra/object_storage.sh` (fixes #387).
- FR-002 MUST ensure `KEYCLOAK_ADMIN_PASSWORD` is emitted exactly once into the seed env file; the Python script `stackit_runtime_secret_env.py` MUST NOT read it from the environment — the shell caller `stackit_foundation_seed_runtime_secret.sh` is the sole owner (fixes #391).
- FR-003 MUST add `--server-side=true` and `--force-conflicts` to the cert-manager Helm upgrade invocation so that Gardener's `gardenlet` field-manager claim on `timeoutSeconds` does not abort the upgrade on STACKIT SKE; `--force-conflicts` is a no-op without `--server-side=true`; Helm 4 requires the explicit `=true` value (bare `--server-side` is invalid) (fixes #390).
- FR-004 MUST seed the ESO `ClusterSecretStore` source secret `runtime-credentials-source` in the `security` namespace inside `stackit_foundation_seed_runtime_secret.sh`, alongside the existing `platform-foundation-contract` secret (fixes #389).

### Non-Functional Requirements (Normative)
- NFR-SEC-001 MUST NOT broaden secret payload scope: the `runtime-credentials-source` secret MUST be populated from the same scoped env file as `platform-foundation-contract`; no additional credentials are introduced.
- NFR-OBS-001 Existing `start_script_metric_trap` and `log_metric` instrumentation in the seed script covers the new secret creation path; no additional metrics required.
- NFR-REL-001 All `kubectl apply` calls MUST use `--dry-run=client -o yaml | kubectl apply -f -` idempotent pattern; re-running the seed script MUST be safe.
- NFR-OPS-001 N/A — runbook impact: operators no longer need a manual `terraform taint` or `kubectl delete secret` workaround for these four scenarios.
- NFR-A11Y-001 N/A — no user-facing flow.

## Normative Option Decision
- Option A: Add `--force-conflicts` only to cert-manager call site in `core_runtime_bootstrap.sh` via a dedicated `run_helm_upgrade_install_force` helper in `tooling.sh`.
- Option B: Add a generic `--force-conflicts` flag parameter to `run_helm_upgrade_install` and pass it only for cert-manager.
- Selected option: OPTION_A
- Rationale: Option A adds zero complexity to the existing helper signature and avoids changing call sites for argocd and external-secrets. The force-conflicts behavior is Gardener-specific to cert-manager; scoping it to a separate function makes that explicit.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 [object storage endpoint] — `object_storage_endpoint()` returns `https://object.storage.eu01.onstackit.cloud` for `STACKIT_REGION=eu01`; no DNS NXDOMAIN on smoke run.
- AC-002 [no duplicate KEYCLOAK key] — running `stackit_foundation_seed_runtime_secret.sh` with `KEYCLOAK_ADMIN_PASSWORD` exported produces a valid env file with exactly one `KEYCLOAK_ADMIN_PASSWORD` line; `kubectl create secret --from-env-file` exits 0.
- AC-003 [cert-manager upgrade] — `core_runtime_bootstrap.sh` cert-manager Helm upgrade succeeds on STACKIT SKE without aborting on Gardener field-manager conflict.
- AC-004 [ESO source secret] — after running the seed script, `kubectl get secret -n security runtime-credentials-source` exists and `kubectl get clustersecretstore runtime-credentials-source-store -o jsonpath='{.status.conditions[0].status}'` returns `True`.

## Informative Notes (Non-Normative)
- Context: All four bugs are confirmed against v1.12.0 and are independent of the autonomous factory epic work tracked on main. The release branch `release/v1.12.x` is branched from the v1.12.0 tag.
- Tradeoffs: `run_helm_upgrade_install_force` duplicates ~20 lines from `run_helm_upgrade_install`. Acceptable for isolation; cert-manager's Gardener quirk is unlikely to spread to other charts.
- Clarifications: Issue #391 body describes the shell script having a "dev-defaults block" that emits KEYCLOAK_ADMIN_PASSWORD — at v1.12.0 that block does not exist yet; the Python script was the sole emitter. The fix pre-emptively moves ownership to the shell caller to match the issue's intent and prevent the duplicate if that block is ever added.

## Explicit Exclusions
- Tier-2 bugs (#395, #383–386, #394, #346, #366) are excluded from this patch release; they target v1.12.2.
- No Terraform, Helm chart values, or ArgoCD manifest changes are included.

## Potential Deferred Proposals
- none
