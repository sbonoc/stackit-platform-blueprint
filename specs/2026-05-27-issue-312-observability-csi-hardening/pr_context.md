# PR Context

## Summary
- Work item: issue-312-observability-csi-hardening
- Objective: Eliminate etcd as a credential store for the observability module on STACKIT lanes by replacing the `blueprint-observability-auth` K8s Secret with Secrets Store CSI Driver delivery from STACKIT Secrets Manager.
- Scope boundaries: STACKIT-lane OTC credential delivery only. Local lane unchanged. Mount path and OTC `${file:...}` references unchanged.

## Requirement Coverage
- Requirement IDs covered: FR-001 through FR-010, NFR-SEC-001 through NFR-SEC-003, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001 through AC-005
- Acceptance criteria covered: AC-001 (no K8s Secret post-deploy), AC-002 (pod starts, tmpfs populated), AC-003 (smoke passes), AC-004 (pytest passes), AC-005 (local lane unchanged)
- Contract surfaces changed: `blueprint/modules/observability/module.contract.yaml` (new CSI prerequisite); `make infra-observability-apply` no longer creates `blueprint-observability-auth` on STACKIT profiles; `make infra-observability-destroy` no longer deletes it.

## Key Reviewer Files
- Primary files to review first:
  - `infra/cloud/stackit/helm/observability/otel-collector.values.yaml` — CSI volume replaces K8s Secret volume
  - `infra/gitops/argocd/optional/{dev,stage,prod}/observability.yaml` — CSI volume + SecretProviderClass inline document (vaultAddress placeholder + auth params)
  - `infra/gitops/argocd/core/{dev,stage,prod}/secrets-store-csi-driver*.yaml` — new CSI driver ArgoCD Applications
  - `infra/cloud/stackit/terraform/foundation/observability_vault.tf` — Vault kv_secret_v2 credential write in foundation workspace (moved from modules/observability/ per Codex review)
  - `infra/cloud/stackit/terraform/foundation/versions.tf` — vault provider added
  - `scripts/bin/infra/observability_apply.sh` — reconcile call removed from STACKIT path
- High-risk files: `scripts/lib/infra/observability.sh` (deprecation guard uses `is_stackit_profile` + `log_fatal`; must not break local path); `tests/infra/modules/observability/test_contract.py` (5 assertions removed/rewritten; 8 new assertions added in post-review commits).

## Validation Evidence
- Required commands executed: `python3 -m pytest tests/infra/modules/observability/ -x -q`; `make quality-hooks-fast`; `make quality-sdd-check`; `make quality-hardening-review`
- Result summary: 111/111 unit assertions PASS (111 after post-review commits fd150b7 + 6263fea adding 3 CSI volume driver assertions and updating 5 existing assertions); quality-hooks-fast PASS — all 11 checks pass after all review fixes; quality-hardening-review PASS; quality-sdd-check PASS. STACKIT smoke (`make infra-observability-smoke`) is manual — requires a live STACKIT cluster with CSI driver running; documented as AC-003 manual acceptance criterion.
- Post-review commits: fd150b7 (5 review findings: BLUEPRINT_STACK guard, delete_all_versions, syncSecret, required_version, positive CSI assertions); 6263fea (5 review findings: vaultAddress placeholders, Vault auth params, vault_kv_secret_v2 moved to foundation TF, bootstrap templates, prerequisites doc)
- Artifact references: `traceability.md`, `hardening_review.md`

## Risk and Rollback
- Main risks: CSI driver unavailable at OTC deploy time → pod stuck in ContainerCreating (fail-safe, documented); Vault TF provider authentication against Secrets Manager requires SM user token from foundation outputs.
- Rollback strategy: revert `extraVolumes` block in STACKIT OTC values to `secret` type; re-run `make infra-observability-apply` to recreate `blueprint-observability-auth`.

## Deferred Proposals
- Proposal A (automated rotation trigger): Parked — trigger: on-scope: observability — event-driven rotation when SM expiry fires; CSI poll interval covers the common case; no current consumer request. Backlog: `AGENTS.backlog.md` § on-scope: observability.
- Proposal B (local lane CSI): Parked — trigger: triage: next-session (stale-after: 2) — conditional on Docker Desktop native Secrets Store CSI Driver support; no actionable scope until that capability ships. Backlog: `AGENTS.backlog.md` § on-scope: observability.
- Proposal C (KMS envelope encryption): Parked — trigger: on-scope: observability — KMS module is a separate optional module; revisit when KMS hardening is in scope. Backlog: `AGENTS.backlog.md` § on-scope: observability.
