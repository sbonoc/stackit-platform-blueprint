# Hardening Review

## Repository-Wide Findings Fixed
- Finding: no repository-wide hardening regressions introduced. To be confirmed at implementation time by running `make quality-hooks-fast` and the full pytest suite.

## Security Review

### CSI driver credential delivery (NFR-SEC-001, NFR-SEC-003)
- Credentials are delivered via the Secrets Store CSI Driver as a tmpfs mount — never written to etcd. `blueprint-observability-auth` K8s Secret does not exist on STACKIT lanes post-deploy.
- `SecretProviderClass` is namespace-scoped to `observability` — no cross-namespace secret access.
- Vault provider authenticates to STACKIT Secrets Manager using a token provisioned by the foundation TF layer (SM user credentials). Token is passed as a TF variable, never written to state files in cleartext.

### Credential non-persistence (NFR-SEC-002)
- `OBSERVABILITY_USERNAME` password and push URLs are not written to any state file. This constraint is inherited from PR #308 and is preserved after removing the reconcile function call from the STACKIT path.

### Local lane unchanged
- Local lane retains K8s Secret lifecycle. Threat model for Docker Desktop single-developer machine does not warrant CSI driver complexity.

## Observability and Diagnostics Changes
- STACKIT Secrets Manager access logs provide a full audit trail for every credential read at OTC pod start and CSI poll interval.
- No additional in-repo instrumentation is required (NFR-OBS-001).
- OTC pod `ContainerCreating` stuck state (CSI mount failure) is surfaced by existing cluster health monitoring.

## Architecture and Code Quality Compliance
- CSI driver installation is cluster-scoped (ArgoCD core layer), consistent with the pattern used for ArgoCD, ESO, and cert-manager.
- `observability_reconcile_runtime_secret()` and `observability_delete_runtime_secret()` remain in `observability.sh` for the local-lane path — no breaking change for local consumers.
- Deprecation guard in `observability.sh` emits `log_warn` when called on a STACKIT profile — operators are informed without a hard failure.
- Test updates follow the red → green TDD order defined in plan.md — existing assertions are rewritten before the implementation changes are made.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)
- N/A — no UI surfaces introduced or modified.

## Proposals Only (Not Implemented)
- Proposal A: Automated credential rotation trigger — rotate on Secrets Manager expiry event; deferred; trigger: on-scope: observability security hardening.
- Proposal B: Local lane CSI driver — local lane retains K8s Secret; deferred; trigger: Docker Desktop native CSI driver support.
- Proposal C: KMS envelope encryption of credentials stored in Secrets Manager — out of scope; KMS module concern.
