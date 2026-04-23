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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260423-issue-163-fresh-env-smoke-gate.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-016, SDD-C-017, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: SDD-C-013 not applicable (no managed service provisioned). SDD-C-014 not applicable (no K8s/Crossplane/ESO components). SDD-C-015 not applicable (no app delivery workflow scope). SDD-C-018 not applicable (this is the blueprint fix, not a consumer workaround). SDD-C-022 not applicable (no HTTP routes or API endpoints). SDD-C-023 not applicable (no filter or payload-transform logic). SDD-C-024: any reproducible finding from the gate script MUST be translated to an automated test (covered in plan).

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + subprocess; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: Tooling-only Bash/Python script change; no managed service is provisioned or consumed by this work item.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: This change adds shell and Python tooling with no K8s, Crossplane, or runtime identity components. The local-first profile is declared for compliance; none of its runtime components are exercised by this work item.

## Objective
- Business outcome: Consumer upgrade runs that pass the existing postcheck gate are also validated for CI-equivalent behavior before the developer opens a PR, eliminating the systematic class of failures where working-tree-present files mask bootstrap correctness regressions that only surface in CI's clean-checkout environment.
- Success metric: A gate-green upgrade run signals that `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` both exit 0 in a clean-checkout-equivalent worktree; the developer can open the PR with confidence that CI will not see a different result than local.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The fresh-env gate MUST create a temporary git worktree from the HEAD of the consumer upgrade branch immediately after `make blueprint-upgrade-consumer-postcheck` exits 0 and before the upgrade is declared complete.
- FR-002 The fresh-env gate MUST run `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` inside the temporary worktree, inheriting the parent shell environment unchanged.
- FR-003 The fresh-env gate MUST exit non-zero if any target exits non-zero inside the worktree; on failure the gate MUST diff the worktree file state against the post-apply working tree and MUST include a diagnostic divergence list (file, reason) in the JSON report and inline stdout.
- FR-004 The gate script MUST register an EXIT trap that calls `git worktree remove --force <worktree-path>`, so the worktree is unconditionally removed when the gate script exits, regardless of outcome (pass, fail, or interrupt).
- FR-005 The gate MUST exit non-zero if worktree creation fails for any reason (unclean index, git lock contention, disk error, or missing git binary); the upgrade MUST NOT be declared complete when worktree creation fails.
- FR-006 The gate MUST write a structured JSON report to `artifacts/blueprint/fresh_env_gate.json` AND emit inline stdout progress during execution; the JSON report is the canonical artifact for CI/CD consumption.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 The worktree MUST NOT execute uncommitted content; the worktree is created from a committed HEAD only. Environment variable inheritance from the parent shell is acceptable because the worktree runs the same make targets under the same trust boundary as the parent upgrade run.
- NFR-OBS-001 The JSON report MUST include the fields: `status` (pass|fail|error), `worktree_path` (string), `targets_run` (list of strings), `divergences` (list of {file, reason}), `error` (string|null), `exit_code` (int). The shell wrapper MUST emit metric `blueprint_upgrade_fresh_env_gate_status_total` with label `status=pass|fail|error` after the gate completes.
- NFR-REL-001 The gate MUST be idempotent — re-running on the same committed HEAD MUST produce the same outcome. The gate MUST NOT mutate the working tree; the temporary worktree is isolated from the working tree by design.
- NFR-OPS-001 Gate failure output MUST be actionable: inline stdout and the JSON report MUST identify the diverging files and the nature of the divergence (failing target, exit code, file diff) so the developer can understand the CI-equivalent failure without additional diagnosis.

## Normative Option Decision
- Option A: Run the post-upgrade smoke check inside a temporary git worktree created from the upgrade branch HEAD. The worktree starts clean (no working-tree files). Discard the worktree after the check.
- Option B: For each file managed by `ensure_file_with_content` and `ensure_infra_template_file`, temporarily rename or hide the file, run bootstrap, and verify the outcome.
- Selected option: OPTION_A
- Rationale: Option A creates a self-contained environment that faithfully reproduces CI's clean-checkout state without requiring a maintained manifest of bootstrap-managed files. The worktree approach imposes no additional preconditions beyond those already required by the upgrade flow (clean commit state). Option B requires a separately maintained file manifest that can diverge from actual bootstrap behavior as tooling evolves, and is more invasive to the working tree.

## Contract Changes (Normative)
- Config/Env contract: New env var `BLUEPRINT_UPGRADE_FRESH_ENV_GATE_PATH` (default: `artifacts/blueprint/fresh_env_gate.json`) accepted by the gate shell wrapper to allow artifact path override.
- API contract: none
- Event contract: none
- Make/CLI contract: New make target `blueprint-upgrade-fresh-env-gate` added to `make/blueprint.generated.mk` (and template counterpart); called after `blueprint-upgrade-consumer-postcheck` in the upgrade sequence; `blueprint/contract.yaml` MUST declare this target as required. New files: `scripts/bin/blueprint/upgrade_fresh_env_gate.sh`, `scripts/lib/blueprint/upgrade_fresh_env_gate.py`.
- Docs contract: `docs/blueprint/` reference docs for the upgrade skill MUST be updated to document the fresh-env gate, its position in the upgrade sequence, and the JSON artifact schema.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this is the blueprint fix itself)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 Given a consumer upgrade branch where a bootstrap-managed file is absent in a clean checkout, when the gate runs, then at least one target inside the worktree exits non-zero, the gate exits non-zero, and `fresh_env_gate.json` has `status=fail` with the failing target and diverging files identified.
- AC-002 Given a consumer upgrade branch where all bootstrap-managed files reproduce correctly from scratch, when the gate runs, then both targets inside the worktree exit 0, the gate exits 0, and `fresh_env_gate.json` has `status=pass`.
- AC-003 Given worktree creation fails for any reason, when the gate is invoked, then the gate exits non-zero, the upgrade is blocked, and `fresh_env_gate.json` has `status=error` if the artifact path is writable.
- AC-004 Given a gate run interrupted by SIGINT or SIGTERM, when the EXIT trap fires, then the temporary worktree is removed via `git worktree remove --force` and the worktree path is absent from `git worktree list`.
- AC-005 Given a successful gate run, when the gate exits 0, then `artifacts/blueprint/fresh_env_gate.json` exists with `status=pass` and the temporary worktree is absent from `git worktree list`.

## Informative Notes (Non-Normative)
- Context: This is Phase 2, Issue #163 of the consumer upgrade flow improvement programme. Phase 1 (#169) introduced the CI e2e upgrade validation lane; #162 added the post-merge behavioral validation gate. This gate adds CI-equivalent environment simulation during the local upgrade run, completing the local/CI signal parity objective.
- Tradeoffs: The worktree approach adds overhead proportional to the time required to run `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` inside a clean environment. No time budget is enforced; the gate completes when the targets finish. This is consistent with the existing postcheck contract.
- Clarifications: Environment variable inheritance is intentional and acceptable because the parent upgrade run already trusts the developer's environment. The worktree is created from a committed HEAD only, so no uncommitted content is executed.

## Explicit Exclusions
- Opt-out flag for the fresh-env gate (gate is mandatory, no skip mechanism).
- Time budget enforcement or gate timeout.
- Sanitized or restricted environment for the worktree run.
- Deep source-chain or transitive dependency analysis of bootstrap-managed files.
- Detection of divergences in non-file artifacts (environment variables, in-memory state).
