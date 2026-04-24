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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-189-prune-glob-enforcement.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-011, SDD-C-014
- Control exception rationale: SDD-C-005/C-006 (API/event contract) not applicable — change is internal upgrade tooling with no external API surface. SDD-C-010 (frontend) not applicable. SDD-C-012/C-013/C-015-C-021 not applicable.

## Implementation Stack Profile (Normative)
- Backend stack profile: python3 (existing upgrade tooling stack)
- Frontend stack profile: none
- Test automation profile: pytest (existing test suite in tests/blueprint/)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: not applicable — tooling-only change
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: tooling-only Python module change; no Kubernetes or runtime identity surface affected

## Objective
- Business outcome: After a consumer upgrade, `make blueprint-upgrade-consumer-validate` MUST detect any files matching `source_artifact_prune_globs_on_init` that were re-introduced into the consumer working tree and fail with actionable output. `make blueprint-upgrade-consumer-postcheck` MUST block on non-empty violations. The upgrade skill runbook MUST instruct operators to verify prune globs after manual merge actions.
- Success metric: A generated-consumer repo containing any file matching the prune globs MUST cause both validate and postcheck to exit non-zero, with the violation files named in the report and on stderr.

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 `upgrade_consumer_validate.py` MUST read `source_artifact_prune_globs_on_init` from `blueprint/contract.yaml` when `repo_mode` is `generated-consumer` and perform a glob-match scan of the consumer working tree against each pattern.
- REQ-002 `upgrade_consumer_validate.py` MUST collect all repo-relative POSIX paths matching any prune glob into a `violations` list and include a `prune_glob_check` section in `upgrade_validate.json` with fields: `status` (`success` | `failure` | `skipped`), `globs_checked` (list of patterns), `violations` (sorted list of matching relative paths), `violation_count` (int), `remediation_hint` (string).
- REQ-003 `upgrade_consumer_validate.py` MUST set the overall validate `status` to `failure` when `prune_glob_check.violation_count > 0`.
- REQ-004 `upgrade_consumer_validate.py` MUST emit a stderr diagnostic message listing each violation path and its matching glob pattern when violations are found.
- REQ-005 The prune glob scan MUST be skipped (`prune_glob_check.status = "skipped"`) and MUST NOT affect overall validate status when `repo_mode` is NOT `generated-consumer`.
- REQ-006 The prune glob scan MUST be skipped (`prune_glob_check.status = "skipped"`) when the contract cannot be loaded; the existing `contract_load_error` gate covers this failure path.
- REQ-007 `upgrade_consumer_postcheck.py` MUST read `prune_glob_check` from the validate report and surface `violation_count` and `violations` as a `prune_glob_violations` section in `upgrade_postcheck.json`.
- REQ-008 `upgrade_consumer_postcheck.py` MUST add `prune-glob-violations` to `blocked_reasons` when `prune_glob_check.violation_count > 0`.
- REQ-009 `.agents/skills/blueprint-consumer-upgrade/SKILL.md` MUST add an explicit required check step after manual merge resolution instructing operators to verify that no files matching the prune globs were introduced, naming the canonical glob patterns by value.
- REQ-010 A unit test MUST verify that the prune glob scan returns matching paths when a file matching a prune glob exists in the working tree.
- REQ-011 A unit test MUST verify that the prune glob scan returns an empty violations list when no files match any prune glob.
- REQ-012 A unit test MUST verify that the prune glob scan returns status `skipped` when repo mode is `template-source`.
- REQ-013 An integration test MUST verify that `upgrade_consumer_validate.py` exits non-zero and the report includes `prune_glob_check.violations` when matching files are present.
- REQ-014 An integration test MUST verify that `upgrade_consumer_postcheck.py` exits non-zero and includes `prune-glob-violations` in `blocked_reasons` when the validate report contains violations.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The prune glob scan MUST use Python `pathlib.Path.rglob()` with patterns from `blueprint/contract.yaml` exclusively — no shell expansion, no subprocess. The implementation MUST NOT follow symlinks that resolve outside the repo root.
- NFR-OBS-001 The validate module MUST emit one stderr line per violation in the format `prune-glob violation: <path> (matches: <glob>)`; no new metrics are required.
- NFR-REL-001 If the contract cannot be loaded, the prune glob check MUST be set to `skipped` with no additional failure contribution beyond the existing `contract_load_error` block.
- NFR-OPS-001 The `prune_glob_check.remediation_hint` field MUST name the exact files to remove and the command to re-run validation.

## Normative Option Decision
- Option A: Add prune glob check to `upgrade_consumer_validate.py` (post-apply validate phase) and surface the result in postcheck via the validate report. Update skill runbook.
- Option B: Add new `prune-glob-excluded` / `prune-glob-violation` action types to the upgrade planner (`upgrade_consumer.py`), requiring plan JSON schema changes and a new planner code path.
- Selected option: OPTION_A
- Rationale: The validate module already loads the contract and scans the working tree. Adding the check there is additive (one new function, one new JSON section) with no schema-breaking changes to plan or apply artifacts. Option B requires planner schema changes and is more invasive for a check that is naturally a post-apply concern.

## Contract Changes (Normative)
- Config/Env contract: none — no new environment variables.
- API contract: none.
- Event contract: none.
- Make/CLI contract: none — `make blueprint-upgrade-consumer-validate` and `make blueprint-upgrade-consumer-postcheck` invocation signatures are unchanged.
- Docs contract: `docs/blueprint/architecture/execution_model.md` MUST be updated to document the prune glob check in the validate phase. `.agents/skills/blueprint-consumer-upgrade/SKILL.md` MUST add the required check step (REQ-009).

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/189
- Temporary workaround path: none — sbonoc/dhe-marketplace correction commit `0ca5d0f` restores correct state; future upgrades rely on this blueprint fix.
- Replacement trigger: merged fix in blueprint repo + next consumer upgrade
- Workaround review date: 2026-07-24

## Normative Acceptance Criteria
- AC-001 Given a generated-consumer repo containing `docs/blueprint/architecture/decisions/ADR-foo.md`, when `make blueprint-upgrade-consumer-validate` is run, `upgrade_validate.json` MUST include `prune_glob_check.violations` containing that path and `prune_glob_check.status = "failure"`, and the command MUST exit non-zero.
- AC-002 Given a generated-consumer repo with no files matching any prune glob, when `make blueprint-upgrade-consumer-validate` is run, `prune_glob_check.status` MUST be `"success"`, `violations` MUST be empty, and the command MUST NOT fail due to the prune glob check alone.
- AC-003 Given a validate report with `prune_glob_check.violation_count > 0`, when `make blueprint-upgrade-consumer-postcheck` is run, `upgrade_postcheck.json` MUST include `prune-glob-violations` in `blocked_reasons` and the command MUST exit non-zero.
- AC-004 Given a `template-source` repo, when `make blueprint-upgrade-consumer-validate` is run, `prune_glob_check.status` MUST be `"skipped"` and MUST NOT contribute to a validate failure.
- AC-005 The upgrade skill runbook MUST contain a required check step naming the glob patterns `specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*` and `docs/blueprint/architecture/decisions/ADR-*.md`.

## Informative Notes (Non-Normative)
- Context: `source_artifact_prune_globs_on_init` is declared in `blueprint/contract.yaml` and applied at init time to remove blueprint-internal artifacts (ADRs, work-item specs) from generated-consumer repos. Without upgrade-phase enforcement, an operator who manually adds "missing" files after apply can re-introduce these artifacts. Reported from sbonoc/dhe-marketplace#40 — 25 ADRs re-introduced.
- Tradeoffs: The validate gate runs after the operator resolves manual merges; there is a window between apply and validate where violations can exist undetected. This is acceptable — violations are surfaced before the upgrade branch is pushed.
- Clarifications: Enforcement must be blueprint-owned. Planner changes (option B) are explicitly deferred.

## Explicit Exclusions
- This work item does NOT add new plan action types to the upgrade planner or modify plan/apply JSON schemas.
- This work item does NOT modify `upgrade_consumer.py`.
- This work item does NOT introduce new environment variables or CLI flags.
- This work item does NOT add prune glob enforcement to consumer repos directly.
