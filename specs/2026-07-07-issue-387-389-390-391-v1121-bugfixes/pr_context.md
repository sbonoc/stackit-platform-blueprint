# PR Context

## Summary
- Work item: 2026-07-07-issue-387-389-390-391-v1121-bugfixes
- Objective: Ship four P1 infrastructure bug fixes as v1.12.1 so consumers on v1.12.0 can take a patch upgrade without touching the main branch / future minor version.
- Scope boundaries: Script-only changes in `scripts/lib/infra/` and `scripts/bin/infra/`. No Terraform, Helm chart values, ArgoCD manifests, or consumer-facing contract surfaces changed.

## Requirement Coverage
- Requirement IDs covered: FR-001, FR-002, FR-003, FR-004, NFR-SEC-001, NFR-REL-001
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Contract surfaces changed: none

## Key Reviewer Files
- Primary files to review first:
  - `scripts/lib/infra/object_storage.sh` — hostname typo fix (1 line)
  - `scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh` — KEYCLOAK ownership + ESO source secret seeding
  - `scripts/lib/infra/stackit_runtime_secret_env.py` — remove env-var read for KEYCLOAK_ADMIN_PASSWORD
  - `scripts/lib/infra/tooling.sh` — new `run_helm_upgrade_install_force` function
  - `scripts/bin/infra/core_runtime_bootstrap.sh` — swap cert-manager call to force-conflicts variant
- High-risk files:
  - `stackit_foundation_seed_runtime_secret.sh` — adds a new `kubectl apply` block; re-run idempotency depends on `--dry-run=client -o yaml | kubectl apply -f -` pattern already used by the existing block (same pattern applied).

## Validation Evidence
- Required commands executed: `bash -n` syntax check on all 3 modified shell scripts (OK); `make quality-sdd-check` bypass-track pass; pre-commit hooks passed on all 5 commits.
- Result summary: All static checks pass. No live cluster available for AC-001–AC-004 integration smoke; each fix is a 1–10 line targeted change following existing patterns.
- Artifact references: Fix commits on `release/v1.12.x` — `4298bc8b` (#387), `edb7a711` (#391), `8fbb2b17` (#390), `181d7d3d` (#389).

## Risk and Rollback
- Main risks: (1) `runtime-credentials-source` kubectl apply overwrites pre-existing secret if operator has custom keys — idempotent pattern mitigates for matching keys; (2) `--force-conflicts` overrides Gardener field-manager claim on `timeoutSeconds` — Gardener may reset on next reconcile but cert-manager remains functional.
- Rollback strategy: Pin consumers to `v1.12.0` in their blueprint version pin. The `release/v1.12.x` branch can be reverted per-commit if a regression is found post-release.

## Deferred Proposals
- Tier-2 bugs (#395, #383–386, #394, #346, #366): deferred to v1.12.2 batch. Same release branch; no main branch involvement needed.
- Integration smoke tests for seed script (AC-001–AC-004): deferred to a follow-up chore ticket; requires a live STACKIT SKE cluster and cannot run in CI without infrastructure credentials.
