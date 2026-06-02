# Tasks

## Gate Checks (Required Before Implementation)
- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`
- [ ] G-002 Confirm open questions and unresolved alternatives are `0`
- [ ] G-003 Confirm required sign-offs are approved
- [ ] G-004 Confirm `Applicable Guardrail Controls` section includes `SDD-C-###` IDs
- [ ] G-005 Confirm `Implementation Stack Profile` section is fully populated

## Implementation
- [ ] T-001 Author the 6 implementer persona files under `.agents/personas/<name>.md` (`po-analyst`, `architect`, `tech-lead`, `implementer`, `devsecops-qa`, `doc-keeper`) per the persona template contract and FR-001 / FR-005 / FR-006 / FR-007 / FR-008 / FR-009 / FR-010 / FR-011 / FR-012
- [ ] T-002 Author the 4 reviewer persona files under `.agents/personas/<name>.md` (`security-reviewer`, `architecture-reviewer`, `contract-reviewer`, `test-coverage-reviewer`) including non-overlapping `## Review Dimensions` (FR-013) and the architecture-reviewer's `## Cross-Context Impact Reporting` template (FR-014)
- [ ] T-003 Author the 10 new skill directories with `SKILL.md` runbooks under `.agents/skills/<skill-name>/` per FR-002 / FR-003 / FR-005 / FR-006 / FR-008 / FR-015 / FR-016
- [ ] T-004 Update `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) — add 20 new rows (10 personas + 10 skills), each `stable` + `extensible`, owning ticket `#333` (FR-004)
- [ ] T-005 Update consumer-facing docs/diagrams when contracts/behavior change — N/A for this child (no consumer-facing how-to changes; inheritance is via existing C8 machinery)
- [ ] T-006 Add EXACTLY ONE row to `CLAUDE.md` § Skills slash-command table for `/blueprint-sdd-step08-agent-pr-review` per FR-019 (Actor: `Software Engineer`; runbook path: `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md`). MUST NOT add any other rows.
- [ ] T-007 Backfill `## Required Output Schema` section containing EXACTLY ONE fenced ```yaml jsonschema``` block on each of the 8 existing SDD skill `SKILL.md` files listed in FR-020; add `blueprint-version` front-matter where missing

## Test Automation
- [ ] T-101 Add `tests/blueprint/personas_skills/test_roster_exists.py` covering AC-001 (10 personas with correct names) + AC-002 (10 new skill directories each with SKILL.md)
- [ ] T-102 Add `tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py` covering AC-003 (each new SKILL.md has `## Required Output Schema` with exactly one yaml jsonschema block parsing as valid JSON Schema), AC-004 (Contract C8 enumeration row present for each of the 20 paths with `stable` + `extensible`), AC-005 (`blueprint-version` semver front-matter on all 20 files)
- [ ] T-103 Add `tests/blueprint/personas_skills/test_no_placeholders_no_secrets.py` covering AC-006 (no placeholder tokens + zero baseline secret-pattern matches across the 20 new files)
- [ ] T-104 Add `tests/blueprint/personas_skills/test_dod_phrases.py` covering AC-007 (DevSecOps/QA DoD three mandated items) + AC-008 (Tech Lead DoD four mandated items)
- [ ] T-105 Add `tests/blueprint/personas_skills/test_persona_invocation_safety.py` covering AC-009 (every `## Skills Invoked` reference resolves) + AC-010 (no persona claims human sign-off role)
- [ ] T-106 Add `tests/blueprint/personas_skills/test_reviewer_personas.py` covering AC-011 (reviewer-dimension non-overlap), AC-012 (architecture-reviewer Cross-Context Impact Reporting template fields present), and AC-015 (each of the 4 reviewer persona files contains the reviewer-model-heterogeneity statement AND cites `ADR-issue-337-reviewer-model-heterogeneity.md` by path)
- [ ] T-107 Add `tests/blueprint/personas_skills/test_no_skill_invokes_skill.py` covering AC-013 (no new SKILL.md directive-invokes another skill)
- [ ] T-108 Add `tests/blueprint/personas_skills/test_persona_template_structure.py` covering AC-014 — assert each of the 10 persona files contains the 9 common section headings from FR-017 in EXACTLY the specified order, the 4 reviewer persona files additionally contain `## Review Dimensions`, `.agents/personas/architecture-reviewer.md` additionally contains `## Cross-Context Impact Reporting`, and each required section has at least one non-blank line of content between its heading and the next heading
- [ ] T-109 Add `tests/blueprint/personas_skills/test_claude_md_slash_command_row.py` covering AC-016 — assert `CLAUDE.md` contains EXACTLY ONE table row whose slash-command cell is `` `/blueprint-sdd-step08-agent-pr-review` `` and whose runbook-path cell is `` `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md` ``, AND no other row references any of the 9 other new skill names from FR-002
- [ ] T-110 Add `tests/blueprint/personas_skills/test_existing_skills_output_schema_backfill.py` covering AC-017 — assert each of the 8 existing skill `SKILL.md` files from FR-020 contains EXACTLY ONE `## Required Output Schema` heading followed by EXACTLY ONE fenced ```yaml jsonschema``` block parsing as valid JSON Schema (draft-07 or later) AND each file's YAML front-matter contains a `blueprint-version` key matching the semver pattern

## Accessibility Testing (Normative — mark N/A with rationale for non-UI specs)
- [ ] T-A01 N/A — NFR-A11Y-001 declared N/A in `spec.md`; this work item ships no UI surface (governance docs + persona/skill markdown files only). No axe-core scan, no keyboard operability test, no focus-indicator test, no programmatic-label test.

## Validation and Release Readiness
- [ ] T-201 Run `make quality-sdd-check` and `uv run python3 -m pytest tests/blueprint/personas_skills/` and capture results in `traceability.md`
- [ ] T-202 Attach evidence (test output, file listings) to `traceability.md`
- [ ] T-203 Confirm no stale TODOs / dead code / drift; in particular verify FR-008 holds across all 20 new files
- [ ] T-204 Run documentation validation (`make docs-build` and `make docs-smoke`)
- [ ] T-205 Run hardening review validation bundle (`make quality-hardening-review`) and ensure `hardening_review.md` is clean before handoff

## Publish
- [ ] P-001 Update `hardening_review.md` with repository-wide findings fixed and proposals-only section
- [ ] P-002 Update `pr_context.md` with requirement/contract coverage, key reviewer files, validation evidence, and rollback notes
- [ ] P-003 Ensure PR description follows repository template headings and references `pr_context.md`

## App Onboarding Minimum Targets (Normative)
- [ ] A-001 N/A — `apps-bootstrap` and `apps-smoke` are not affected by this work item; declared `App onboarding impact: no-impact` in `plan.md`
- [ ] A-002 N/A — backend app lanes `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are unaffected
- [ ] A-003 N/A — frontend app lanes `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are unaffected
- [ ] A-004 N/A — aggregate gates `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are unaffected
- [ ] A-005 N/A — port-forward operational wrappers `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are unaffected
