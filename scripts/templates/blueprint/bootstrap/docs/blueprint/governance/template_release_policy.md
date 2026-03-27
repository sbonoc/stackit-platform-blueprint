# Template Release Policy

This document defines how blueprint template releases are cut and supported.

## Versioning
- Template releases use semantic version tags: `vMAJOR.MINOR.PATCH`.
- Compatibility metadata is declared in `blueprint/contract.yaml` under `repository.template_bootstrap`.

## Release Workflow
1. Ensure backlog P0/P1 scope for the milestone is complete.
2. Run required validation bundles:
   - `make quality-hooks-run`
   - `make infra-validate`
   - `make infra-smoke`
   - CI matrix and consumer conformance lanes must pass:
     - `contract-matrix` (`local-full`/`stackit-dev` x observability `false`/`true`)
     - `consumer-golden-conformance` (generated-repo scenario matrix across `local-lite`, `local-full`, and `stackit-dev` with representative optional-module combinations)
3. Generate release notes:
   - `make blueprint-release-notes`
4. Create and push release tag (`v*`).
5. GitHub Actions release workflow publishes notes and artifact.

## Support Policy
- `MAJOR.MINOR` line receives fixes until the next `MINOR` is released.
- Critical fixes may be backported to the previous minor line.
- Upgrade path support starts at `minimum_supported_upgrade_from`.

## Consumer Expectations
- Consumers should run `make blueprint-migrate` before post-upgrade validation bundles.
- Consumers should follow `docs/platform/consumer/upgrade_runbook.md` on every template upgrade.

## Migration Governance
- Every new template version requiring upgrade changes must add an explicit migration transition in
  `scripts/lib/blueprint/migrate_repo.py`.
- Unsupported source versions must fail with a clear message instead of best-effort mutation.
