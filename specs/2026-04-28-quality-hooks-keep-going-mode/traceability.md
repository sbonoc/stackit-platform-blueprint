# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | architecture.md § Bounded Contexts (Context A) | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-002, AC-003, AC-006) | docs/blueprint/operations/<quality-gates-doc>.md (path TBD Slice 5), ADR-20260428 | log_metric quality_hooks_keep_going_total |
| FR-002 | SDD-C-005 | architecture.md § Bounded Contexts (Context A) | scripts/bin/quality/hooks_strict.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_strict_keep_going.py (AC-002, AC-006) | docs/blueprint/operations/<quality-gates-doc>.md, ADR-20260428 | log_metric quality_hooks_keep_going_total |
| FR-003 | SDD-C-005 | architecture.md § Bounded Contexts (Context B) | scripts/bin/quality/hooks_run.sh | tests/blueprint/test_quality_hooks_run_keep_going.py (AC-005, AC-006) | ADR-20260428 § Decision (cross-phase ordering) | combined exit code |
| FR-004 | SDD-C-005, SDD-C-009 | architecture.md § Bounded Contexts (pre-commit invariant) | scripts/bin/quality/hooks_fast.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-004) | ADR-20260428 § Decision (pre-commit fail-fast) | log_info pre-commit start |
| FR-005 | SDD-C-005, SDD-C-012 | architecture.md § High-Level Component Design | scripts/bin/quality/hooks_fast.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_fast_keep_going.py (AC-002) | ADR-20260428 § Decision | summary block emission |
| FR-006 | SDD-C-005, SDD-C-012 | architecture.md § High-Level Component Design | scripts/bin/quality/hooks_strict.sh, scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_strict_keep_going.py | ADR-20260428 § Decision | summary block emission |
| FR-007 | SDD-C-012 | architecture.md § Presentation/API/workflow boundaries | scripts/lib/shell/keep_going.sh (`keep_going_finalize`) | tests/blueprint/test_quality_hooks_keep_going.py (AC-007) | ADR-20260428 § Summary block | marker line `===== quality-hooks keep-going summary =====` |
| FR-008 | SDD-C-012 | architecture.md § Application layer | scripts/lib/shell/keep_going.sh (`keep_going_finalize`), scripts/bin/quality/hooks_run.sh | tests/blueprint/test_quality_hooks_run_keep_going.py (AC-005) | ADR-20260428 § Decision | exit code |
| FR-009 | SDD-C-005 | architecture.md § Risks (Risk 1, mitigation) | scripts/bin/quality/hooks_fast.sh, hooks_strict.sh, hooks_run.sh | T-105 contract test (default-path byte-equivalence) | ADR-20260428 § Consequences | absence of summary marker on default invocation |
| FR-010 | SDD-C-005 | architecture.md § Presentation boundary | scripts/bin/quality/hooks_fast.sh, hooks_strict.sh, hooks_run.sh `--help` | tests/blueprint/test_quality_hooks_*_keep_going.py (AC-006) | ADR-20260428 | `--help` output |
| NFR-SEC-001 | SDD-C-009 | architecture.md § Non-Functional (Security) | scripts/lib/shell/keep_going.sh | T-101 (cleanup trap), code review | ADR-20260428 § Consequences | EXIT trap removes ${TMPDIR}/quality_hook_* |
| NFR-OBS-001 | SDD-C-010 | architecture.md § Non-Functional (Observability) | scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_keep_going.py (AC-007 part b/c) | ADR-20260428 | log_metric quality_hooks_keep_going_total + tail re-emission |
| NFR-REL-001 | SDD-C-005 | architecture.md § Non-Functional (Reliability) | scripts/lib/shell/keep_going.sh (EXIT trap composition) | manual signal-injection test in T-201 | ADR-20260428 § Consequences | EXIT trap fires on SIGTERM |
| NFR-OPS-001 | SDD-C-010 | architecture.md § Bounded Contexts (Context B) | scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl, make/blueprint.generated.mk | T-201 (`make help` output check) | docs/blueprint/operations/<quality-gates-doc>.md (Slice 5) | `make help` lists env var |
| AC-001 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh default path | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Consequences | exit on first failure, no summary marker |
| AC-002 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh keep-going path + helper | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | summary block |
| AC-003 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh env-var trigger | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | env-var honored |
| AC-004 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_fast.sh pre-commit fail-fast block | tests/blueprint/test_quality_hooks_fast_keep_going.py | ADR-20260428 § Decision | abort before downstream |
| AC-005 | SDD-C-012 | spec.md § Normative Acceptance Criteria | hooks_run.sh cross-phase orchestration | tests/blueprint/test_quality_hooks_run_keep_going.py | ADR-20260428 § Decision | combined exit |
| AC-006 | SDD-C-012 | spec.md § Normative Acceptance Criteria | --help text in three scripts | tests/blueprint/test_quality_hooks_*_keep_going.py | --help output | docs cross-reference |
| AC-007 | SDD-C-012 | spec.md § Normative Acceptance Criteria | scripts/lib/shell/keep_going.sh | tests/blueprint/test_quality_hooks_keep_going.py | ADR-20260428 § Decision | helper contract |
| AC-008 | SDD-C-012 | spec.md § Normative Acceptance Criteria | make/blueprint.generated.mk recipes | T-201 manual run + log capture | docs operations doc | env var propagation |

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
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007
  - AC-008

## Validation Summary
- Required bundles executed: pending implementation
- Result summary: pending implementation
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: After merge, evaluate whether the agent harness should auto-export `QUALITY_HOOKS_KEEP_GOING=true` for SDD inner-loop verification phases (separate work item; not in scope here).
- Follow-up 2: Parallel execution of independent checks remains a deferred optimization (see ADR Alternative D).
- Follow-up 3: Structured (JSON) summary output for machine consumers remains deferred (see Explicit Exclusions item 4).
