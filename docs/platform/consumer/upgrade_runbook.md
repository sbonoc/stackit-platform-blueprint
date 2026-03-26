# Upgrade Runbook

Use this runbook when updating a generated repository from one template version to another.

## Before Upgrade
Run baseline checks on current state:

```bash
make quality-hooks-run
make infra-validate
make infra-smoke
```

## Apply Template Upgrade
1. Pull/merge the new template changes into your repository.
2. Run migration:

```bash
make blueprint-migrate
```

`blueprint-migrate` resolves source/target compatibility and applies only explicitly registered migration transitions.

## After Upgrade
Run full post-upgrade checks:

```bash
make quality-hooks-run
make infra-validate
make infra-audit-version
make infra-smoke
```

## Compatibility Contract
- Template compatibility lives in `blueprint/contract.yaml`:
  - `template_bootstrap.template_version`
  - `template_bootstrap.minimum_supported_upgrade_from`
  - `template_bootstrap.upgrade_command`

If your source version is older than `minimum_supported_upgrade_from`, perform staged upgrades.

## Supported Migration Transitions
- Migration transitions are explicitly registered in `scripts/lib/blueprint/migrate_repo.py`.
- Current template baseline is pre-release `1.0.0`; no published transitions exist yet.
- For `template_version: 1.0.0`, `make blueprint-migrate` is expected to return a no-op success message.
- Unsupported transitions fail fast with a clear error and list available transitions.
