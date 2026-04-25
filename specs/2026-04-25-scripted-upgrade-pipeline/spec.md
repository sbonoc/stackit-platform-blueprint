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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260425-scripted-upgrade-pipeline.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-018
- Control exception rationale: SDD-C-017 excluded — no HTTP route, query/filter, or new API endpoint changes. SDD-C-019 excluded — no managed-service runtime decisions. SDD-C-020 excluded — this is a blueprint-internal tooling improvement with no consumer workaround lifecycle. SDD-C-021 excluded — no new API or event contracts introduced.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + bash; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest (existing `tests/blueprint/` suite; new integration fixtures)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: no managed service is provisioned or consumed; this work item adds Python scripts, shell orchestration, and Makefile targets only
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: no Kubernetes, Crossplane, or runtime identity components exercised; local-first profile declared for compliance only

## Objective
- Business outcome: The `blueprint-consumer-upgrade` runbook's ~30 open-interpretation decision points are replaced by a single deterministic make-target pipeline (`make blueprint-upgrade-consumer`). Consumer operators run one command, read one residual report, and commit. No free-form investigation is required. Every failure mode observed in the v1.0.0→v1.6.0 upgrade (F-001 through F-010) either becomes impossible or is surfaced with a prescribed action.
- Success metric: `make blueprint-upgrade-consumer BLUEPRINT_UPGRADE_REF=vX.Y.Z` runs end-to-end on a clean consumer working tree and exits 0 with no manual steps; `blueprint/contract.yaml` identity fields (`name`, `repo_mode`) are provably preserved by a new unit test; all existing upgrade gate tests continue to pass.

## Normative Requirements

### Functional Requirements (Normative)

#### Stage 1 — Pre-flight validation
- FR-001 The pipeline entry script MUST abort with a non-zero exit and a human-readable message when the consumer working tree contains unstaged or untracked changes.
- FR-002 The pipeline entry script MUST abort with a non-zero exit when `BLUEPRINT_UPGRADE_REF` is unset or does not resolve to a valid ref in `BLUEPRINT_UPGRADE_SOURCE`.
- FR-003 The pipeline entry script MUST abort with a non-zero exit when `blueprint/contract.yaml` is absent, unparseable, or has a `repo_mode` value other than `generated-consumer`.

#### Stage 2 — Apply with delete
- FR-004 The pipeline MUST invoke `blueprint-upgrade-consumer-apply` with `BLUEPRINT_UPGRADE_ALLOW_DELETE` set according to the open question resolution in Q-2; the flag MUST be overridable by the caller and MUST be documented in `make help` output.

#### Stage 3 — Contract file resolution
- FR-005 The contract resolver MUST preserve the consumer identity fields `name`, `repo_mode`, and `description` from the consumer's existing `blueprint/contract.yaml`, regardless of the values present in the blueprint source content.
- FR-006 The contract resolver MUST merge `required_files` by taking all entries from the blueprint source plus any consumer-added entries whose corresponding files exist on disk; consumer-added entries whose files no longer exist on disk MUST be dropped and recorded in the resolver's JSON decision report.
- FR-007 The contract resolver MUST evaluate every glob in `source_artifact_prune_globs_on_init` from both the blueprint source and the merged intermediate against the consumer's working tree; any glob that matches one or more existing paths MUST be dropped from the resolved output and recorded with the matching path count in the resolver's JSON decision report.
- FR-008 The contract resolver MUST emit a structured JSON decision report (`artifacts/blueprint/contract_resolve_decisions.json`) containing the list of dropped `required_files` entries, dropped prune globs, and the resolved identity fields written.

#### Stage 5 — Coverage gap detection and file fetch

- FR-009 The pipeline MUST compare all files referenced in `blueprint/contract.yaml` sections (`required_files`, `template_sync_allowlist`, `template_sync_prune_targets`) against files present on disk after Stage 2 apply.
- FR-010 For each referenced file that is absent from disk, the pipeline MUST fetch the file from `BLUEPRINT_UPGRADE_SOURCE` at `BLUEPRINT_UPGRADE_REF` using a local git operation against the already-cloned source repository; no external HTTP calls are permitted. Fetch scope is broad — any contract-referenced file absent from disk is fetched regardless of whether it appears in the upgrade plan.

#### Stage 6 — Bootstrap template mirror sync
- FR-011 For every file modified or created by Stages 2–5, the pipeline MUST check whether a path mirror exists under `scripts/templates/blueprint/bootstrap/<path>` and, if it exists, MUST overwrite the mirror with the workspace copy.

#### Stage 7 — Make target validation for new/changed docs
- FR-012 The pipeline MUST scan all markdown files created or modified by Stages 2–6 for fenced code blocks containing `make <target>`. For each `<target>` token found, the pipeline MUST verify the target appears in a `.PHONY` declaration across all `.mk` files in the consumer repository. Missing targets MUST be emitted as structured warnings in the residual report; Stage 7 MUST NOT abort the pipeline.

#### Stage 8 — Generated reference docs regeneration
- FR-013 The pipeline MUST run `make quality-docs-sync-generated-reference` exactly once after all file mutations from Stages 2–7 are complete; this is the single prescribed sync point for generated reference documentation.

#### Stage 9 — Gate chain
- FR-014 The pipeline MUST run `make infra-validate` followed by `make quality-hooks-run` in sequence. On first failure, the pipeline MUST abort and emit a structured error that includes the specific sub-check that failed and the file(s) involved.

#### Stage 10 — Residual report
- FR-015 The pipeline MUST always emit a residual report to `artifacts/blueprint/upgrade-residual.md`, even when the pipeline exits non-zero due to a partial failure.
- FR-016 Every item in the residual report MUST include a prescribed action (not a free-form note). Consumer-owned conflict files MUST include "resolve manually and re-run `make quality-hooks-run`." Missing make targets MUST include "add `.PHONY: <target>` stub to `make/platform.mk`." Dropped required_files entries MUST include "verify no consumer tooling references this path." Dropped prune globs MUST include "confirm no consumer content matches this pattern or adjust the glob in `blueprint/contract.yaml`."
- FR-017 The residual report MUST list all files classified as `consumer_owned_manual_review` in the reconcile report, with their prescribed action.
- FR-018 The residual report MUST list consumer test paths under `tests/` that are absent from `scripts/lib/quality/test_pyramid_contract.json` (pyramid classification gaps), with prescribed action "add an entry to `test_pyramid_contract.json`."
- FR-019 The existing individual make targets (`blueprint-upgrade-consumer-apply`, `blueprint-upgrade-consumer-validate`, `blueprint-upgrade-consumer-preflight`, `blueprint-upgrade-consumer-postcheck`, `blueprint-upgrade-fresh-env-gate`) MUST remain independently callable with unchanged behavior; `blueprint-upgrade-consumer` chains them but does not replace them.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The pipeline MUST NOT perform any external HTTP fetches. File retrieval in Stage 5 MUST use only local git operations against the already-cloned `BLUEPRINT_UPGRADE_SOURCE` repository.
- NFR-REL-001 Running `make blueprint-upgrade-consumer` twice on a clean working tree after a successful first run MUST produce no file changes and MUST exit 0 (idempotency).
- NFR-OPS-001 No consumer-specific logic (consumer name, module list, skill directory names) MUST appear in the pipeline scripts. All consumer-specific configuration MUST be read at runtime from `blueprint/contract.yaml`.
- NFR-OBS-001 The pipeline MUST emit a structured, stage-labeled progress line to stdout before and after each stage execution so that consumers can follow progress without reading source code.

## Normative Option Decision

### Q-1 — Stage 5 fetch scope
- Option A: Narrow — fetch only plan-covered `action=create` files absent from disk.
- Option B: Broad — fetch any contract-referenced file absent from disk regardless of plan coverage.
- Selected option: Option B — broad scope; fetch any contract-referenced file absent from disk regardless of plan coverage.
- Rationale: Option B provides a correct invariant independent of plan completeness, guards against partially interrupted prior runs, committed deletions of blueprint-managed files, and future contract section evolution not covered by the #185 planner audit. Decision by sbonoc PR comment 2026-04-25.

### Q-2 — BLUEPRINT_UPGRADE_ALLOW_DELETE default
- Option A: Delete enabled by default in the pipeline (`BLUEPRINT_UPGRADE_ALLOW_DELETE=true`); `=false` is an explicit non-destructive override that lists would-be deletions in the residual report.
- Option B: Delete disabled by default (consistent with current individual target behavior); `=true` must be set explicitly.

- Selected option: Option A — delete enabled by default (`BLUEPRINT_UPGRADE_ALLOW_DELETE=true`); `=false` is the explicit non-destructive override.
- Rationale: The primary motivation for this work item is deterministic end-to-end operation; keeping superseded files on disk is inconsistent with that goal and was the direct cause of F-003. The non-destructive mode remains available via `BLUEPRINT_UPGRADE_ALLOW_DELETE=false` override. Decision by sbonoc PR comment 2026-04-25.

## Contract Changes (Normative)
- Config/Env contract: New env var `BLUEPRINT_UPGRADE_ALLOW_DELETE` with pipeline default `true` (delete enabled); documented in `make help` and `SKILL.md`.
- API contract: none (no HTTP API)
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: New target `blueprint-upgrade-consumer`; existing targets unchanged. New artifacts: `artifacts/blueprint/contract_resolve_decisions.json`, `artifacts/blueprint/upgrade-residual.md`.
- Docs contract: `.agents/skills/blueprint-consumer-upgrade/SKILL.md` reduced from ~30-step runbook to 6-step flow; `references/manual_merge_checklist.md` updated.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 `make blueprint-upgrade-consumer BLUEPRINT_UPGRADE_REF=vX.Y.Z` runs end-to-end on a consumer repo with a clean working tree and exits 0 when all gates pass, with no additional manual steps required beyond reviewing the residual report.
- AC-002 `blueprint/contract.yaml` `name` and `repo_mode` fields are preserved through an upgrade cycle; verified by a new unit test that runs the contract resolver against a fixture conflict JSON and asserts identity fields are unchanged.
- AC-003 A file referenced in `blueprint/contract.yaml` `required_files` that is absent from disk after apply is automatically fetched from the upgrade source; verified by an integration test against a minimal fixture consumer.
- AC-004 Superseded files recorded as `action=skip` in the upgrade plan are deleted by Stage 2 (when delete is enabled); verified by the existing `blueprint-upgrade-fresh-env-gate` end-to-end test.
- AC-005 The residual report is always generated (even on partial pipeline failure) and every item has a prescribed action with no free-form notes.
- AC-006 Existing upgrade gate tests (`test_upgrade_consumer.py`, `test_upgrade_consumer_wrapper.py`, `test_upgrade_preflight.py`, `test_upgrade_postcheck.py`) continue to pass without modification.

## Informative Notes (Non-Normative)
- Context: This work item is the culmination of the consumer upgrade flow improvement programme (Phase 4 in the backlog). Phases 1–3 (foundation, correctness gates, reporting layer) are complete. This phase delivers the single-command UX on top of the proven baseline.
- Tradeoffs: Making delete the default (Q-2 Option A) trades user surprise (unexpected deletions) for deterministic outcomes (no orphan files). The residual report's prescribed actions are intentionally minimal — the goal is zero free-form investigation, not exhaustive guidance for every edge case.
- Clarifications:
  - F-009 (stale reconcile report) is not addressed by a new script stage — it is addressed by Stage 10's residual report which states "all gates passed; reconcile report snapshot is superseded by gate results." The existing partial fix from #179-187 already recomputes stale reconcile reports.
  - Stage 4 (auto-resolve non-contract conflicts) uses existing `source_content` take behavior; no new code is required for this stage — it is already the default behavior of the apply step for blueprint-managed files.

## Explicit Exclusions
- Changes to SDD lifecycle skills (step01–step07).
- Changes to the platform CI workflow (`.github/workflows/ci.yml`).
- Consumer application code.
- Incremental tag-to-tag upgrade mode (Issue #168 — separate work item).
- `BLUEPRINT_UPGRADE_DRY_RUN=true` flag (Issue #167 — separate work item; the `ALLOW_DELETE=false` mode is a partial overlap, not a substitute).
- Consumer-specific test pyramid classifications (surfaced in residual report as a gap; seeding is consumer-owned).
