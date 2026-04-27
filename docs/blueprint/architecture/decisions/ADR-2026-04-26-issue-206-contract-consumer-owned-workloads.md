# ADR: Remove Hardcoded Workload Manifest Names from Blueprint Contract (issue #206)

- **Date**: 2026-04-26
- **Status**: approved
- **Work item**: 2026-04-26-issue-206-contract-consumer-owned-workloads
- **Reported by**: sbonoc/dhe-marketplace (v1.7.0 upgrade findings)

## Context

`blueprint/contract.yaml` lists four blueprint-seed workload manifest names in two locations:

1. The global `required_files` list (lines ~379–382):
   - `infra/gitops/platform/base/apps/backend-api-deployment.yaml`
   - `infra/gitops/platform/base/apps/backend-api-service.yaml`
   - `infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml`
   - `infra/gitops/platform/base/apps/touchpoints-web-service.yaml`

2. `optional_modules.app_runtime_gitops_contract.required_paths_when_enabled`
   (same four paths, repeated).

`blueprint/contract.yaml` is itself a `required_file` and is overwritten in its entirety during
every `blueprint-upgrade` run. Any consumer modification to their `blueprint/contract.yaml`
(e.g., removing these four paths because they renamed their workload manifests) is lost after
the next upgrade. Consumers must manually re-patch the file after every upgrade — a recurring
tax that embeds blueprint implementation details into the consumer upgrade workflow.

Issues #207 and #208 addressed the downstream symptoms (prune deletion and smoke CI failures).
This ADR addresses the root cause: the contract should not enumerate consumer workload filenames.

## Decision

Move the four seed manifest paths from `required_files` to `source_only_paths` in
`blueprint/contract.yaml`. Remove them from `app_runtime_gitops_contract.required_paths_when_enabled`.

**`source_only_paths`** is the correct classification:
- The upgrade planner classifies `source_only` paths as `skip` — they are not synced from
  blueprint source to consumer repos on upgrade.
- The template-source CI coverage check (`audit_source_tree_coverage`) includes `source_only`
  paths in its coverage roots — so template-source CI continues to pass.
- The four seed files remain in the template source repo for use by `blueprint-init-repo`
  (which copies them on initial consumer initialization).

**`required_paths_when_enabled`** in `app_runtime_gitops_contract` retains only:
- `infra/gitops/platform/base/apps` (directory presence)
- `infra/gitops/platform/base/apps/kustomization.yaml` (required by the smoke assertion per #208)

## Alternatives Considered

**Option B — Consumer workload manifest paths field**: Add a new schema field
`consumer_workload_manifest_paths: list[str]` to `app_runtime_gitops_contract` that consumers
declare their actual manifest names; the upgrade planner carries this field forward across
upgrades. This is a richer mechanism but requires: a Pydantic schema change, an upgrade planner
carry-forward mechanism for consumer-declared overrides, and a migration path for existing consumers.
Deferred as a future enhancement after this fix ships.

**Option C — 3-way merge for blueprint/contract.yaml**: Treat `blueprint/contract.yaml` as a
merge-required file rather than a required overwrite. This would allow any consumer customization
to persist across upgrades. However, it would complicate the upgrade contract significantly and
introduce merge conflicts for all consumers on every upgrade. Not selected.

## Consequences

- **Positive**: Consumers who rename their workload manifests no longer need to re-patch
  `blueprint/contract.yaml` after each upgrade.
- **Positive**: Zero code changes — uses the existing `source_only_paths` mechanism.
- **Positive**: Template-source CI coverage checks continue to pass.
- **Risk**: The upgrade planner can no longer push content updates to the four seed manifest
  files (they are `source_only` → skip forever). This is intentional: blueprint seeds them
  at init time, consumers own them thereafter. If blueprint changes the seed content in a
  future release, consumers will not receive those changes automatically.
- **Follow-up 1**: Option B (consumer_workload_manifest_paths field) remains a valid future
  enhancement for teams that want explicit preflight validation of their actual manifest names.
- **Follow-up 2**: Source-only seed change advisory — when blueprint improves the content of
  a `source_only` seed file in a future release, the upgrade planner must emit an advisory plan
  entry with a unified diff so consumers are notified and can apply the delta manually. Without
  this, `source-only / skip` is silent even when the seed content changed. Tracked in backlog
  as `proposal(issue-206): source-only seed change advisory`.
