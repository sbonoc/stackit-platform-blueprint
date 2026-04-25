# Manual Merge Checklist

Use this checklist when `required_manual_actions` is non-empty after preflight/apply.

## 1) Confirm Blocking Items

- Inspect `artifacts/blueprint/upgrade_preflight.json`.
- Extract `required_manual_actions` and affected paths.
- Treat runtime dependency edge breaks (missing referenced artifacts/scripts) as blocking.

## 2) Preserve Ownership Boundaries

- Keep consumer-owned files consumer-owned.
- Merge blueprint-managed updates without deleting consumer custom logic.
- Never use destructive commands to silence merge conflicts.

## 3) Resolve One Path at a Time

- For each path, compare:
  - current consumer file
  - blueprint target change
  - surrounding contract/doc references
- Prefer additive merges and explicit comments only when non-obvious behavior is introduced.

## 3a) Module Scaffold After Merges

Optional module scaffold (infra/cloud/stackit/terraform/modules/{module}/, infra/local/helm/{module}/, tests/infra/modules/{module}/, infra/gitops/argocd/optional/${ENV}/{module}.yaml) is managed by `make infra-bootstrap`, not by manual merge. After resolving conflicts:

- **If any enabled module scaffold file was deleted** during conflict resolution (to force a reseed), re-run `make infra-bootstrap` — it will recreate from the updated template.
- **If `make infra-validate` reports template drift** for an enabled module: delete the drifted file(s) and re-run `make infra-bootstrap` to reseed from the current template. Do not manually patch scaffold to match the template.
- **If a module was disabled**: run `make infra-destroy-disabled-modules` to remove its scaffold. Do not run this speculatively.

## 4) Re-run Required Commands

After merges, run in order:

```bash
make blueprint-upgrade-consumer
BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer

# Reseed enabled module scaffold from updated templates (always safe — create-if-missing)
make infra-bootstrap

make blueprint-upgrade-consumer-validate
make blueprint-upgrade-consumer-postcheck
make infra-validate
make quality-hooks-run
```

## 5) Close the Loop in Report

Always report:

- manual paths merged
- rationale per path
- remaining manual actions (if any)
- final validation outcomes
