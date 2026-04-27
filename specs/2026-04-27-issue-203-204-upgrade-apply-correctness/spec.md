# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-203-204-upgrade-apply-correctness.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripts (scripts/lib/blueprint — no web framework)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none — no managed services involved
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: script-only change; no infrastructure provisioning, Kubernetes context, or identity baseline involved

## Objective
- Business outcome: Consumers running `make blueprint-upgrade-consumer` with `BLUEPRINT_UPGRADE_ALLOW_DELETE=true` no longer lose renamed workload manifests outside `base/apps/`; Terraform files produced by 3-way merge no longer fail `terraform validate` with duplicate block declarations.
- Success metric: AC-001–AC-006 pass; zero consumer-reported regressions for rename+prune and Terraform-dedup scenarios after next blueprint release.

## Normative Requirements

### Functional Requirements (Normative)

- REQ-001 MUST check whether a file scheduled for deletion is referenced in the `resources:` or `patches:` list of any `kustomization.yaml` present in the consumer working tree before executing the delete during upgrade apply.
- REQ-002 MUST classify a file that passes the kustomization-ref check as `consumer-kustomization-ref` ownership, `skip` action, `none` operation, and MUST NOT delete it.
- REQ-003 MUST preserve the existing delete behavior unchanged for files not referenced in any kustomization.yaml and not covered by the `_is_consumer_owned_workload` guard.
- REQ-004 MUST scan the merged content of any `.tf` file for duplicate top-level block declarations after a successful (no-conflict) 3-way merge.
- REQ-005 MUST auto-deduplicate byte-identical duplicate Terraform blocks and record the removed blocks in `ApplyResult.reason`.
- REQ-006 MUST emit a conflict artifact for non-identical duplicate Terraform blocks and classify the apply result as `conflict`.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 MUST parse `kustomization.yaml` files using `yaml.safe_load` only. Shell execution MUST NOT be used during the ref-check.
- NFR-OBS-001 Auto-deduplication of Terraform blocks MUST record block type, label, and file path in `ApplyResult.reason` and in the apply artifact JSON under `deduplication_log`.
- NFR-REL-001 If `kustomization.yaml` parsing raises any exception, the ref-check MUST default to `False` (file is not protected), log a warning to stderr, and MUST NOT raise an unhandled exception.
- NFR-OPS-001 The apply artifact JSON MUST include `consumer_kustomization_ref_count` and `tf_dedup_count` counters for operational visibility.

## Normative Option Decision
- Option A: Kustomization-ref check implemented inside `_classify_entries` at classification time (eager, per-candidate-path scan).
- Option B: Kustomization-ref check deferred to a post-classify pass over the full entry list (lazy, batch).
- Selected option: OPTION_A
- Rationale: Option A integrates at the same code location as the existing `_is_consumer_owned_workload` guard; keeps entry list consistent on first construction; no second pass required.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no new make targets or flags; `BLUEPRINT_UPGRADE_ALLOW_DELETE` semantics unchanged
- Docs contract: `docs/blueprint/architecture/decisions/ADR-issue-203-204-upgrade-apply-correctness.md` added

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/203 ; https://github.com/sbonoc/stackit-platform-blueprint/issues/204
- Temporary workaround path: dhe-marketplace restored deleted files from git history (#203); removed duplicate variable block manually (#204)
- Replacement trigger: this PR merged in blueprint
- Workaround review date: 2026-07-27

## Normative Acceptance Criteria

- AC-001 MUST: given a file absent in blueprint source and referenced in a consumer `kustomization.yaml` `patches:` list, when `allow_delete=True`, the file MUST NOT be deleted and the entry MUST carry `ownership=consumer-kustomization-ref`, `action=skip`.
- AC-002 MUST: given a file absent in blueprint source and listed in a consumer `kustomization.yaml` `resources:` list, when `allow_delete=True`, the file MUST NOT be deleted.
- AC-003 MUST: given a file absent in blueprint source and NOT referenced in any kustomization.yaml (and not covered by `_is_consumer_owned_workload`), when `allow_delete=True`, the existing delete classification MUST be produced unchanged.
- AC-004 MUST: given a `.tf` file whose clean 3-way merge produces two byte-identical `variable "<name>" {}` blocks, the written file MUST contain exactly one such block and `ApplyResult.result` MUST be `"merged-deduped"`.
- AC-005 MUST: given a `.tf` file whose clean 3-way merge produces two non-identical `variable "<name>" {}` blocks, the apply step MUST emit a conflict artifact and MUST NOT write the merged file.
- AC-006 MUST: `_is_kustomization_referenced` MUST return `False` and emit a stderr warning when a `kustomization.yaml` is malformed; no exception MUST propagate to the caller.

## Informative Notes (Non-Normative)
- Context: Both bugs were discovered during the dhe-marketplace v1.6.0→v1.7.0 upgrade. #203 caused `kustomize build` failures when renamed consumer manifests were pruned; #204 caused `terraform validate` failures from duplicate variable declarations. Issue #207 (PR #210) added a path-specific bridge guard (`_is_consumer_owned_workload`) for `base/apps/`; issue #206 (PR #211) moved the four blueprint seed manifests in `base/apps/` to `consumer_seeded` so they are classified by contract ownership before the prune branch is reached. This work item generalises the remaining gap: consumer-renamed files outside `base/apps/` (e.g. `infra/gitops/platform/environments/local/patch-*.yaml`) that are not in any contract ownership class and are referenced by a consumer kustomization.yaml. The principled long-term fix for #203 (consumer app descriptor `apps.yaml`) remains parked.
- Layering note: The three guards now form a stack. (1) Contract ownership (`consumer_seeded`, `source_only`, etc.) is evaluated first — files in these classes never reach the prune branch. (2) `_is_consumer_owned_workload` is a zero-cost O(1) fast path for any remaining `base/apps/` YAML not in the contract. (3) `_is_kustomization_referenced` (this work item) is the general fallback for any other overlay tree — it incurs filesystem reads and is only reached if the first two guards do not match.
- Tradeoffs: The kustomization-ref scan adds filesystem reads per kustomization.yaml per candidate delete; acceptable because upgrade apply runs infrequently and the ref-list is typically small (single overlay kustomization.yaml with <20 resources). Terraform deduplication uses regex-based top-level block scanning; does not require `terraform` on PATH.
- Clarifications: none

## Explicit Exclusions
- apps.yaml / consumer app descriptor proposal: out of scope
- Non-Terraform structured file deduplication (YAML, HCL modules): out of scope
- Incremental upgrade mode (#168) and dry-run mode (#167): out of scope
