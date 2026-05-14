# Specification

## Spec Readiness Gate (Blocking)
<!-- SPEC_PRODUCT_READY=true: intake gate — Product sign-off only; unlocks agent ADR drafting.
     SPEC_READY=true: implementation gate — all sign-offs required; unlocks coding. -->
- SPEC_READY: false
- SPEC_PRODUCT_READY: false
- Open questions count: 2
- Unresolved alternatives count: 0
- Unresolved TODO markers count: 0
- Pending assumptions count: 0
- Open clarification markers count: 2
- Product sign-off: pending
- Architecture sign-off: pending
- Security sign-off: pending
- Operations sign-off: pending
- Missing input blocker token: none
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-275-sdd-bypass-track.md
- ADR status: proposed

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017
- Control exception rationale:
  - SDD-C-009: N/A — no new secrets, authentication, or authorization surfaces introduced.
  - SDD-C-013: N/A — no STACKIT managed service involved; this is blueprint governance tooling.
  - SDD-C-018: N/A — this IS the blueprint governance fix, not a consumer-side workaround.
  - SDD-C-019: N/A — no async messaging surfaces.
  - SDD-C-020: N/A — no OpenAPI specification changes.
  - SDD-C-021: N/A — no Pact contract changes.
  - SDD-C-022: N/A — no HTTP route or API endpoint changes.
  - SDD-C-023: N/A — no filter or payload-transform logic.
  - SDD-C-024: N/A — no version pin changes.

## Implementation Stack Profile (Normative)
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: this work item is blueprint governance tooling (a Python script + AGENTS.md policy update); no STACKIT runtime service module is introduced or modified.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: custom-approved-exception
- Local-first exception rationale: blueprint governance tooling change — no Kubernetes runtime deployment required

## Objective
- Business outcome: Every fix, refactor, upgrade, and chore change can complete full governance traceability with a proportionate artifact set — eliminating the current choice between governance theater (10 stub artifacts) and ungoverned shortcuts. Maintenance velocity increases without relaxing audit standards.
- Success metric: `quality-sdd-check` passes for a `specs/` dir containing only `spec.md` + `pr_context.md` when `SPEC_READY_EXCEPTION: upgrade` is set with `authorized-by: <handle>`; `quality-sdd-check` also passes when no `specs/` dir exists (chore path); all existing full-SDD specs continue to pass without change.

## Normative Requirements

### Functional Requirements (Normative)
- FR-001 `spec.md` MUST support a new optional `SPEC_READY_EXCEPTION` field in the Spec Readiness Gate section with exactly one of the allowed values: `bug-fix`, `upgrade`, `refactor`, `chore`, `authorized-deviation`. Absence of the field MUST be treated as equivalent to no exception (full SDD applies).
- FR-002 When `SPEC_READY_EXCEPTION` is set to any value other than `none`, `spec.md` MUST also carry an `authorized-by: <handle>` field in the Spec Readiness Gate section. The `authorized-by` field MUST NOT be empty, `none`, or a placeholder.
- FR-003 `check_sdd_assets.py` MUST, when processing a `spec.md` with a valid `SPEC_READY_EXCEPTION` and a non-empty `authorized-by`, skip all artifact-existence requirements beyond `{spec.md, pr_context.md}` (i.e., skip checks for `plan.md`, `tasks.md`, `architecture.md`, `traceability.md`, `graph.json`, `evidence_manifest.json`, `context_pack.md`, `hardening_review.md`).
- FR-004 `check_sdd_assets.py` MUST treat the "implementation tasks are checked while SPEC_READY is not true" violation as a non-blocking warning (printed to stdout with a `[WARNING]` prefix, not counted as a failure) when `SPEC_READY_EXCEPTION` is set with a non-empty `authorized-by`.
- FR-005 `check_sdd_assets.py` MUST NOT change its validation behavior for any `spec.md` that has `SPEC_READY: true` and no `SPEC_READY_EXCEPTION` set. All existing artifact checks MUST continue to apply.
- FR-006 `check_sdd_assets.py` MUST emit a structured log metric line `[METRIC] name=sdd_exception_gate_total value=1 type=<exception-type> authorized_by=<handle>` to stdout for every spec evaluated via the exception path.
- FR-007 The `spec.md` scaffold template MUST include `SPEC_READY_EXCEPTION: none` and `authorized-by: none` as default values in the Spec Readiness Gate section so new work items are explicit about their exception status.

### Non-Functional Requirements (Normative)
- NFR-SEC-001 The `authorized-by` field MUST provide a human-readable audit trail for every exception-path evaluation. No machine authentication is introduced; the field is a governance assertion, not an access control gate.
- NFR-OBS-001 The metric line emitted per FR-006 MUST follow the blueprint structured log format `[METRIC] name=<metric_name> value=<int> <label=value>...` so existing log parsers and CI summaries can consume it without modification.
- NFR-REL-001 The exception mechanism MUST be opt-in and purely additive: removing `SPEC_READY_EXCEPTION` from a `spec.md` MUST immediately restore full-SDD validation with no migration step. No existing `spec.md` file requires modification.
- NFR-OPS-001 N/A — this is a developer tooling change. No Kubernetes runtime operation is affected.
- NFR-A11Y-001 N/A — no UI surfaces introduced or modified.

## Normative Option Decision
- Option A: Add `SPEC_READY_EXCEPTION` field to spec.md + update `check_sdd_assets.py` to reduce required artifacts for exception types (field-gated per-spec).
- Option B: Add a separate lightweight spec template (e.g. `spec.lite.md`) that the scaffold creates when a `--type bug-fix` flag is passed, with the checker detecting the file name.
- Selected option: OPTION_A
- Rationale: Option A keeps a single spec format and a single checker code path; the exception field is self-documenting inside the artifact; existing tooling (scaffold, spec-pr-ready, quality-hooks-fast) requires no structural changes. Option B fragments the artifact surface, requires changes to the scaffold CLI, and creates two parallel spec validation code paths that will drift.

## Contract Changes (Normative)
- Config/Env contract: `spec.md` Spec Readiness Gate section gains two new optional fields: `SPEC_READY_EXCEPTION` (allowed values: `none`, `bug-fix`, `upgrade`, `refactor`, `chore`, `authorized-deviation`) and `authorized-by` (non-empty handle when exception is set). These fields have default values `none` so existing spec.md files are unaffected.
- API contract: none
- OpenAPI / Pact contract path: none
- Event contract: none
- Make/CLI contract: none — no new or changed make targets or CLI flags.
- Docs contract: `AGENTS.md` gains a new subsection documenting the lightweight bypass track, allowed exception types, and the `authorized-by` requirement.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria
- AC-001 A regression test MUST parse a synthetic `spec.md` with `SPEC_READY_EXCEPTION: upgrade` and a valid `authorized-by`, invoke the checker logic, and assert that no artifact-existence violations are raised for missing `plan.md`, `tasks.md`, `traceability.md`, `graph.json`, `evidence_manifest.json`, `context_pack.md`, `hardening_review.md`.
- AC-002 A regression test MUST invoke `check_sdd_assets.py` against a repository state with no `specs/` directory and assert that the script exits 0 (existing behavior preserved; regression guard).
- AC-003 A regression test MUST parse a synthetic `spec.md` with `SPEC_READY: true` and no `SPEC_READY_EXCEPTION` and assert that all 10-artifact existence checks still apply (no regression for full-SDD path).
- AC-004 A regression test MUST parse a synthetic `spec.md` with `SPEC_READY_EXCEPTION: bug-fix` and `authorized-by: testuser` and assert that the metric line `name=sdd_exception_gate_total` is emitted to stdout.
- AC-005 A regression test MUST parse a synthetic `spec.md` with `SPEC_READY_EXCEPTION: bug-fix` but NO `authorized-by` field (or `authorized-by: none`) and assert that the checker raises a violation requiring `authorized-by` to be set.
- AC-006 `make quality-sdd-check` MUST pass for this work item's own `spec.md` (self-consistency gate).

## Informative Notes (Non-Normative)
- Context: The motivating case is `sbonoc/dhe-marketplace` PR #62 — a blueprint v1.10.0 upgrade corrective convergence that required 10 stub SDD artifacts to satisfy `quality-sdd-check`. The workaround (`AGENTS.decisions.md` deviation record) is the current approach; FR-001–006 make it unnecessary by providing a first-class supported path.
- Tradeoffs: Exception-path specs skip traceability.md and graph.json, so requirement-to-test linkage is not machine-verifiable for bypass-track work items. This is acceptable for fix/refactor/upgrade/chore changes where the traceability takes a different form (failing test, pipeline report, etc.) and is documented in pr_context.md.
- Clarifications:

  > **[NEEDS CLARIFICATION — Q-1]** For the `chore` exception type with NO `specs/` directory at all: MUST `quality-sdd-check` actively verify that `AGENTS.decisions.md` contains an entry referencing the current PR/branch, or is the passive pass (checker finds no specs to validate) sufficient?
  >
  > **Options:**
  > - **A)** Passive pass is sufficient — the checker iterates over existing `specs/*/spec.md` files; if none exist, it passes. The `AGENTS.decisions.md` requirement is a process convention documented in `AGENTS.md`, not a technical gate. (Agent recommendation)
  > - **B)** Active verification — the checker reads the current git branch, extracts the PR number, and searches `AGENTS.decisions.md` for a matching entry.
  >
  > **Agent recommendation:** Option A — Option B requires the checker to know the current branch/PR context, which introduces a tight CI-environment coupling and makes the script non-deterministic in local runs. The passive pass (AC-002) is sufficient for the technical gate; the `AGENTS.decisions.md` entry is enforced by convention and code review.

  > **[NEEDS CLARIFICATION — Q-2]** For the `upgrade` exception type, the issue proposal mentions "`spec.md` + `pr_context.md` + link to `artifacts/blueprint/upgrade/`". MUST this link be enforced by the checker as a required field in `pr_context.md`, or is it a recommended convention documented in `AGENTS.md`?
  >
  > **Options:**
  > - **A)** Convention only — documented in `AGENTS.md` under the upgrade exception type; not checked by `check_sdd_assets.py`. (Agent recommendation)
  > - **B)** Enforced — checker verifies that `pr_context.md` contains a reference to the `artifacts/blueprint/upgrade/` path when `SPEC_READY_EXCEPTION: upgrade` is set.
  >
  > **Agent recommendation:** Option A — the artifact link varies by upgrade (different slug, dates); enforcing a path pattern would create false positives. Convention + pr_context.md Validation Evidence section is sufficient.

## Explicit Exclusions
- Full SDD lifecycle for feature/enhancement change types: this work item does not modify the existing 10-artifact requirement for `SPEC_READY: true` specs. That path is unchanged.
- Automated `AGENTS.decisions.md` enforcement: verifying chore entries in `AGENTS.decisions.md` against live PR state is excluded (see Q-1 above).
- Consumer-repo AGENTS.md propagation: updating the consumer-repo AGENTS.md template with the new bypass track guidance is included (FR-007 covers the scaffold template; AGENTS.md consumer template propagation follows the normal bootstrap-template sync process).
