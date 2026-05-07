# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | architecture.md § Bounded Contexts (Context A) | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-002, AC-003, AC-006) | docs/blueprint/operations/<quality-gates-doc>.md (path resolved in Slice 10), ADR-20260428 | log_metric quality_hooks_keep_going_total |
| FR-002 | SDD-C-005 | architecture.md § Bounded Contexts (Context A) | scripts/bin/quality/hooks_strict.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_strict_keep_going.py (AC-002, AC-006) | docs/blueprint/operations/<quality-gates-doc>.md, ADR-20260428 | log_metric quality_hooks_keep_going_total |
| FR-003 | SDD-C-005 | architecture.md § Bounded Contexts (Context B) | scripts/bin/quality/hooks_run.sh | tests/blueprint/test_quality_hooks_run_keep_going.py (AC-005, AC-006) | ADR-20260428 § Decision (cross-phase ordering) | combined exit code |
| FR-004 | SDD-C-005, SDD-C-009 | architecture.md § Bounded Contexts (pre-commit invariant) | scripts/bin/quality/hooks_fast.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-004) | ADR-20260428 § Decision (pre-commit fail-fast) | log_info pre-commit start |
| FR-005 | SDD-C-005, SDD-C-012 | architecture.md § High-Level Component Design | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-002) | ADR-20260428 § Decision | summary block emission |
| FR-006 | SDD-C-005, SDD-C-012 | architecture.md § High-Level Component Design | scripts/bin/quality/hooks_strict.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_strict_keep_going.py | ADR-20260428 § Decision | summary block emission |
| FR-007 | SDD-C-012 | architecture.md § Presentation/API/workflow boundaries | scripts/lib/shell/keep_going.sh (`keep_going_finalize`) | tests/blueprint/test_quality_hooks_keep_going.py (AC-007) | ADR-20260428 § Summary block | marker line `===== quality-hooks keep-going summary =====` |
| FR-008 | SDD-C-012 | architecture.md § Application layer | scripts/lib/shell/keep_going.sh (`keep_going_finalize`), scripts/bin/quality/hooks_run.sh | tests/blueprint/test_quality_hooks_run_keep_going.py (AC-005) | ADR-20260428 § Decision | exit code |
| FR-009 | SDD-C-005 | architecture.md § Risks (Risk 1, mitigation) | scripts/bin/quality/hooks_fast.sh, hooks_strict.sh, hooks_run.sh | T-105 contract test (default-path byte-equivalence) | ADR-20260428 § Consequences | absence of summary marker on default invocation |
| FR-010 | SDD-C-005 | architecture.md § Presentation boundary | scripts/bin/quality/hooks_fast.sh, hooks_strict.sh, hooks_run.sh `--help` | tests/blueprint/test_quality_hooks_*_keep_going.py (AC-006) | ADR-20260428 | `--help` output |
| FR-011 | SDD-C-005, SDD-C-012 | architecture.md § Bounded Contexts (Context C) | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/quality_gating.sh | tests/blueprint/test_quality_hooks_fast_path_gating.py (AC-009, AC-010, AC-011) | ADR-20260428 § Decision (path-gating), operations doc (path-gating set) | log_metric quality_hooks_skip_total + log_info skipping |
| FR-012 | SDD-C-005, SDD-C-012 | architecture.md § Bounded Contexts (Context C) | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/quality_gating.sh | tests/blueprint/test_quality_hooks_fast_spec_ready_gating.py (AC-012, AC-013, AC-011) | ADR-20260428 § Decision (phase-gating), operations doc | log_metric quality_hooks_skip_total + log_info skipping |
| FR-013 | SDD-C-005 | architecture.md § Application layer (dedup) | scripts/bin/quality/hooks_fast.sh | tests/blueprint/test_quality_hooks_fast_dedup.py (AC-014) | ADR-20260428 § Decision (dedup), operations doc | log_warn when pre-commit missing |
| FR-014 | SDD-C-005 | architecture.md § Bounded Contexts (Context D) | .agents/skills/blueprint-sdd-step05-implement/SKILL.md | tests/blueprint/test_step05_skill_per_slice_gate.py (AC-015) | ADR-20260428 § Decision (skill clarification) | SKILL.md content invariants |
| FR-015 | SDD-C-005, SDD-C-019, SDD-C-020 | architecture.md § Bounded Contexts (Context D, governance) | AGENTS.md, scripts/templates/consumer/init/AGENTS.md.tmpl | tests/blueprint/test_agents_md_quality_hooks_subsection.py (AC-016) | ADR-20260428 § Decision 6 (cross-skill propagation) | canonical normative subsection |
| FR-016 | SDD-C-005 | architecture.md § Bounded Contexts (Context D) | .agents/skills/blueprint-sdd-step04-plan-slicer/SKILL.md, blueprint-sdd-step05-implement/SKILL.md, blueprint-sdd-step07-pr-packager/SKILL.md, blueprint-consumer-upgrade/SKILL.md, blueprint-consumer-ops/SKILL.md, references/* | tests/blueprint/test_skill_quality_hooks_cross_links.py (AC-017) | ADR-20260428 § Decision 6 | cross-link line in each skill |
| FR-017 | SDD-C-005, SDD-C-020 | architecture.md § Bounded Contexts (Context D, env propagation) | .envrc, .claude/settings.json | tests/blueprint/test_envrc_and_claude_settings.py (AC-018) | ADR-20260428 § Decision 6 | env exports and settings.json env block |
| NFR-SEC-001 | SDD-C-009 | architecture.md § Non-Functional (Security) | scripts/lib/shell/keep_going.sh | T-101 (cleanup trap), code review | ADR-20260428 § Consequences | EXIT trap removes ${TMPDIR}/quality_hook_* |
| NFR-OBS-001 | SDD-C-010 | architecture.md § Non-Functional (Observability) | scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_keep_going.py (AC-007 part b/c) | ADR-20260428 | log_metric quality_hooks_keep_going_total + tail re-emission |
| NFR-REL-001 | SDD-C-005 | architecture.md § Non-Functional (Reliability) | scripts/lib/shell/keep_going.sh (EXIT trap composition) | manual signal-injection test in T-201 | ADR-20260428 § Consequences | EXIT trap fires on SIGTERM |
| NFR-OPS-001 | SDD-C-010 | architecture.md § Bounded Contexts (Context B) | scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl, make/blueprint.generated.mk | T-201 (`make help` output check) | docs/blueprint/operations/<quality-gates-doc>.md (Slice 10) | `make help` lists env var |
| NFR-OBS-002 | SDD-C-010 | architecture.md § High-Level Component Design (skip metric) | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/quality_gating.sh | T-107, T-108 (skip-metric assertions) | ADR-20260428 § Consequences | quality_hooks_skip_total emitted |
| NFR-OPS-002 | SDD-C-010 | architecture.md § Bounded Contexts (Context C) | scripts/bin/quality/hooks_fast.sh `--help`, make.tmpl doc-comments | T-103, T-201 | docs/blueprint/operations/<quality-gates-doc>.md (Slice 10) | --help mentions QUALITY_HOOKS_FORCE_FULL |
| AC-001 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh default path | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Consequences | exit on first failure, no summary marker |
| AC-002 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh keep-going path + helper | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | summary block |
| AC-003 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh env-var trigger | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | env-var honored |
| AC-004 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh pre-commit fail-fast block | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | abort before downstream |
| AC-005 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_run.sh cross-phase orchestration | tests/blueprint/test_quality_hooks_run_keep_going.py | ADR-20260428 § Decision | combined exit |
| AC-006 | SDD-C-012 | spec.md § Normative Acceptance Criteria | --help text in three scripts | tests/blueprint/test_quality_hooks_*_keep_going.py | --help output | docs cross-reference |
| AC-007 | SDD-C-012 | spec.md § Normative Acceptance Criteria | scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_keep_going.py | ADR-20260428 § Decision | helper contract |
| AC-008 | SDD-C-012 | spec.md § Normative Acceptance Criteria | make/blueprint.generated.mk recipes | T-201 manual run + log capture | docs operations doc | env var propagation |
| AC-009 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh path-gate dispatch | tests/blueprint/test_quality_hooks_fast_path_gating.py | ADR-20260428 § Decision (path-gating) | skip metric for both infra checks |
| AC-010 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh path-gate dispatch | tests/blueprint/test_quality_hooks_fast_path_gating.py | ADR-20260428 § Decision (path-gating) | both infra checks executed |
| AC-011 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh QUALITY_HOOKS_FORCE_FULL handling | tests/blueprint/test_quality_hooks_fast_path_gating.py + test_quality_hooks_fast_spec_ready_gating.py | ADR-20260428 § Decision (force-full) | force-full overrides all gates |
| AC-012 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh phase-gate block | tests/blueprint/test_quality_hooks_fast_spec_ready_gating.py | ADR-20260428 § Decision (phase-gating) | quality-spec-pr-ready skipped on intake |
| AC-013 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh phase-gate block | tests/blueprint/test_quality_hooks_fast_spec_ready_gating.py | ADR-20260428 § Decision (phase-gating) | quality-spec-pr-ready runs on SPEC_READY=true |
| AC-014 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh dedup edits | tests/blueprint/test_quality_hooks_fast_dedup.py | ADR-20260428 § Decision (dedup) | grep + log-line absence |
| AC-015 | SDD-C-012 | spec.md § Normative Acceptance Criteria | .agents/skills/blueprint-sdd-step05-implement/SKILL.md | tests/blueprint/test_step05_skill_per_slice_gate.py | ADR-20260428 § Decision (skill clarification) | SKILL.md content assertions |
| AC-016 | SDD-C-012 | spec.md § Normative Acceptance Criteria | AGENTS.md, scripts/templates/consumer/init/AGENTS.md.tmpl | tests/blueprint/test_agents_md_quality_hooks_subsection.py | ADR-20260428 § Decision 6 | subsection title + body invariants |
| AC-017 | SDD-C-012 | spec.md § Normative Acceptance Criteria | six skill files + references | tests/blueprint/test_skill_quality_hooks_cross_links.py | ADR-20260428 § Decision 6 | canonical cross-link line present |
| AC-018 | SDD-C-012 | spec.md § Normative Acceptance Criteria | .envrc, .claude/settings.json | tests/blueprint/test_envrc_and_claude_settings.py | ADR-20260428 § Decision 6 | env exports verified |
| AC-019 | SDD-C-012 | spec.md § Normative Acceptance Criteria | AGENTS.md + consumer-init AGENTS.md.tmpl drift | T-201 (manual run) | quality-sdd-check-all output | gate passes |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - FR-007
  - FR-008
  - FR-009
  - FR-010
  - FR-011
  - FR-012
  - FR-013
  - FR-014
  - FR-015
  - FR-016
  - FR-017
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-OBS-002
  - NFR-REL-001
  - NFR-OPS-001
  - NFR-OPS-002
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007
  - AC-008
  - AC-009
  - AC-010
  - AC-011
  - AC-012
  - AC-013
  - AC-014
  - AC-015
  - AC-016
  - AC-017
  - AC-018
  - AC-019

## Validation Summary
- Required bundles executed: `make quality-hooks-fast` (keep-going active via `.envrc`, ~169s, 2 failures: quality-spec-pr-ready + quality-docs-check-changed — both fixed during validation); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` (~174s, 1 failure: quality-spec-pr-ready — fixed after completing publish artifacts); `QUALITY_HOOKS_FORCE_FULL=true make quality-hooks-fast` (~176s, 1 failure: quality-spec-pr-ready — fixed after completing publish artifacts); `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-run` (~294s, fast phase all pass, strict phase 1 pre-existing failure: blueprint-template-smoke bash 3.x declare -A on macOS — unrelated to this work item); `python3 -m pytest tests/blueprint/ -q` (793 tests, all pass); `make docs-build` (pass, after MDX `&lt;1 s` escape fix and broken AGENTS.md link fix); `make docs-smoke` (pass); `make quality-hardening-review` (pass); `make quality-sdd-check` (pass).
- Result summary: all implementation tasks complete; 793 unit tests pass; docs build and smoke pass; hardening review passes; quality-spec-pr-ready passes after completing all publish artifacts; `quality-docs-check-changed` required running `sync_blueprint_template_docs.py` to sync the new `docs/blueprint/governance/quality_hooks.md` to the blueprint template; `blueprint-template-smoke` strict-phase failure is a pre-existing macOS bash 3.x incompatibility (declare -A) unrelated to this work item.
- Documentation validation:
  - `make docs-build`: PASS (~13s) after two fixes: (1) `&lt;1 s` MDX escape in ADR line 18; (2) removed broken relative link to `AGENTS.md` (repo root, not in docs site) from `quality_hooks.md`.
  - `make docs-smoke`: PASS

## T-201 Timing Evidence

| Command | Mode | Duration | Outcome |
|---|---|---|---|
| `make quality-hooks-fast` (`.envrc` sets `KEEP_GOING=true`) | keep-going | 169s | 2 failures (quality-spec-pr-ready: publish incomplete; quality-docs-check-changed: template sync needed) |
| `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` | keep-going explicit | 174s | 1 failure (quality-spec-pr-ready: publish incomplete) |
| `QUALITY_HOOKS_FORCE_FULL=true make quality-hooks-fast` | force-full + keep-going | 176s | 1 failure (quality-spec-pr-ready: publish incomplete) |
| `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-run` | full run keep-going | 294s | 1 failure strict phase (blueprint-template-smoke: pre-existing macOS bash 3.x) |
| `make quality-hooks-fast` (all tasks complete) | keep-going | ~170s | final run — see T-202 sample block |

Baseline pre-PR: ~107s (fail-fast, full infra path). New docs/spec-only path target: &lt;15s with path-gating active.

## T-202 Summary Block Sample

```
===== quality-hooks keep-going summary =====
  shellcheck                                         PASS (89s)
  quality-root-dir-prelude-check                     PASS (0s)
  quality-infra-shell-source-graph-check             PASS (0s)
  quality-sdd-check-all                              PASS (0s)
  quality-spec-pr-ready                              PASS (0s)
  quality-ci-check-sync                              PASS (0s)
  quality-docs-check-changed                         PASS (7s)
  infra-validate                                     PASS (9s)
  infra-contract-test-fast                           PASS (68s)
===== all checks passed =====
```

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: After merge, evaluate whether the agent harness should auto-export `QUALITY_HOOKS_KEEP_GOING=true` for SDD inner-loop verification phases (separate work item; not in scope here).
- Follow-up 2: Parallel execution of independent checks remains a deferred optimization (see ADR Alternative D).
- Follow-up 3: Structured (JSON) summary output for machine consumers remains deferred (see Explicit Exclusions item 4).
