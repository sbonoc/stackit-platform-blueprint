# Implementation Plan

## Implementation Start Gate
- Implementation tasks MUST remain unchecked until `SPEC_READY=true`.
- If required inputs are missing, add `BLOCKED_MISSING_INPUTS` in `spec.md` and keep the gate closed.

## Constitution Gates (Pre-Implementation)
- Simplicity gate:
  - 20 markdown files following a fixed template; no abstractions, no helpers, no shared partials.
  - No runtime code introduced; reuse the existing `.agents/skills/` and `.agents/personas/` discovery mechanisms unchanged.
- Anti-abstraction gate:
  - Author content directly inside each `.md` file. Do not introduce a templating engine, persona-rendering script, or shared YAML fragment.
  - Tests live as direct pytest functions reading files with `pathlib.Path`, not as a custom validation framework.
- Integration-first testing gate:
  - For this content-only ticket the integration surface is "the orchestrator (Child B) can parse our files". The closest proxy here is: JSON-schema parsing of every `## Required Output Schema` block + YAML-front-matter parsing of every file. T-102 covers both.
- Positive-path filter/transform test gate:
  - N/A — no filter or payload-transform logic introduced.
- Finding-to-test translation gate:
  - Any reproducible pre-PR finding (e.g., persona file missing a DoD bullet) MUST be expressed as a failing pytest assertion in T-104 / T-105 first, then the persona file is edited until green.
  - If a deterministic automation path does not exist (e.g., subjective wording feedback from a human reviewer), record the exception rationale, owner, and follow-up trigger in `pr_context.md`.

## Delivery Slices
1. **Slice 1 — Persona scaffolding + template skeleton + reviewer non-overlap (red→green).** Write T-101 (file existence + count), T-105 (skill-path resolution + sign-off-role absence), and T-108 (persona template skeleton: 9 common section headings in exact order + non-empty content + reviewer-only `## Review Dimensions` + architecture-reviewer-only `## Cross-Context Impact Reporting`) as failing tests. Author the 6 implementer personas and the 4 reviewer personas to the minimum content that turns those tests green. Includes FR-001, FR-005, FR-006, FR-008, FR-011, FR-012, FR-017 partial coverage.
2. **Slice 2 — New skill runbooks + existing-skill `## Required Output Schema` backfill (red→green).** Write T-102 (front-matter + jsonschema parsing for the 10 new skills), T-103 (placeholder + secret scan over the 10 new files), and T-110 (front-matter + jsonschema parsing for the 8 existing skill files listed in FR-020) as failing tests. Author the 10 new skill `SKILL.md` files including the YAML jsonschema block, front-matter, and the FR-016 no-skill-invokes-skill discipline; then backfill the `## Required Output Schema` section + `blueprint-version` front-matter on each of the 8 existing skill `SKILL.md` files per FR-020 / T-007. Includes FR-002, FR-003, FR-005, FR-006, FR-008, FR-016, FR-020.
3. **Slice 3 — DoD specifics + reviewer dimensions + cross-context-impact template + reviewer heterogeneity documentation (red→green).** Write T-104 (DevSecOps and Tech Lead DoD phrases) and T-106 (reviewer-dimension non-overlap + architecture-reviewer Cross-Context Impact Reporting template + reviewer-model-heterogeneity statement + ADR-issue-337-reviewer-model-heterogeneity.md path citation in each of the 4 reviewer persona files). Author the affected persona files to turn those tests green. Includes FR-009, FR-010, FR-013, FR-014, FR-018.
4. **Slice 4 — Contract C8 enumeration + ADR + skill-invocation-by-skill ban + CLAUDE.md slash-command row (red→green).** Write T-107 (no skill→skill invocation directive), the C8 enumeration assertion in T-102, and T-109 (CLAUDE.md contains EXACTLY ONE new slash-command row for step08 and no other new-skill rows). Add 20 rows to `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c). Add the ADR `ADR-issue-360-factory-personas-skills-roster.md`. Add the `/blueprint-sdd-step08-agent-pr-review` row to `CLAUDE.md` § Skills table per FR-019 / T-006. Includes FR-004, FR-007, FR-015, FR-016, FR-019.
5. **Slice 5 — NFR documentation (red→green).** Add the persona→C7 `phase` declarations (NFR-OBS-001), the activation-trigger + stop-cleanup references (NFR-OPS-001), the reproducibility statement absence-of-randomness (NFR-REL-001). Re-run the full T-101…T-107 bundle to confirm everything stays green.

## Change Strategy
- Migration / rollout sequence: single PR ships all 20 files + the C8 enumeration + the ADR + the test bundle. No staged rollout; the surface is internal and consumer instances inherit on next blueprint upgrade.
- Backward compatibility policy: additive only. No existing persona file (none exist yet) is renamed or removed. No existing skill is modified.
- Rollback plan: `git revert <commit>`. Pure content; no migration state.

## Validation Strategy (Shift-Left)
- Unit checks: T-101 (file existence), T-102 (front-matter parse + jsonschema parse + C8 enumeration), T-103 (placeholder + secret scan), T-104 (DoD phrases), T-105 (skill-path resolution + sign-off-role absence), T-106 (reviewer-dimension non-overlap + architecture-reviewer template), T-107 (no skill→skill invocation directive).
- Contract checks: T-102 covers the contract surface: every new `SKILL.md`'s `## Required Output Schema` block parses as JSON Schema, and the C8 enumeration matches the 20 expected paths.
- Integration checks: none — no runtime.
- E2E checks: none — `has-user-facing-flow=false`, E2E classification N/A.

## App Onboarding Contract (Normative)
- Required minimum make targets:
  - `apps-bootstrap`
  - `apps-smoke`
  - `backend-test-unit`
  - `backend-test-integration`
  - `backend-test-contracts`
  - `backend-test-e2e`
  - `touchpoints-test-unit`
  - `touchpoints-test-integration`
  - `touchpoints-test-contracts`
  - `touchpoints-test-e2e`
  - `test-unit-all`
  - `test-integration-all`
  - `test-contracts-all`
  - `test-e2e-all-local`
  - `infra-port-forward-start`
  - `infra-port-forward-stop`
  - `infra-port-forward-cleanup`
- App onboarding impact: no-impact
- Notes: this work item adds no new Make targets and does not change any existing app-delivery Make target. SDD-C-015 does not apply.

## Documentation Plan (Document Phase)
- Blueprint docs updates:
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) — add 20 new rows (10 personas + 10 skills).
  - `docs/blueprint/architecture/decisions/ADR-issue-360-factory-personas-skills-roster.md` — new ADR (see `## Decision`).
- Consumer docs updates: none. The persona/skill files inherit automatically via existing C8 machinery; no consumer-facing how-to is changed by this ticket. (Consumer-facing how-to for invoking personas is owned by Child B once the orchestrator ships.)
- Mermaid diagrams updated: `architecture.md` ships the persona→skill flowchart. No other diagram is changed.
- Docs validation commands:
  - `make docs-build`
  - `make docs-smoke`

## Publish Preparation
- PR context file:
  - `pr_context.md`
- Hardening review file:
  - `hardening_review.md`
- Local smoke gate (HTTP route/filter changes):
  - N/A — no HTTP route, query/filter, or new API endpoint introduced. SDD-C-022 does not apply.
- Publish checklist:
  - include requirement/contract coverage
  - include key reviewer files
  - include validation evidence + rollback notes

## Operational Readiness
- Logging/metrics/traces: NFR-OBS-001 — every persona file declares the C7 `phase` enum value(s) its actions emit; every new `SKILL.md` declares the `phase` emitted on completion. The orchestrator (Child B) will read these declarations to emit C7 events at phase boundaries.
- Alerts/ownership: no new alert. The static surface emits no runtime signal; runtime ownership of the persona/skill execution lifecycle belongs to Child B.
- Runbook updates: none. The factory orchestrator runbook is authored by Child B.

## Risks and Mitigations
- Risk 1 — Persona content drifts from the FR phrases over time and the grep-based tests pass on outdated content. Mitigation: tests assert on exact phrases anchored to the FR text; any wording change requires a paired spec+test edit visible in the PR diff.
- Risk 2 — Child B's jsonschema validator turns out to need additional fields beyond what the `## Required Output Schema` blocks declare today. Mitigation: schemas use draft-07 conservatively and Child B can extend in one pass at validator-implementation time. OQ-2 keeps the door open for a retroactive uniform pass.
- Risk 3 — Reviewer dimensions ending up overlapping in subtle wording (e.g., "credentials" vs "secret material" across security-reviewer and contract-reviewer). Mitigation: T-106 enforces token-level non-overlap after case-folding and whitespace normalization; if false positives arise, refine the persona text to use canonical dimension names.
