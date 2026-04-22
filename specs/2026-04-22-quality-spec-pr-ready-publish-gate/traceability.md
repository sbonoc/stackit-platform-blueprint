# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | `_resolve_spec_dir` resolves spec dir from `SPEC_SLUG` env var or git branch | `scripts/bin/quality/check_spec_pr_ready.py:_resolve_spec_dir` | `BranchResolutionTests.test_spec_slug_env_var_overrides_branch`, `test_sdd_branch_pattern_resolves_spec_dir` | `architecture.md` context-B | `hooks_fast.sh` branch-pattern guard |
| FR-002 | SDD-C-005 | `_check_tasks` validates unchecked boxes, scaffold subjects, P-00N presence | `scripts/bin/quality/check_spec_pr_ready.py:_check_tasks` | `TasksCheckTests` (7 cases) | `spec.md` FR-002 | exit code |
| FR-003 | SDD-C-005 | `_check_plan` validates inline fields, slices, impact, risk mitigations | `scripts/bin/quality/check_spec_pr_ready.py:_check_plan` | `PlanCheckTests` (8 cases) | `spec.md` FR-003 | exit code |
| FR-004 | SDD-C-005 | `_check_hardening_review` validates findings, observability/arch fields, proposals | `scripts/bin/quality/check_spec_pr_ready.py:_check_hardening_review` | `HardeningReviewCheckTests` (7 cases) | `spec.md` FR-004 | exit code |
| FR-005 | SDD-C-005 | `_check_pr_context` validates inline fields, sub-bullets, scaffold proposals | `scripts/bin/quality/check_spec_pr_ready.py:_check_pr_context` | `PrContextCheckTests` (7 cases) | `spec.md` FR-005 | exit code |
| FR-006 | SDD-C-005 | label-aware placeholder detection via exact string matching per label | `scripts/bin/quality/check_spec_pr_ready.py` constants | negative-path tests per label variant | `spec.md` FR-006 | exit code |
| FR-007 | SDD-C-006 | `quality-spec-pr-ready` make target invokes `check_spec_pr_ready.py` | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl:quality-spec-pr-ready`, `make/blueprint.generated.mk` | `MissingSpecDirTests` | `spec.md` FR-007 | make exit code |
| FR-008 | SDD-C-006 | `hooks_fast.sh` branch-pattern guard invokes `quality-spec-pr-ready` | `scripts/bin/quality/hooks_fast.sh` | `PositivePathTests.test_fully_filled_spec_dir_exits_zero` | `spec.md` FR-008 | `hooks_fast.sh` log |
| NFR-SEC-001 | SDD-C-009 | all reads via `pathlib`; no subprocess except `git branch --show-current` | `scripts/bin/quality/check_spec_pr_ready.py:_resolve_spec_dir` | static review | `architecture.md` security note | n/a |
| NFR-OBS-001 | SDD-C-010 | violations printed with `[quality-spec-pr-ready] file:line: message` prefix | `scripts/bin/quality/check_spec_pr_ready.py:main` | all negative-path tests assert PREFIX in output | `spec.md` NFR-OBS-001 | stdout |
| NFR-REL-001 | SDD-C-011 | missing spec dir exits non-zero with clear diagnostic; missing file emits violation | `scripts/bin/quality/check_spec_pr_ready.py:main` | `MissingSpecDirTests` (2 cases) | `spec.md` NFR-REL-001 | exit code |
| NFR-OPS-001 | SDD-C-011 | `hooks_fast.sh` guard is branch-pattern conditional; zero cost on non-SDD branches | `scripts/bin/quality/hooks_fast.sh` | `BranchResolutionTests.test_non_sdd_branch_does_not_match_pattern` | `spec.md` NFR-OPS-001 | `hooks_fast.sh` |
| AC-001 | SDD-C-012 | fully-filled spec dir exits 0 | `scripts/bin/quality/check_spec_pr_ready.py:main` | `PositivePathTests.test_fully_filled_spec_dir_exits_zero` | `pr_context.md` | exit code 0 |
| AC-002 | SDD-C-012 | each scaffold placeholder type exits non-zero with prefixed message | all `_check_*` functions | all negative-path test classes | `pr_context.md` | exit code 1 |
| AC-003 | SDD-C-012 | branch `codex/YYYY-MM-DD-<slug>` → spec dir `specs/YYYY-MM-DD-<slug>` | `_resolve_spec_dir` | `BranchResolutionTests.test_sdd_branch_pattern_resolves_spec_dir` | `architecture.md` | resolved path |
| AC-004 | SDD-C-012 | missing spec dir exits non-zero with clear message | `main()` | `MissingSpecDirTests.test_nonexistent_spec_dir_exits_nonzero` | `spec.md` AC-004 | exit code 1 |
| AC-005 | SDD-C-006 | `quality-spec-pr-ready` present in both makefile files | template + rendered mk | `make quality-sdd-check` (makefile validation) | `spec.md` AC-005 | make target |
| AC-006 | SDD-C-006 | `hooks_fast.sh` invokes check on SDD branch; skips on non-SDD | `hooks_fast.sh` guard | `PositivePathTests.test_fully_filled_spec_dir_exits_zero` | `spec.md` AC-006 | `hooks_fast.sh` log |
| AC-007 | SDD-C-012 | all 39 tests in `test_spec_pr_ready.py` pass | `tests/blueprint/test_spec_pr_ready.py` | `python3 -m pytest tests/blueprint/test_spec_pr_ready.py` | `pr_context.md` validation evidence | test runner |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001
  - AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007

## Validation Summary
- Required bundles executed: `make quality-hooks-fast`, `make quality-sdd-check`, `make quality-docs-sync-all`, `make infra-contract-test-fast`, `SPEC_SLUG=2026-04-22-quality-spec-pr-ready-publish-gate make quality-spec-pr-ready`
- Result summary: all gates green; 39 new tests pass; `quality-spec-pr-ready` exits 0 on this spec's publish-gate files
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: update `check_spec_pr_ready.py` allowlist constants when `.spec-kit/templates/blueprint/` scaffold labels change (see hardening review proposal 1).
