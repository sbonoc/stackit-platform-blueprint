# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: true
- SPEC_PRODUCT_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-20260430-issue-241-make-override-warnings.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale:
  - SDD-C-001: no missing inputs — all requirements are deterministically derivable from the GitHub issue and existing Makefile structure
  - SDD-C-009: tooling-only change (Makefile variable declarations); no authn/authz, secret handling, or privilege boundary is involved
  - SDD-C-010: no log, metric, or trace paths are created or modified; the change affects only Make variable definitions
  - SDD-C-013: no runtime capability or managed service is involved
  - SDD-C-014: no runtime baseline or Kubernetes context is involved
  - SDD-C-015: no app delivery workflow or port-forward wrapper is affected
  - SDD-C-018: this work item IS the blueprint upstream fix; the defect is resolved here rather than worked around in a consumer
  - SDD-C-022: not HTTP route, query/filter, or API endpoint scope
  - SDD-C-023: no filter or payload-transform logic
  - SDD-C-024: the bug manifests as a GNU Make warning (not a failing test); no reproducible smoke/curl/deterministic-check finding exists; the fix is validated by new contract assertions

## Implementation Stack Profile (Normative)
- Backend stack profile: not applicable — tooling-only change (Makefile template + Python contract test)
- Frontend stack profile: not applicable
- Test automation profile: pytest (contract tests in tests/blueprint/test_quality_contracts.py)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: tooling-only change; no runtime service is provisioned or modified by this work item
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none — stack profile fields reflect the blueprint repository baseline; the work item itself touches no runtime path

## Objective
- Business outcome: Consumer repos can customise the `spec-scaffold` default track and the `blueprint-uplift-status` script path by setting override-point variables in `make/platform.mk`, without redefining blueprint-managed Make targets and without producing GNU Make override warnings.
- Success metric: `make help 2>&1 | grep "warning:"` produces no output on a consumer repo that previously required target re-definition for these two customisation points.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `blueprint.generated.mk` MUST declare `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` before the `spec-scaffold` target definition, and the `spec-scaffold` recipe MUST use `$(SPEC_SCAFFOLD_DEFAULT_TRACK)` in place of the hardcoded `blueprint` string as the `--track` default.
- FR-002 `blueprint.generated.mk` MUST declare `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` before the `blueprint-uplift-status` target definition, and the `blueprint-uplift-status` recipe MUST invoke `@$(BLUEPRINT_UPLIFT_STATUS_SCRIPT)` in place of the hardcoded script path.
- FR-003 Both variable declarations MUST use the GNU Make conditional assignment operator (`?=`) so that a consumer-defined value set via `:=` in `make/platform.mk` (included after `blueprint.generated.mk`) takes precedence and produces no override warning.
- FR-004 The template file `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` MUST be updated with the same variable declarations and recipe substitutions as FR-001 and FR-002, and `make blueprint-render-makefile` MUST produce an `make/blueprint.generated.mk` identical to the manually-edited file.

### Non-Functional Requirements (Normative)
- NFR-REL-001 The change MUST be backward compatible: consumer repos that do not set `SPEC_SCAFFOLD_DEFAULT_TRACK` or `BLUEPRINT_UPLIFT_STATUS_SCRIPT` MUST observe behavior identical to the pre-fix state.
- NFR-OPS-001 Consumer repos that previously produced GNU Make `overriding commands for target` warnings for `spec-scaffold` or `blueprint-uplift-status` MUST produce no such warnings after adopting the updated `blueprint.generated.mk`.

## Normative Option Decision
- Option A: Expose `?=` configuration variables (`SPEC_SCAFFOLD_DEFAULT_TRACK`, `BLUEPRINT_UPLIFT_STATUS_SCRIPT`) in `blueprint.generated.mk.tmpl`; consumer overrides the variable in `platform.mk`, not the target. No structural change to include order or target definition.
- Option B: Restructure the consumer Makefile include order so `platform.mk` is included before `blueprint.generated.mk`, and use `?=`-style late-binding in blueprint targets. Requires changing the root `Makefile` template include ordering and verifying no existing targets rely on the current order.
- Selected option: OPTION_A
- Rationale: Option A is idiomatic GNU Make, requires minimal change (two variable declarations and two recipe token substitutions), and has no risk of breaking existing include-order assumptions. Option B is a deeper structural change with wider blast radius and no additional benefit over Option A given that the blueprint-first include order works correctly with `?=` defaults overridden by consumer `:=` assignments.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: adds `SPEC_SCAFFOLD_DEFAULT_TRACK` (default: `blueprint`) and `BLUEPRINT_UPLIFT_STATUS_SCRIPT` (default: `scripts/bin/blueprint/uplift_status.sh`) as documented consumer-settable override-point variables to the `blueprint.generated.mk` surface
- Docs contract: `docs/reference/generated/core_targets.generated.md` regenerated automatically by `quality-docs-sync-core-targets` (no content change expected — targets retain same help strings)

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/241
- Temporary workaround path: consumer re-defines affected targets in `make/platform.mk` after the blueprint include; GNU Make override warnings are emitted but behavior is functionally correct
- Replacement trigger: merged PR in blueprint repo that exposes the `?=` configuration variables for `spec-scaffold` and `blueprint-uplift-status`
- Workaround review date: 2026-07-30

## Normative Acceptance Criteria
- AC-001 MUST: running `make spec-scaffold SPEC_SLUG=foo` on a consumer repo where `SPEC_SCAFFOLD_DEFAULT_TRACK` is not set invokes `spec_scaffold.py --track blueprint` and produces no GNU Make override warning.
- AC-002 MUST: a consumer that sets `SPEC_SCAFFOLD_DEFAULT_TRACK := consumer` in `make/platform.mk` causes `make spec-scaffold` to invoke `spec_scaffold.py --track consumer` without triggering any `overriding commands` warning.
- AC-003 MUST: running `make blueprint-uplift-status` on a repo where `BLUEPRINT_UPLIFT_STATUS_SCRIPT` is not set invokes `scripts/bin/blueprint/uplift_status.sh` and produces no override warning.
- AC-004 MUST: a consumer that sets `BLUEPRINT_UPLIFT_STATUS_SCRIPT := scripts/bin/platform/blueprint/uplift_status.sh` in `make/platform.mk` causes the target to invoke the consumer script without triggering any `overriding commands` warning.
- AC-005 MUST: `tests/blueprint/test_quality_contracts.py` contains assertions that verify `SPEC_SCAFFOLD_DEFAULT_TRACK ?= blueprint` and `BLUEPRINT_UPLIFT_STATUS_SCRIPT ?= scripts/bin/blueprint/uplift_status.sh` are present in both the template file and the rendered `make/blueprint.generated.mk`.

## Informative Notes (Non-Normative)
- Context: GNU Make does not support per-target warning suppression for `overriding commands`. The `?=` / `:=` pattern is the idiomatic solution: blueprint sets the default with `?=`, consumer overrides with `:=` in a file included after blueprint, with no target re-definition required.
- Tradeoffs: The override-point surface is intentionally minimal (two variables). Additional targets are not covered in this work item; they can be added in follow-on items when consumer override needs are identified.
- Clarifications: none

## Explicit Exclusions
- Does not add `?=` override points for any Make targets beyond `spec-scaffold` and `blueprint-uplift-status`.
- Does not change the Makefile include order in the consumer root `Makefile` template.
- Does not add a `--warn-undefined-variables` global suppression mechanism.
