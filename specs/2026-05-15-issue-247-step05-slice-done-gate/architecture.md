# Architecture

## Context
- Work item: 2026-05-15-issue-247-step05-slice-done-gate
- Owner: sbonoc
- Date: 2026-05-15

## Stack and Execution Model
- Backend stack profile: none
- Frontend stack profile: none
- Test automation profile: none
- Agent execution model: single-agent

## Problem Statement
- What needs to change and why: `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` defines the per-slice definition of done for all implementation work. It currently allows a slice to be declared done as soon as the unit test suite passes, with no gate on API response field completeness, Vue rendering branch coverage, Pact same-repo provider verification, or local smoke. A real delivery failure (six missing catalog fields visible in the browser) confirmed all four gaps. Three new guardrails and a promoted smoke gate close the gaps.
- Scope boundaries: `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` (guardrail section and main workflow section) and `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` (new file). No other files change.
- Out of scope: All other SDD step skill runbooks. `AGENTS.md`. `blueprint/contract.yaml`. Make targets. Any code or test changes.

## Bounded Contexts and Responsibilities
- Skill runbook governance layer: `.agents/skills/blueprint-sdd-step05-implement/SKILL.md` is the normative source of truth for step-05 per-slice definition of done. It is agent-consumed and human-reviewed. It does not execute code; it governs agent behavior at each slice boundary.
- Reference checklist layer: `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` is a short, checklist-format companion to SKILL.md. It is contract-governed (`blueprint/contract.yaml` required_files) and propagated to consumer repos. It provides a per-slice self-check artifact; its content MUST stay in sync with the guardrails in SKILL.md.

## High-Level Component Design
- Domain layer: governance rules (Guardrails #13–#15 and the smoke gate promotion) — define what constitutes a complete slice for HTTP and UI-rendering scope
- Application layer: SKILL.md "Workflow" section — the execution model that agents follow per-slice; "After All Slices Complete" section — the post-slice validation bundle
- Infrastructure adapters: none (docs only; no code)
- Presentation/API/workflow boundaries: the slice-done "Required Report Format" section in SKILL.md surfaces the gate results; the checklist in `references/implement_checklist.md` is the consumer-facing companion

## Integration and Dependency Edges
- Upstream dependencies: Issue #247 root-cause analysis confirming the four gaps; AGENTS.md `§ Minimum Validation Bundles by Change Type` (source of the smoke gate wording); AGENTS.md `§ Contract Testing Standards` (source of the Pact requirement); AGENTS.md `§ Testing and Quality Ratios` (source of the pyramid and branch-coverage expectation)
- Downstream dependencies: Consumer repos that receive `.agents/skills/blueprint-sdd-step05-implement/references/implement_checklist.md` via blueprint upgrade will see the updated checklist; no code behavior changes
- Data/API/event contracts touched: none

## Non-Functional Architecture Notes
- Security: none — docs-only change
- Observability: none — no operated code paths added
- Reliability and rollback: SKILL.md is version-controlled; rollback is `git revert`. The checklist file is new and its deletion restores the prior state. Consumer repos receive the checklist update on next blueprint upgrade; there is no runtime rollback surface.
- Monitoring/alerting: none

## Risks and Tradeoffs
- Risk 1: Guardrail prose changes its meaning on reword → mitigation: ADR records the decision rationale; spec ACs provide the normative reference for human review; Option B (automated content scanner) is available as a future safety net.
- Tradeoff 1: Raising the per-slice bar for HTTP and UI-rendering scope increases implementation effort per slice (field-coverage integration test, component branch enumeration, Pact consumer+provider in same slice). This is the intended consequence — the previous bar was demonstrably insufficient.

## Diagrams

No diagram required — this work item involves prose edits to two markdown files with no data flow, component topology, or lifecycle state machine that benefits from a visual representation.
