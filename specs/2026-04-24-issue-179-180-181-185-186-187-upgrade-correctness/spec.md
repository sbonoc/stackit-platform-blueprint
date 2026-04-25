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
- ADR path: docs/blueprint/architecture/decisions/ADR-20260424-upgrade-correctness-bundle-179-180-181-185-186-187.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-018
- Control exception rationale: SDD-C-017 excluded — no HTTP route, query/filter, or new API endpoint changes. SDD-C-019 excluded — no managed-service runtime decisions. SDD-C-020 excluded — this work item IS the upstream blueprint fix; no consumer workaround lifecycle applies. SDD-C-021 excluded — no new API or event contracts introduced.

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + bash; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest (existing `tests/blueprint/` suite)
- Agent execution model: specialized-subagents-isolated-worktrees
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: no managed service is provisioned or consumed; this work item corrects blueprint-internal Python scripts and shell tooling only
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: this work item adds Python scripting and shell tooling corrections with no Kubernetes, Crossplane, or runtime identity components exercised; the local-first profile is declared for compliance; none of its runtime components are in scope

## Objective
- Business outcome: Six behavioral correctness bugs in blueprint upgrade tooling are eliminated. Upgrade gates produce accurate, actionable outputs. Consumer operators are not permanently blocked by stale reconcile data, false-positive behavioral findings, or silently incomplete upgrade plans. Generated CI workflows enforce least-privilege GITHUB_TOKEN posture by default.
- Success metric: All six regression tests (one per bug) pass; `make blueprint-upgrade-consumer-postcheck` unblocks after all conflicts are resolved; behavioral check produces zero false positives on canonical consumer shell files; upgrade planner emits warnings for uncovered source files; fresh-env gate fails on file-level divergence; generated `ci.yml` includes explicit permissions block.

## Normative Requirements

### Functional Requirements (Normative)

#### #179 — upgrade_reconcile_report: conflicts_unresolved state tracking
- FR-001 `build_upgrade_reconcile_report` MUST populate `conflicts_unresolved` with only those files that contain active `<<<<<<<` / `=======` / `>>>>>>>` merge markers in the current working tree at report-build time.
- FR-002 Files whose apply result is `merged` (auto-merged by the upgrade tool) MUST be excluded from `conflicts_unresolved`.
- FR-003 Files whose apply result was `conflict` but whose markers have since been manually cleared MUST be excluded from `conflicts_unresolved`.
- FR-004 The same file path MUST NOT be counted in `conflicts_unresolved` more than once regardless of how many source paths (plan entry vs apply result) reference it.

#### #180 — upgrade_shell_behavioral_check: false-positive call-site detection
- FR-005 `_find_unresolved_call_sites` MUST NOT classify the leading token of a case-label alternation line (`token|...)` or `token | ...`) as a function call site.
- FR-006 `_find_unresolved_call_sites` MUST NOT classify bare-word tokens on lines inside a `local`, `declare`, `readonly`, or `typeset` array initializer block (opened with `=(`) as function call sites.

#### #181 — upgrade_shell_behavioral_check: _EXCLUDED_TOKENS incomplete
- FR-007 `_EXCLUDED_TOKENS` MUST include `tar` and `pnpm` as common OS/tool commands.
- FR-008 `_EXCLUDED_TOKENS` MUST include all blueprint runtime functions guaranteed available via the standard bootstrap source chain: `blueprint_require_runtime_env`, `blueprint_sanitize_init_placeholder_defaults`, `ensure_file_from_template`, `ensure_file_from_rendered_template`, `postgres_init_env`, `object_storage_init_env`, `rabbitmq_seed_env_defaults`, `public_endpoints_seed_env_defaults`, `identity_aware_proxy_seed_env_defaults`, `keycloak_seed_env_defaults`, `render_optional_module_values_file`, `apply_optional_module_secret_from_literals`, `delete_optional_module_secret`.

#### #185 — upgrade planner: source tree completeness audit
- FR-009 The upgrade planner MUST audit every file in the blueprint source tree and identify files not reachable via `required_files`, `init_managed`, `conditional_scaffold_paths`, or `blueprint_managed_roots` (excluding `source_only` paths).
- FR-010 Each uncovered source file MUST produce a `WARNING` line to stderr and MUST be counted in the plan report JSON under `uncovered_source_files_count`.
- FR-011 The upgrade planner MUST raise a hard failure (non-zero exit) when any blueprint source file is uncovered; a plan with uncovered files MUST NOT be produced. The validate gate MUST additionally enforce `uncovered_source_files_count == 0` as a belt-and-suspenders check.

  Decision: Option A — hard failure in plan step. Rationale: uncovered files indicate a blueprint contract authoring error that MUST be caught before any consumer apply runs; this is consistent with issue #185 preferred behavior. Decision recorded from PR comment by sbonoc, 2026-04-25.

#### #186 — upgrade_fresh_env_gate: file-state divergence detection
- FR-012 After running `make infra-validate` and `make blueprint-upgrade-consumer-postcheck` in the clean worktree, the gate MUST collect checksums of all files under `artifacts/blueprint/` from both the clean worktree and the working tree.
- FR-013 Files whose checksums differ between the clean worktree and the working tree MUST be recorded in `fresh_env_gate.json` under `divergences` as a list of `{"path": "<relative-path>", "worktree_checksum": "...", "working_tree_checksum": "..."}` entries.
- FR-014 The gate MUST set `gate_status=fail` when `divergences` is non-empty, even when both make-target runs exit with code 0.

#### #187 — render_ci_workflow: GITHUB_TOKEN least-privilege enforcement
- FR-015 The `_render_ci` function MUST include a `permissions:` block in the generated `ci.yml` at the workflow level, placed after the `on:` trigger block and before the `jobs:` section.
- FR-016 The workflow-level `permissions` block MUST set `contents: read` at minimum, denying all other token scopes by default unless explicitly granted at the job level.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 Generated `ci.yml` files MUST enforce least-privilege GITHUB_TOKEN posture per the GitHub security hardening guide; no job SHALL inherit implicit write access to any token scope unless that scope is declared explicitly at the job level.
- NFR-OBS-001 All gate artifacts (`fresh_env_gate.json`, plan report JSON, reconcile report JSON) MUST record structured fields for gate outcome, divergence counts, and uncovered file counts so that CI tooling can parse and surface them without string matching.
- NFR-REL-001 The upgrade validate gate MUST enforce `uncovered_source_files_count == 0`; the postcheck gate MUST enforce `conflicts_unresolved_count == 0` only when active merge markers remain; the fresh-env gate MUST enforce zero divergences between clean-worktree and working-tree output files.
- NFR-OPS-001 All gate failures MUST emit a human-readable diagnostic to stderr naming the specific file(s), token(s), or path(s) causing the failure so operators can remediate without inspecting raw JSON artifacts.

## Normative Option Decision
- Option A: Implement FR-011 as a hard gate failure in the plan step (plan raises error when uncovered_source_files_count > 0).
- Option B: Implement FR-011 as warn-and-continue in plan step; validate gate enforces zero count.
- Selected option: OPTION_A
- Rationale: Catching uncovered files in the plan step prevents consumers from ever running an apply against an incomplete plan. Consistent with issue #185 preferred behavior. Confirmed by sbonoc via PR comment 2026-04-25.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none (no new make targets; existing targets produce corrected output)
- Docs contract: none

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this work item IS the blueprint fix)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 Given a consumer repo where all conflict markers have been manually resolved, `make blueprint-upgrade-consumer-postcheck` MUST complete without `conflicts_unresolved_count > 0` blocking the gate.
- AC-002 Given a consumer upgrade where the apply step auto-merges a file (apply result == `merged`), the reconcile report MUST NOT include that file in `conflicts_unresolved`.
- AC-003 A shell file containing `case "$var" in build|test) ... esac` MUST produce zero false-positive `unresolved_symbols` entries for `build` or `test`.
- AC-004 A shell file containing a multi-line `local modules=(\n  observability\n  postgres\n)` initializer MUST produce zero false-positive `unresolved_symbols` entries for `observability` or `postgres`.
- AC-005 A shell file calling `tar`, `pnpm`, or any of the thirteen blueprint runtime functions listed in FR-008 MUST produce zero `unresolved_symbols` findings from the behavioral check.
- AC-006 A blueprint source file not enumerated in `required_files`, `init_managed`, `conditional_scaffold_paths`, or `blueprint_managed_roots` MUST cause the upgrade planner to emit a `WARNING` to stderr and record `uncovered_source_files_count >= 1` in the plan report.
- AC-007 When `uncovered_source_files_count > 0` in the plan report, the upgrade validate gate MUST fail.
- AC-008 When `make infra-validate` produces a different output file under `artifacts/blueprint/` in the clean worktree versus the working tree (both runs exit 0), `fresh_env_gate.json` MUST contain a non-empty `divergences` array and `gate_status` MUST be `fail`.
- AC-009 Running `make blueprint-consumer-ci-render` (or the equivalent render step) on any consumer MUST produce a `ci.yml` that includes `permissions:\n  contents: read` at the workflow level, before `jobs:`.

## Informative Notes (Non-Normative)
- Context: All six bugs were filed on 2026-04-24 from consumer PR sbonoc/dhe-marketplace#40 observations. Issues #180 and #181 affect the same Python module and are bundled per AGENTS.backlog.md guidance. Issue #186 is the next layer after #182 (gitignored artifact seeding, fixed in v1.5.0): seeding made the gate runnable; this fix makes the gate actually verify CI equivalence.
- Tradeoffs: Bundling all six into one work item reduces PR overhead but increases review surface. The fixes are independent (disjoint files) and can be implemented in parallel delivery slices; the bundle is justified by the shared consumer-upgrade-flow scope and the same consumer PR that surfaced all six.
- Clarifications: Q-1 (FR-011 gate severity) resolved 2026-04-25: Option A selected — hard failure in plan step.

## Explicit Exclusions
- Issue #184 (consumer-extensible exclusion set for behavioral check) is explicitly excluded — it is a separate enhancement tracked as a follow-on to #181.
- Issue #189 (prune-glob enforcement) is explicitly excluded — it has its own work item (`specs/2026-04-24-issue-189-prune-glob-enforcement`).
- Issue #183 (stale reconcile report detection) is explicitly excluded — it is a separate P2 enhancement.
- Model-inversion of the upgrade planner (long-term fix for #185) is explicitly excluded — only the immediate completeness-audit fix (warnings + count in report JSON + validate gate) is in scope.
