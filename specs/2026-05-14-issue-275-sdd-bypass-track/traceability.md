# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-015 | N/A | architecture.md §Bounded Context | `scripts/bin/quality/check_sdd_assets.py` — `SPEC_READY_EXCEPTION` field parsing | `test_sdd_bypass_track.py::test_exception_field_accepted` | `AGENTS.md` §Lightweight SDD Bypass Track | `quality-sdd-check` gate output |
| FR-002 | SDD-C-011, SDD-C-015 | N/A | ADR §Decision | `check_sdd_assets.py` — `authorized-by` validation | `test_sdd_bypass_track.py::test_missing_authorized_by_raises_violation` (AC-005) | `AGENTS.md` §Lightweight SDD Bypass Track | `quality-sdd-check` gate output |
| FR-003 | SDD-C-005, SDD-C-015 | N/A | architecture.md §Gate Evaluation Flow | `check_sdd_assets.py` — bypass branch skips non-essential artifact checks | `test_sdd_bypass_track.py::test_bypass_path_skips_artifact_checks` (AC-001) | ADR §Decision | `quality-sdd-check` gate output |
| FR-004 | SDD-C-007, SDD-C-015 | N/A | architecture.md §Gate Evaluation Flow | `check_sdd_assets.py` — warning demotion logic | `test_sdd_bypass_track.py` — impl-tasks-checked warning test | `AGENTS.md` §Lightweight SDD Bypass Track | `quality-sdd-check` warning output |
| FR-005 | SDD-C-005, SDD-C-015 | N/A | ADR §Decision | `check_sdd_assets.py` — full-SDD path unchanged | `test_sdd_bypass_track.py::test_full_sdd_path_unaffected` (AC-003) | spec.md §Explicit Exclusions | `quality-sdd-check` gate output |
| FR-006 | SDD-C-010 | N/A | architecture.md §Non-Functional Architecture Notes | `check_sdd_assets.py` — `[METRIC] name=sdd_exception_gate_total` emit | `test_sdd_bypass_track.py::test_metric_emitted` (AC-004) | `AGENTS.md` §Lightweight SDD Bypass Track | CI job log |
| FR-007 | SDD-C-005, SDD-C-014 | N/A | plan.md §Slice 1 | `spec_scaffold.py` or spec.md template — `SPEC_READY_EXCEPTION: none` and `authorized-by: none` defaults | `make quality-sdd-check` on a freshly scaffolded spec | `AGENTS.md` §Lightweight SDD Bypass Track | scaffold output |
| NFR-SEC-001 | SDD-C-011 | N/A | ADR §Decision | `authorized-by` field in spec.md | AC-005 test (missing field → violation) | `AGENTS.md` §authorized-by requirement | git log audit trail |
| NFR-OBS-001 | SDD-C-010 | N/A | architecture.md §Non-Functional Architecture Notes | `[METRIC]` line in `check_sdd_assets.py` | AC-004 test (metric line emitted) | `AGENTS.md` §Lightweight SDD Bypass Track | CI job log `sdd_exception_gate_total` |
| NFR-REL-001 | SDD-C-012 | N/A | architecture.md §Reliability | backward-compatible defaults (`SPEC_READY_EXCEPTION: none`); no existing spec.md migration | AC-002 (no specs/ dir → exit 0); AC-003 (full-SDD path unaffected) | spec.md §Contract Changes | remove exception field → full-SDD restored |
| NFR-OPS-001 | N/A | N/A | N/A | N/A — developer tooling change; no Kubernetes runtime operation affected | N/A | spec.md §NFR-OPS-001 (declared not applicable) | N/A |
| NFR-A11Y-001 | N/A | N/A | N/A | N/A — no UI surfaces introduced or modified | N/A | spec.md §NFR-A11Y-001 (declared not applicable) | N/A |
| AC-001 | SDD-C-012 | N/A | N/A | `tests/blueprint/test_sdd_bypass_track.py` | pytest pass | N/A | N/A |
| AC-002 | SDD-C-012 | N/A | N/A | `tests/blueprint/test_sdd_bypass_track.py` | pytest pass | N/A | N/A |
| AC-003 | SDD-C-012 | N/A | N/A | `tests/blueprint/test_sdd_bypass_track.py` | pytest pass | N/A | N/A |
| AC-004 | SDD-C-010, SDD-C-012 | N/A | N/A | `tests/blueprint/test_sdd_bypass_track.py` | pytest pass | N/A | N/A |
| AC-005 | SDD-C-011, SDD-C-012 | N/A | N/A | `tests/blueprint/test_sdd_bypass_track.py` | pytest pass | N/A | N/A |
| AC-006 | SDD-C-016 | N/A | N/A | `make quality-sdd-check` on this work item's own spec.md | quality-sdd-check PASS | N/A | N/A |

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
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - NFR-A11Y-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006

## Validation Summary
- Required bundles executed: (to be completed at Verify phase)
- Result summary: (to be completed at Verify phase)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Consider adding a `SPEC_READY_EXCEPTION: chore` + active `AGENTS.decisions.md` validation (Q-1 Option B) if future audit requirements demand machine-verifiable chore governance. Parked — surfaces on-scope: quality.
