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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-182-fresh-env-gate-artifact-seeding.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-011, SDD-C-014
- Control exception rationale: SDD-C-005/C-006 (API/event contract) not applicable — change is internal shell tooling with no external API surface. SDD-C-010 (frontend) not applicable. SDD-C-012/C-013/C-015–C-021 not applicable (no new modules, no database, no auth changes).

## Implementation Stack Profile (Normative)
- Backend stack profile: bash + python3 (existing upgrade tooling stack)
- Frontend stack profile: none
- Test automation profile: pytest (existing test suite in tests/blueprint/)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: stackit-managed-first
- Managed service exception rationale: not applicable — tooling-only change
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: not-applicable-stackit-runtime
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: tooling-only shell script change; no Kubernetes or runtime identity surface affected

## Objective
- Business outcome: After a successful consumer upgrade run, `make blueprint-upgrade-fresh-env-gate` MUST complete without failing due to missing gitignored upgrade artifacts in the temporary worktree, allowing the CI-equivalence comparison to reach and execute the actual postcheck validation logic.
- Success metric: `make blueprint-upgrade-fresh-env-gate` exits 0 after a complete upgrade run (plan + apply + conflict resolution) on a repo where the upgrade was performed correctly.

## Normative Requirements

### Functional Requirements (Normative)
- REQ-001 The gate MUST copy the directory `artifacts/blueprint/` from `$consumer_root` into the temporary worktree (at `$worktree_path/artifacts/blueprint/`) before invoking any make targets inside the worktree, when that directory exists in the working tree.
- REQ-002 The seeding step MUST be a no-op when `artifacts/blueprint/` does not exist in `$consumer_root`; the gate MUST NOT exit with an error caused by a missing artifact directory.
- REQ-003 The gate MUST emit a `log_info` message that includes the source path (`$consumer_root/artifacts/blueprint`) when the seeding step executes.
- REQ-004 The gate MUST emit a `log_info` message identifying the skip reason when the artifact directory is absent and seeding is skipped.
- REQ-005 Seeded artifacts MUST be removed unconditionally on gate exit (pass, fail, or interrupt) via the existing `_cleanup_worktree` EXIT trap; no additional cleanup logic is required.
- REQ-006 Seeded artifacts MUST NOT appear in the divergence report produced by `upgrade_fresh_env_gate.py`; the existing `_EXCLUDE_TOP_DIRS` set in the Python module already excludes `artifacts/` from divergence computation and MUST NOT be modified.
- REQ-007 A new integration test MUST verify that the gate exits 0 when `artifacts/blueprint/` is present in the working tree and postcheck succeeds after seeding.
- REQ-008 A new integration test MUST verify that the gate does not error on the seeding step when `artifacts/blueprint/` is absent, and continues to run `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` normally.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The seeding operation MUST copy only `artifacts/blueprint/` and MUST NOT traverse or copy any path outside that subdirectory. The `artifacts/blueprint/` path contains only JSON/text upgrade report files with no secret material by contract; no `.env`, credential, or token files reside in this path.
- NFR-OBS-001 The gate MUST emit a `log_info` message on artifact seeding (REQ-003) and on seeding skip (REQ-004). No new metrics are required; the existing `blueprint_upgrade_fresh_env_gate_status_total` metric is sufficient.
- NFR-REL-001 The existing `_cleanup_worktree` EXIT trap removes the worktree directory unconditionally via `rm -rf`; seeded artifacts inside the worktree are cleaned up by this trap with no additional code required.
- NFR-OPS-001 When the seeding step executes, the log message MUST include both the source path and the destination path to support diagnosis of seeding failures in CI logs.

## Normative Option Decision
- Option A: Seed `artifacts/blueprint/` via `cp -r` in `upgrade_fresh_env_gate.sh`, immediately after `worktree_created=true`, before any make targets are invoked.
- Option B: Pass artifact paths as environment variables to the make targets inside the worktree and update postcheck to accept them.
- Selected option: OPTION_A
- Rationale: Option A accurately models what a CI pipeline does (prior pipeline steps produce artifacts, the postcheck step consumes them in a clean checkout). Option A is a localized 8-line addition to the shell script with zero changes to downstream make targets or the Python module. Option B would require changes to at least three components (the shell script, the Makefile, and the postcheck script) and introduces coupling between the gate and the postcheck's internal path handling.

## Contract Changes (Normative)
- Config/Env contract: none — no new environment variables; existing `BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH` is unchanged.
- API contract: none.
- Event contract: none.
- Make/CLI contract: none — `make blueprint-upgrade-fresh-env-gate` invocation signature is unchanged.
- Docs contract: `docs/blueprint/architecture/execution_model.md` MUST be updated to document the artifact-seeding step in the fresh-env gate description.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: https://github.com/sbonoc/stackit-platform-blueprint/issues/182
- Temporary workaround path: `scripts/bin/blueprint/upgrade_fresh_env_gate.sh` (artifact seeding added locally in consumer repo)
- Replacement trigger: merged fix in blueprint repo + next consumer upgrade
- Workaround review date: 2026-07-24

## Normative Acceptance Criteria
- AC-001 Given a consumer repo where `artifacts/blueprint/` exists and contains valid upgrade reports, when `make blueprint-upgrade-fresh-env-gate` is run after a successful upgrade, the gate MUST exit 0.
- AC-002 Given a consumer repo where `artifacts/blueprint/` does not exist, when the gate runs, the seeding step MUST be skipped and the gate MUST proceed to run `make infra-validate` and `make blueprint-upgrade-consumer-postcheck`; the gate MUST NOT exit non-zero due to the absent artifact directory alone.
- AC-003 After the gate exits (any outcome), `git worktree list` MUST report exactly one worktree entry (the main worktree); seeded artifacts MUST NOT remain on disk.
- AC-004 When seeding occurs, the gate log output MUST contain a message with the string `seeding blueprint upgrade artifacts` and the source path.
- AC-005 The divergence report (`fresh_env_gate.json`) MUST NOT list any file under `artifacts/` in the `divergences` array, whether or not seeding occurred.

## Informative Notes (Non-Normative)
- Context: `git worktree add <path> HEAD` initializes the worktree from the git object store. Gitignored files — including all of `artifacts/` — are absent by design. The postcheck (`blueprint_upgrade_consumer_postcheck.py`) treats missing artifacts as a hard failure. Seeding the artifacts into the worktree before running the postcheck is the minimal, correct fix.
- Tradeoffs: Seeding copies potentially large JSON report files. In practice, `artifacts/blueprint/` contains 3–5 JSON files totalling a few KB per upgrade run; the copy cost is negligible.
- Clarifications: none.

## Explicit Exclusions
- This work item does NOT modify the divergence computation logic in `upgrade_fresh_env_gate.py`; `_EXCLUDE_TOP_DIRS` already excludes `artifacts/`.
- This work item does NOT change the postcheck script or any make targets.
- This work item does NOT introduce new environment variables or configuration surface.
