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
- ADR path: docs/blueprint/architecture/decisions/ADR-issue-165-semantic-annotations.md
- ADR status: approved

## Applicable Guardrail Controls (Normative)
- Applicable control IDs: SDD-C-001, SDD-C-002, SDD-C-003, SDD-C-004, SDD-C-005, SDD-C-006, SDD-C-007, SDD-C-008, SDD-C-009, SDD-C-010, SDD-C-011, SDD-C-012, SDD-C-013, SDD-C-014, SDD-C-015, SDD-C-016, SDD-C-017, SDD-C-018, SDD-C-019, SDD-C-020, SDD-C-021
- Control exception rationale: none

## Implementation Stack Profile (Normative)
- Backend stack profile: python_scripting_plus_bash (Python stdlib + subprocess; no web framework)
- Frontend stack profile: none
- Test automation profile: pytest
- Agent execution model: single-agent
- Managed service preference: explicit-consumer-exception
- Managed service exception rationale: Tooling-only Python script change; no managed service is provisioned or consumed by this work item.
- Runtime profile: local-first-docker-desktop-kubernetes
- Local Kubernetes context policy: docker-desktop-preferred
- Local provisioning stack: crossplane-plus-helm
- Runtime identity baseline: eso-plus-argocd-plus-keycloak
- Local-first exception rationale: This change adds Python scripting with no K8s, Crossplane, or runtime identity components. The local-first profile is declared for compliance; none of its runtime components are exercised by this work item.

## Objective
- Business outcome: `merge-required` upgrade plan entries tell consumers not only which file to merge, but what changed and what to verify in the merged result — so a developer applying an upgrade can confirm correctness without reading raw diffs or changelogs.
- Success metric: Every `merge-required` entry in the upgrade plan JSON and summary markdown includes a `semantic` annotation with a `kind`, a `description` of the change, and at least one actionable `verification_hint`; the annotation is auto-generated from the diff in all detectable cases and falls back to `structural-change` otherwise.

## Normative Requirements

### Functional Requirements (Normative)

- FR-001 The plan generation MUST produce a `semantic` annotation object on every `merge-required` entry in the upgrade plan. The annotation MUST contain: `kind` (a closed-set change category string), `description` (a human-readable summary of what changed), and `verification_hints` (a non-empty ordered list of actionable consumer checks).
- FR-002 The `kind` field MUST be assigned from the following closed set by static diff analysis of the baseline-to-source diff for the entry: `function-added`, `function-removed`, `variable-changed`, `source-directive-added`, `structural-change`. When no specific pattern matches, `kind` MUST be `structural-change`.
- FR-003 The static diff analysis MUST detect the following change patterns by comparing baseline content to upgrade source content using line-by-line and regex analysis (no file execution permitted): (a) `function-added` — a shell function definition present in source but absent in baseline; (b) `function-removed` — a shell function definition present in baseline but absent in source; (c) `variable-changed` — a shell variable assignment (`VAR=value`) whose value differs between baseline and source; (d) `source-directive-added` — a `source` or `.` directive present in source but absent in baseline.
- FR-004 When annotation generation for a single entry encounters an error (encoding exception, unexpected diff structure), that entry MUST receive `kind: structural-change` as a fallback annotation and plan generation MUST continue without aborting; the failure MUST be logged as a warning.
- FR-005 The `semantic` annotation MUST be serialized in `upgrade_plan.json` for each `merge-required` entry. The `upgrade_plan.schema.json` MUST be updated to declare the `semantic` property as an optional nested object on plan entries.
- FR-006 The `upgrade_summary.md` MUST render `semantic.description` and `semantic.verification_hints` for each `merge-required` entry in the merge-required section.
- FR-007 For entries with `planned_action = merge-required` in `upgrade_apply.json`, the apply result MUST carry the `semantic` annotation alongside the existing result fields. The `upgrade_apply.schema.json` MUST be updated to declare the optional `semantic` property on result items.

### Non-Functional Requirements (Normative)

- NFR-SEC-001 Annotation generation MUST NOT execute any content derived from blueprint or consumer files; diff analysis MUST use static line-by-line comparison and regex matching only. No subprocess calls with file content as arguments are permitted.
- NFR-OBS-001 Plan generation MUST log the count of `merge-required` entries processed, the count with a specific auto-generated `kind` (not `structural-change`), and the count assigned the `structural-change` fallback. No new metrics or distributed traces are required.
- NFR-REL-001 Annotation generation failures MUST be caught per-entry and result in a `structural-change` fallback; plan generation MUST remain non-blocking. The `semantic` field addition to both JSON artifacts MUST be backward-compatible: consumers that ignore unknown fields are unaffected.
- NFR-OPS-001 The `semantic` annotation MUST be readable directly from `upgrade_plan.json` and `upgrade_summary.md` without new CLI commands. The closed-set `kind` values MUST be documented in the generated reference docs to enable programmatic filtering.

## Normative Option Decision
- Option A: Implement annotation generation in a new standalone module `scripts/lib/blueprint/upgrade_semantic_annotator.py`; call it from `upgrade_consumer.py` at both `merge-required` entry creation sites; use static regex heuristics with a `structural-change` fallback.
- Option B: Require human-authored annotation metadata files stored alongside blueprint-managed files; load and surface them at plan generation time.
- Selected option: OPTION_A
- Rationale: Option A derives annotations from the actual diff with zero authoring overhead and is always consistent with the change; the dominant change patterns in shell scripts (function adds/removes, variable changes, source directives) are reliably detectable via regex. Option B requires discipline to maintain annotation files in sync with every blueprint change and introduces a new file contract with no clear enforcement mechanism.

## Contract Changes (Normative)
- Config/Env contract: none
- API contract: none
- Event contract: none
- Make/CLI contract: No new Make targets. `upgrade_plan.json` is extended with an optional `semantic` nested object on `merge-required` entries; `upgrade_apply.json` result items gain the same optional field. Field is absent on non-merge-required action types.
- Docs contract: `upgrade_plan.schema.json` and `upgrade_apply.schema.json` MUST be updated. `docs/blueprint/` upgrade reference docs MUST document the `semantic` annotation field, the closed set of `kind` values, and verification hint format.

## Blueprint Upstream Defect Escalation (Normative)
- Upstream issue URL: none (this is the blueprint fix itself)
- Temporary workaround path: none
- Replacement trigger: none
- Workaround review date: none

## Normative Acceptance Criteria

- AC-001 Given a `merge-required` entry for a file where a shell function was added in the blueprint source relative to baseline, `upgrade_plan.json` MUST include `semantic.kind = "function-added"`, `semantic.description` naming the function, and `semantic.verification_hints` with at least one hint confirming the function definition is present in the merged result.
- AC-002 Given a `merge-required` entry for a file where a variable assignment value changed, `upgrade_plan.json` MUST include `semantic.kind = "variable-changed"`, `semantic.description` naming the variable and its new value, and `semantic.verification_hints` confirming the correct value is present in the merged result.
- AC-003 Given a `merge-required` entry for a file where no detectable pattern is matched, `upgrade_plan.json` MUST include `semantic.kind = "structural-change"` and at least one `verification_hint` directing manual diff review.
- AC-004 Given an annotation generation error for one entry, plan generation MUST complete; the affected entry MUST carry `semantic.kind = "structural-change"` and no other plan entries MUST be affected.
- AC-005 `upgrade_plan.json` for a plan with at least one `merge-required` entry MUST validate against the updated `upgrade_plan.schema.json` and MUST include a fully populated `semantic` object on every such entry.
- AC-006 `upgrade_summary.md` MUST render `semantic.description` and the full `semantic.verification_hints` list for each `merge-required` entry.
- AC-007 `upgrade_apply.json` MUST include the `semantic` annotation on each result item whose `planned_action` is `merge-required`.

## Informative Notes (Non-Normative)
- Context: This is the companion to issue #162 (post-merge behavioral gate). #162 detects dropped function definitions after apply; this issue surfaces at plan time what will need verification. Together they close the consumer information gap at both ends: before merge (plan) and after merge (gate).
- Tradeoffs: Regex heuristics have known false negatives for complex diffs (e.g. large refactors, heredoc-embedded variable assignments). These are accepted at MVP — `structural-change` fallback remains actionable. Detection coverage can be extended in follow-up without changing the annotation contract.
- Clarifications: Only `merge-required` entries receive a `semantic` annotation. `create`, `update`, `skip`, and `conflict` entries are out of scope. Source-directive traversal (following sourced files to detect transitive changes) is out of scope; only the top-level file diff is analyzed.

## Explicit Exclusions
- Source-directive chain resolution beyond depth 0 (sourced files are not traversed for annotation generation).
- Non-merge-required action types: `create`, `update`, `skip`, `conflict`.
- Full POSIX shell parser.
- Non-shell file types at MVP (YAML, Makefile, Python — structural-change fallback applies).
- Semantic annotation rendering in the reconcile report and postcheck report (plan and summary only for MVP; apply result carries the annotation but does not re-render it).
