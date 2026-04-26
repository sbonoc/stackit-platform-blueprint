# ADR: Issues #198 + #199 — Upgrade Coverage Gaps: VALIDATION_TARGETS and feature_gated Ownership Class

- **Status**: approved
- **Date**: 2026-04-26
- **Issues**: #198, #199, #199 (comment), #203 (detection mitigation only), #204 (excluded)
- **Work item**: `specs/2026-04-26-issue-198-199-upgrade-coverage-gaps/`

## Context

Three independent gaps in the blueprint upgrade pipeline allow regressions to go
undetected.

**Issue #199 — `blueprint-template-smoke` missing from `VALIDATION_TARGETS`**:
`VALIDATION_TARGETS` in `upgrade_consumer_validate.py` is the authoritative set
of Make targets run in a generated-consumer repo after blueprint upgrade. The
`blueprint-template-smoke` target (added in a prior issue to validate the
init-path) was never added to this tuple, so init-path regressions are never
caught by the post-upgrade validation gate. During the v1.6.0→v1.7.0 consumer
upgrade, `apps/catalog` was incorrectly placed in `consumer_seeded`, causing
`seed_consumer_owned_files` to crash with `FileNotFoundError` at CI — undetected
locally because `blueprint-template-smoke` was not in `VALIDATION_TARGETS`.

**Issue #199 (comment) — `infra-argocd-topology-validate` missing from `VALIDATION_TARGETS`**:
`infra-validate` calls `validate.sh`, which does not run `kustomize build`.
`infra-argocd-topology-validate` is a separate blueprint-managed target that
runs `kustomize build --load-restrictor=LoadRestrictionsNone` on both the ArgoCD
base and the active overlay — but it is not in `VALIDATION_TARGETS`. During the
v1.6.0→v1.7.0 upgrade, Stage 2's prune step deleted consumer-owned manifests
still referenced by `kustomization.yaml` (see #203). The upgrade validation
passed, but `kustomize build` would have caught the missing files immediately.
The breakage only surfaced at the CI `blueprint-quality` job.

**Issue #198 — `apps/catalog*` paths not declared in `ownership_path_classes`**:
`audit_source_tree_coverage` cross-checks every git-tracked blueprint source
file against the union of `required_files`, `init_managed`,
`conditional_scaffold`, `blueprint_managed_roots`, and `source_only`. The three
`apps/catalog` paths (`apps/catalog`, `apps/catalog/manifest.yaml`,
`apps/catalog/versions.lock`) are governed by `app_catalog_scaffold_contract`
(a separate top-level key in `contract.yaml`) but are absent from
`ownership_path_classes`. This causes false-positive "uncovered file" warnings
on every coverage audit — and blocks plan generation when the strict gate is
enforced.

The `apps/catalog` paths are distinct from `conditional_scaffold` entries:
conditional-scaffold paths correspond one-to-one with `optional_modules` entries
and are validated by the equality invariant at `validate_contract.py:1771-1781`;
`apps/catalog` paths are opt-in via a standalone feature flag with no seed
template, so they cannot satisfy that equality invariant without loosening the
schema.

**Issues #203 and #204 (excluded)**:
Issue #203 (Stage 2 prune deletes consumer-renamed seeded files) and #204 (3-way
merge emits duplicate Terraform variable blocks) are real bugs, but their root
causes require architectural changes to Stage 2 apply logic and the merge
algorithm respectively. Both are excluded from this work item (see Alternatives
Considered). The detection gap from #203's symptoms is mitigated by adding
`infra-argocd-topology-validate` to `VALIDATION_TARGETS`.

## Decision

**For #199 and #199 (comment)**: Add `"blueprint-template-smoke"` and
`"infra-argocd-topology-validate"` to `VALIDATION_TARGETS` in
`upgrade_consumer_validate.py`. Two-line change. `infra-argocd-topology-validate`
degrades gracefully when kustomize is absent (falls back to kustomization-file
check), so it has no hard kustomize dependency.

**For #198**: Add a `feature_gated` ownership class as a new peer of
`conditional_scaffold` in `RepositoryOwnershipPathClasses`. Paths in this class:

- Are covered by `audit_source_tree_coverage` (passed as an additional coverage
  set).
- Require no disk-presence check (they are only expected on-disk when the
  corresponding feature flag is enabled in the consumer).
- Are not subject to the equality invariant against `optional_modules`.
- Default to an empty list when the YAML key is absent, preserving backward
  compatibility for all existing YAML files.

`blueprint/contract.yaml` declares `apps/catalog`,
`apps/catalog/manifest.yaml`, and `apps/catalog/versions.lock` under
`feature_gated`. The bootstrap template counterpart is mirrored.

## Alternatives Considered

**Option A — extend `OptionalModuleContract.paths` via `_optional_str_map`** (#198):
Add the three `apps/catalog` path keys to `_optional_str_map` and wire them
through `OptionalModuleContract`. Rejected: `_optional_str_map` picks up keys by
hardcoded name; adding new names requires changes in `contract_schema.py`,
`validate_contract.py`, and `contract.yaml` (module structure), and forces the
equality invariant to loosen or be special-cased. The blast radius is materially
larger than stated in the original issue description, and it conflates two
distinct ownership semantics (conditional-scaffold vs feature-gated).

**#203 root cause fix — kustomization reference check before prune**:
Rejected for this work item. The suggested fix (parse `kustomization.yaml`
resources/patches before pruning) handles only the kustomization case, not the
general rename problem. A renamed `consumer_seeded` file is semantically a new
consumer-owned path; the principled fix requires distinguishing blueprint-named
from consumer-renamed files in the upgrade planner — a separate, more invasive
change to Stage 2 apply logic. The detection gap is mitigated by FR-005.

**#204 root cause fix — Terraform-aware deduplication in 3-way merge**:
Rejected for this work item. The fix requires either a semantic Terraform parser
(new dependency, significant complexity) or adding `terraform validate` to
`VALIDATION_TARGETS` (provider-dependent, slow — terraform validate requires
provider plugins to be installed). Architecturally unrelated to the VALIDATION_TARGETS
gaps and feature_gated ownership class addressed here. Separate work item.

## Consequences

- `scripts/lib/blueprint/upgrade_consumer_validate.py`: `"blueprint-template-smoke"` and `"infra-argocd-topology-validate"` added to `VALIDATION_TARGETS`.
- `scripts/lib/blueprint/contract_schema.py`: `feature_gated: list[str]` field on `RepositoryOwnershipPathClasses`; `feature_gated_paths` property on `RepositoryContract`; parser wired in schema loader.
- `scripts/lib/blueprint/upgrade_consumer.py`: `feature_gated` parameter on `audit_source_tree_coverage` (default `frozenset()`); call site passes `set(contract.repository.feature_gated_paths)`; error message in `validate_plan_uncovered_source_files` updated to reference `feature_gated`.
- `scripts/bin/blueprint/validate_contract.py`: reads `feature_gated` from the loaded contract; no disk-presence check, no equality constraint.
- `blueprint/contract.yaml` + bootstrap template: `feature_gated` list added under `ownership_path_classes`.
- Tests: unit tests confirming both targets in `VALIDATION_TARGETS`; unit test confirming `feature_gated` paths are covered by `audit_source_tree_coverage`; test confirming `validate_contract.py` accepts the new field without error.
- No CLI flag changes. No JSON schema changes. No consumer-repo migration required.
- Issues #203 (root cause) and #204 remain open; separate work items required.
