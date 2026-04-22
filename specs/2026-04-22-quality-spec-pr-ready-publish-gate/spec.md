# Specification

## Spec Readiness Gate (Blocking)
- SPEC_READY: true
- Open questions count: 0
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 0
- Product sign-off: approved
- Architecture sign-off: approved
- Security sign-off: approved
- Operations sign-off: approved
- ADR path: docs/blueprint/architecture/decisions/ADR-20260422-quality-spec-pr-ready-publish-gate.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_plus_fastapi_pydantic_v2
- Frontend stack profile: vue_router_pinia_onyx
- Test automation profile: pytest_vitest_playwright_pact
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: none
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: none

## Objective
- Business outcome: Eliminate the class of defects where SDD publish-gate files (plan.md, tasks.md, hardening_review.md, pr_context.md) ship with unfilled scaffold placeholders, because `quality-sdd-check` only validates the five readiness-gate files and provides no coverage for the four publish-gate files.
- Success metric: Running `quality-spec-pr-ready` on a spec dir with any unfilled placeholder exits non-zero and names the file and offending line; running it on a fully-filled spec dir exits 0. `hooks_fast.sh` invokes the check automatically on SDD branches with zero cost on non-SDD branches.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 MUST resolve the active spec directory from `SPEC_SLUG` env var when set; otherwise MUST derive it from the current git branch name matching pattern `codex/YYYY-MM-DD-<slug>` by extracting the date-prefixed slug segment.
- FR-002 MUST validate `tasks.md`: every task box in sections G-00N, T-00N, T-10N, T-20N, P-00N, A-00N MUST be `[x]`; tasks P-001, P-002, P-003 MUST explicitly appear as `[x]`; no task line MUST contain verbatim scaffold subject text (`Update contract/governance surfaces`, `Implement runtime/code changes`, `Update blueprint docs/diagrams`, `Update consumer-facing docs/diagrams when contracts/behavior change`).
- FR-003 MUST validate `plan.md`: constitution-gate lines MUST have non-empty content after the field colon; delivery-slice lines MUST be concrete (not bare `Slice 1:` or `Slice 2:` with nothing after the colon); change-strategy fields MUST be non-empty (`Migration/rollout sequence:`, `Backward compatibility policy:`, `Rollback plan:`); validation-strategy fields MUST be non-empty; app-onboarding impact MUST resolve to exactly one of `no-impact` or `impacted` without the scaffold suffix `(select one)`; operational-readiness fields MUST be non-empty; risk lines MUST have content after the ` -> mitigation:` separator.
- FR-004 MUST validate `hardening_review.md`: the `Repository-Wide Findings Fixed` section MUST contain at least one entry with non-empty content after the label colon; the `Observability and Diagnostics Changes` sub-fields MUST be non-empty; the `Architecture and Code Quality Compliance` sub-fields MUST be non-empty; the `Proposals Only` section MUST contain at least one entry with non-empty content after the label colon, or an explicit `none` or `N/A` statement (bare scaffold default `Proposal 1:` alone MUST NOT pass).
- FR-005 MUST validate `pr_context.md`: required fields (`Work item:`, `Objective:`, `Scope boundaries:`, `Requirement IDs covered:`, `Acceptance criteria covered:`, `Required commands executed:`, `Result summary:`, `Main risks:`, `Rollback strategy:`) MUST be non-empty; the `Primary files to review first:` section MUST contain at least one non-empty bullet; no deferred-proposal line MUST contain the scaffold default text (`not implemented):` with nothing after the colon).
- FR-006 MUST apply label-aware scaffold-placeholder detection to all four files: lines matching `- <Label>:` (label followed by colon and nothing else) where the label text is verbatim from the scaffold template MUST be rejected; the check MUST be label-aware to avoid false positives on intentionally terse single-word fields.
- FR-007 The `quality-spec-pr-ready` make target MUST invoke `check_spec_pr_ready.py` and exit non-zero on any violation.
- FR-008 `hooks_fast.sh` MUST invoke `quality-spec-pr-ready` when the current git branch matches pattern `codex/[0-9]{4}-[0-9]{2}-[0-9]{2}-` and the resolved spec directory exists; MUST skip silently when the branch does not match or the spec directory is absent.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 All file reads MUST be in-process Python via `pathlib`; no subprocess invocation or shell expansion; no path traversal beyond the resolved spec directory.
- NFR-OBS-001 Each violation message MUST include the file name, the specific check that failed, and sufficient context for the author to locate and fix the issue; prefix MUST be `[quality-spec-pr-ready]`.
- NFR-REL-001 A missing or unresolvable spec directory MUST exit non-zero with a clear diagnostic message and MUST NOT silently pass.
- NFR-OPS-001 `hooks_fast.sh` integration MUST be conditional with zero runtime cost on non-SDD branches; the gate MUST be skippable by setting `SPEC_SLUG=` (empty) or by working on a branch not matching the SDD pattern.

## Normative Option Decision
- Option A: Standalone script `scripts/bin/quality/check_spec_pr_ready.py` invoked from a new `quality-spec-pr-ready` make target, wired into `hooks_fast.sh` with a branch-pattern guard — same pattern as `check_sdd_assets.py`.
- Option B: Extend `check_sdd_assets.py` to also validate publish-gate files.
- Selected option: OPTION_A
- Rationale: Option B entangles readiness-gate validation (which runs in all contexts) with publish-gate validation (which is SDD-branch-specific). Option A keeps responsibilities separate, allows the publish-gate check to be skipped cheaply on non-SDD branches, and follows the existing single-responsibility pattern of the quality script suite.

## Contract Changes (Normative)
- Config/Env contract: `SPEC_SLUG` env var accepted by `check_spec_pr_ready.py` to override branch-derived spec dir resolution.
- API contract: none
- Event contract: none
- Make/CLI contract: new target `quality-spec-pr-ready` added to `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl` and regenerated into `make/blueprint.generated.mk`.
- Docs contract: new core-targets doc entry for `quality-spec-pr-ready`; ADR added.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 MUST: `check_spec_pr_ready.py` exits 0 for a fully-filled spec dir where all four files contain concrete content and no scaffold placeholders.
- AC-002 MUST: `check_spec_pr_ready.py` exits non-zero with a `[quality-spec-pr-ready]`-prefixed error naming the file and offending line for each type of scaffold placeholder across all four files.
- AC-003 MUST: branch-name slug resolution correctly derives the spec dir from a branch named `codex/YYYY-MM-DD-<slug>`.
- AC-004 MUST: a missing spec directory causes `check_spec_pr_ready.py` to exit non-zero with a clear diagnostic; a branch not matching the SDD pattern causes it to exit non-zero with a clear diagnostic when `SPEC_SLUG` is also unset.
- AC-005 MUST: the `quality-spec-pr-ready` make target is present in both `make/blueprint.generated.mk` and `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`.
- AC-006 MUST: `hooks_fast.sh` invokes `quality-spec-pr-ready` on a branch matching the SDD pattern when the spec dir exists, and skips silently on non-SDD branches.
- AC-007 MUST: all new tests in `tests/blueprint/test_spec_pr_ready.py` pass, including positive-path, per-file negative-path, branch-resolution, and missing-spec-dir cases.

## Informative Notes (Non-Normative)
- Context: `quality-sdd-check` enforces readiness-gate files (spec.md, architecture.md, context_pack.md, traceability.md, graph.json, evidence_manifest.json) but has no coverage for the four publish-gate files. Authors can open a PR with all-scaffold plan.md, tasks.md, hardening_review.md, or pr_context.md undetected.
- Tradeoffs: label-aware placeholder detection (FR-006) avoids false positives on intentionally short fields, at the cost of a static label allowlist that must be updated if the scaffold templates change.
- Clarifications: none

## Explicit Exclusions
- Validating files other than the four publish-gate files is out of scope; readiness-gate file validation remains owned by `check_sdd_assets.py`.
- Scanning for semantic completeness (e.g. whether the stated objective matches the implementation) is out of scope; only structural/placeholder completeness is checked.
