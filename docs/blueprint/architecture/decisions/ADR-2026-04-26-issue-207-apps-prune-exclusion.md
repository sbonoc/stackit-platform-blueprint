# ADR: Consumer Workload Manifest Prune Exclusion for base/apps/ (issue #207)

- **Date**: 2026-04-26
- **Status**: approved
- **Work item**: 2026-04-26-issue-207-apps-prune-exclusion
- **Reported by**: sbonoc/dhe-marketplace (v1.7.0 upgrade findings)

## Context

The blueprint upgrade planner (`upgrade_consumer.py`) treats `infra/gitops/platform/base/apps/` as
a fully blueprint-managed directory root. This directory is listed in
`required_paths_when_enabled` for the app-runtime optional module, which causes it to become a
`conditional_entry` and a `managed_root` in the upgrade planner.

When a consumer renames their workload manifests (e.g. `backend-api-deployment.yaml` →
`my-api-deployment.yaml`) or adds new manifests, those consumer files are absent from the
blueprint source tree. With `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`, the planner enqueues
`OPERATION_DELETE` for every such file, destroying consumer-owned deployment definitions.

This is a domain boundary violation: blueprint owns the directory structure and
`kustomization.yaml` (which the smoke assertion reads) but does not own individual workload
manifest files.

## Decision

Add a pure predicate `_is_consumer_owned_workload(relative_path: str) -> bool` that returns
`True` for any `.yaml` file under `infra/gitops/platform/base/apps/` except `kustomization.yaml`.

Add an early-exit guard in `_classify_entries()` before the `allow_delete` delete branch. When
the predicate returns `True`, emit `action=skip, operation=none, ownership=consumer-owned-workload`
regardless of the `allow_delete` flag.

`kustomization.yaml` in that directory is explicitly excluded from the predicate because it is
blueprint-managed — the smoke assertion reads it to derive the list of expected manifest paths
(established by issue #208).

## Alternatives Considered

**Option B — Add consumer manifests to `consumer_seeded_paths` in contract.yaml**: Requires
blueprint authors to explicitly list every consumer manifest path. This leaks consumer-specific
knowledge into the blueprint source contract and cannot scale to consumer repos that differ in
manifest naming.

**Option C — Add `base/apps/` to `protected_roots`**: `protected_roots` prevents blueprint from
updating files it owns; it does not protect consumer-created files from deletion. Using it here
would prevent blueprint from managing `kustomization.yaml`, which would break the smoke assertion.

## Consequences

- **Positive**: Consumer repos can rename, add, or remove workload manifests without risk of
  deletion during blueprint upgrade runs, even with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true`.
- **Positive**: Zero-config — no consumer contract.yaml changes required.
- **Positive**: Additive — does not alter classification for any existing path.
- **Risk**: If blueprint adds a real managed manifest under `base/apps/` (non-kustomization) in
  a future release, it will be silently skipped by consumer upgrades. Mitigation: issue #206
  delivers a general contract schema mechanism (`consumer_owned_paths` or equivalent) that
  provides precise per-path ownership declaration and supersedes this bridge guard.

## Bridge Status

This decision is a targeted bridge guard until issue #206 (contract schema for consumer-owned
path declarations) is implemented. The inline comment in code references issue #203 for the
general unification approach.
