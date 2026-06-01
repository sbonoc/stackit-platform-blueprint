# Hardening Review

## Repository-Wide Findings Fixed

- Finding 1: **Naming inconsistency — hyphen vs. space form of `has-user-facing-flow`** (Gap 1, Medium).
  The checker originally looked up only `kv.get("has user-facing flow")` (space form, matching the template). All prose — AGENTS.md, step01 SKILL.md, spec FR text — uses the hyphen form `has-user-facing-flow`. An LLM following step01 instructions could write `- has-user-facing-flow: true` and silently bypass the gate. Fixed in `7ed22fb5` by adding a fallback lookup for the hyphen form in `_check_vgate_classification`; same fix applied to `e2e-gate-classification`. Two regression tests added.

- Finding 2: **FR-001 value list incomplete — N/A missing** (Gap 3, Low).
  The spec FR-001 listed only `automated | manual`, but the templates and governance doc already used N/A as a valid third value (default for non-user-facing work items). The behavior was correct; the spec text was inaccurate. Fixed in `7ed22fb5` by updating FR-001 to list all three values with N/A semantics.

- Finding 3: **Template comment missing "gate violation" language** (Gap 4, Low).
  The `E2E gate classification` inline comment said "only valid when has-user-facing-flow: false" but did not explicitly say "gate violation when has-user-facing-flow: true + playwright", as FR-006 requires. Fixed in `7ed22fb5`; both blueprint and consumer spec templates updated. Consumer init template synced.

- Finding 4: **architecture.md contained stale "spec-field triple" reference** (document-sync commit `a032366a`).
  The three-value classification design (`manual-with-target`) was rejected in Q-3 but the Problem Statement still said "spec-field triple". Fixed to "two new Implementation Stack Profile fields".

- Finding 5: **architecture.md had wrong return type annotation** (document-sync commit `a032366a`).
  Component design said `list[str]`; actual return type is `list[Violation]`. Fixed.

- Finding 6: **architecture.md Mermaid decision flowchart order did not match implementation** (document-sync commit `a032366a`).
  Diagram showed `has-user-facing-flow` check before playwright profile check; implementation checks playwright first. Absent-field violation paths were also missing. Diagram rewritten to match actual decision tree.

- Finding 7: **graph.json missing `NFR-OPS-001 → AC-014` edge** (document-sync commit `a032366a`).
  AC-014 directly tests the NFR-OPS-001 requirement (absent fields are violations, not silent defaults). Edge added.

## Observability and Diagnostics Changes

- New metric: `sdd_vgate_manual_e2e_violation` emitted to stderr on every V-gate classification violation.
  Format: `[METRIC] name=sdd_vgate_manual_e2e_violation value=1 work_item=<slug>`
  Emitted from all three violation branches: absent `has-user-facing-flow`, absent `E2E gate classification`, and non-`automated` classification.
  Mirrors the `sdd_step03_missing_spec_complete` pattern established in issue #352 (PR #355).
  Monitoring: metric can be scraped from CI stderr using the same tooling as #352 metrics. Dedicated sink tracking is deferred — see issue #356.

- Violation messages include: work item slug (in path), violating field name, current value, and expected value. Canonical format: `[quality-sdd-check] specs/<slug>/spec.md: V-gate violation — has-user-facing-flow=true + profile contains 'playwright', but 'E2E gate classification: manual'. Expected: 'automated'.`

## Architecture and Code Quality Compliance

- SOLID / Clean Architecture: `_check_vgate_classification` is a pure function (single responsibility, no side effects beyond metric emission). Wiring via `_validate_work_item_specs` follows the exact pattern of `_check_ac_format` (issue #352). No new module coupling introduced.
- Forward-only guard: `_VGATE_GATE_SINCE = "2026-06-01"` ensures no pre-existing spec is retroactively broken. Pattern mirrors `_SPEC_COMPLETE_GATE_SINCE` from #352.
- Test pyramid (post-implementation): unit 97.82% (113 files / 1799 tests), integration 1.63%, e2e 0.54% — ratios unchanged; 106 tests pass in targeted suite (10 new V-gate tests).
- No new technical debt: no `TODO`, no dead code, no `# type: ignore` annotations added.
- Documentation / diagram / CI / skill consistency: all four audiences updated — quality gate (`check_sdd_assets.py`), spec templates, governance docs (`AGENTS.md`, `spec_driven_development.md`, bootstrap mirror), skill runbooks (step01, step05). Bootstrap mirror sync confirmed via `sync_blueprint_template_docs.py`.

## Accessibility Gate (Normative — non-UI reviewers mark non-applicable items N/A)

- [ ] SC 4.1.2 (Name, Role, Value): N/A — no UI introduced
- [ ] SC 2.1.1 (Keyboard): N/A — no UI introduced
- [ ] SC 2.4.7 (Focus Visible): N/A — no UI introduced
- [ ] SC 1.4.1 (Use of Color): N/A — no UI introduced
- [ ] SC 3.3.1 (Error Identification): N/A — no UI introduced
- [ ] axe-core WCAG 2.1 AA scan evidence: N/A — no UI introduced

## Proposals Only (Not Implemented)

1. **Playwright test existence check**: Machine-verify that at least one `*.spec.ts` or similar Playwright test file exists on disk when `has-user-facing-flow: true`. Deferred because file-existence heuristics require knowing the naming convention per repo and risk false positives for repos that create tests in a separate work item. The current enforcement (classification field must be `automated`) covers the spec-level commitment; this proposal adds a second check at the file level.

2. **Cross-repo V-gate classification audit report**: Generate a report listing all work items across all consumer repos with their V-gate classification status. Deferred — belongs in a dedicated observability/reporting work item; requires aggregation infrastructure not in scope here.

3. **Frontend-stack-mismatch heuristic warning**: When `frontend-stack-profile` is non-`none` but `has-user-facing-flow: false`, emit a non-blocking stderr warning suggesting the author confirm the classification. Deferred because warning semantics require a separate UX surface; the intake inference (FR-009), template signal-list comment (FR-006), and frontend-stack cross-check (FR-009) address the primary risk.
