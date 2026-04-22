# Implementation Plan — ArgoCD AppProject Namespace Policy Gap (#108 / #109)

## Implementation Start Gate

SPEC_READY=true. All inputs resolved. Implementation may proceed.

## Slice 1 — Guard test (red)

Add a failing test class `AppProjectNamespacePolicyTests` to
`tests/infra/test_tooling_contracts.py` that asserts `external-secrets` is present in the
`spec.destinations` list of every AppProject overlay file (local, dev, stage, prod) and the
bootstrap template copy. The test reads each YAML file with PyYAML and checks the destinations
list. Test must fail before the manifest fix.

Files touched: `tests/infra/test_tooling_contracts.py`

## Slice 2 — Manifest fix (green)

Add an `external-secrets` destination entry to `spec.destinations` in all five AppProject files:

1. `infra/gitops/argocd/overlays/local/appproject.yaml`
2. `infra/gitops/argocd/overlays/dev/appproject.yaml`
3. `infra/gitops/argocd/overlays/stage/appproject.yaml`
4. `infra/gitops/argocd/overlays/prod/appproject.yaml`
5. `scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml`

Each entry follows the existing pattern:
```yaml
- namespace: external-secrets
  server: https://kubernetes.default.svc
```

No changes to `namespaceResourceWhitelist` or `clusterResourceWhitelist`.

Files touched: the five AppProject YAML files listed above.

## Slice 3 — ADR and governance

Write ADR at
`docs/blueprint/architecture/decisions/ADR-20260422-issue-108-109-argocd-appproject-namespace-policy.md`.

Update `AGENTS.decisions.md` with the rationale. Update `AGENTS.backlog.md` to mark #108 and
#109 done.

## Validation

- `make infra-contract-test-fast` — must include new guard tests, all green
- `make infra-validate` — must pass
- `make quality-hooks-fast` — must pass

## App Onboarding Contract (Normative)
- Required minimum make targets (all unaffected by this work item):
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: no app delivery scope affected; all targets above remain functional

## Documentation Plan (Document Phase)
- Blueprint docs updates: ADR at `docs/blueprint/architecture/decisions/ADR-20260422-issue-108-109-argocd-appproject-namespace-policy.md`; `AGENTS.decisions.md`
- Consumer docs updates: none (static manifest fix; no consumer-facing behavior change)
- Mermaid diagrams updated: none
- Docs validation commands:
  - `make quality-hooks-fast`
  - `make infra-validate`

## Publish Preparation
- PR context: `specs/2026-04-22-issue-108-109-argocd-appproject-namespace-policy/pr_context.md`
- Hardening review: `specs/2026-04-22-issue-108-109-argocd-appproject-namespace-policy/hardening_review.md`

## Risk / Rollback

**Risk**: Widening AppProject destinations to `external-secrets` allows Argo to manage resources
in that namespace. The `namespaceResourceWhitelist` already covers all intended resource kinds;
no new kinds are added, so the attack surface is unchanged.

**Rollback**: Remove the `external-secrets` destination entries from the five YAML files. No
cluster state migration required.
