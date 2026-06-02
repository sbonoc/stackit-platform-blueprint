# PR Context

## Summary

Authors the complete AI persona roster (6 implementer personas + 4 reviewer
personas) and 10 new SDD/factory skill SKILL.md runbooks that power the STACKIT
autonomous software factory's SDD execution (Child A of Epic #333). Each persona
and skill carries `blueprint-version`, `extensibility-tier: extensible`, and
`emits-phase` front-matter so consumers can shadow under the namespaced convention.
Contract C8 § Category (c) gains 20 enumeration rows (10 personas + 10 skills),
each `stable` + `extensible` + `#333`. CLAUDE.md Skills table gains one new row
for `/blueprint-sdd-step08-agent-pr-review`. The 8 pre-existing SDD step skill
SKILL.md files are retroactively backfilled with `## Required Output Schema`
Draft-07 JSON Schema blocks and `blueprint-version` front-matter. This is a
pure governance-doc and skill-runbook authoring work item — no runtime code,
no orchestrator service, no OpenHands client, no RabbitMQ/C7 emission machinery.

## Requirement Coverage

| Requirement | Implementation Path | Test Evidence |
|---|---|---|
| FR-001 — 10 persona files, correct split | `.agents/personas/` × 10 | T-101 |
| FR-002 — 10 new skill directories + SKILL.md | `.agents/skills/<name>/SKILL.md` × 10 | T-101 |
| FR-003 — Required Output Schema on each new SKILL.md | each new SKILL.md § Required Output Schema | T-102 |
| FR-004 — C8 § Category (c) 20 new rows | `docs/blueprint/autonomous-factory/design-contracts.md` | T-102 |
| FR-005 — extensibility-tier: extensible on all 20 | front-matter + C8 enumeration | T-102 |
| FR-006 — blueprint-version semver on all 20 | front-matter | T-102 |
| FR-007 — upstream-candidate convention documented | persona template + skill template preamble | T-102 |
| FR-008 — no placeholder tokens on any of 20 files | each of the 20 new files | T-103 |
| FR-009 — devsecops-qa DoD mandates PII/non-root/hardening | `.agents/personas/devsecops-qa.md` § DoD | T-104 |
| FR-010 — tech-lead DoD mandates triage-first + decompose + boundary + max fan-out | `.agents/personas/tech-lead.md` § DoD | T-104 |
| FR-011 — every Skills Invoked reference resolves | each persona § Skills Invoked | T-105 |
| FR-012 — no persona claims sign-off authority | each persona | T-105 |
| FR-013 — reviewer dimensions non-overlapping | 4 reviewer persona files | T-106 |
| FR-014 — architecture-reviewer Cross-Context Impact Reporting template | `.agents/personas/architecture-reviewer.md` | T-106 |
| FR-015 — blueprint-ticket-triage-size documents classification + output | `.agents/skills/blueprint-ticket-triage-size/SKILL.md` | T-102 |
| FR-016 — no SKILL.md directive-invokes another skill | each new SKILL.md § Guardrails | T-107 |
| FR-017 — all 9 common sections in order in each persona | each of the 10 persona files | T-108 |
| FR-018 — reviewer-model-heterogeneity convention in each reviewer persona | 4 reviewer personas § Strict Guardrails | T-106 |
| FR-019 — exactly one CLAUDE.md slash-command row for step08 | `CLAUDE.md` | T-109 |
| FR-020 — Required Output Schema backfill on 8 existing SDD skills | 8 existing SKILL.md files | T-110 |
| NFR-SEC-001 — no secrets/PII in new files | each of the 20 new files | T-103 |
| NFR-OBS-001 — C7 phase enum declared in each persona/skill | SDD Cycle Stakes + emits-phase | T-101 |
| NFR-REL-001 — deterministic skill invocation order | § Skills Invoked numbered lists | T-105 |
| NFR-OPS-001 — Activation Triggers + stop-cleanup reference | each persona § Activation Triggers + Collaboration & Handoffs | T-101 |
| NFR-A11Y-001 — N/A (no UI) | — | T-A01 (N/A) |
| AC-001…AC-017 | see traceability.md | T-101…T-110 |

## Key Reviewer Files

- Primary files to review first:
  - `specs/2026-06-02-issue-360-factory-personas-skills/spec.md` — full requirement set (FR-001…FR-020, AC-001…AC-017)
  - `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) — 20 new enumeration rows
  - `.agents/personas/architecture-reviewer.md` — Cross-Context Impact Reporting template + heterogeneity guardrail

| File | Why reviewer-relevant |
|---|---|
| `.agents/personas/architecture-reviewer.md` | Contains `## Cross-Context Impact Reporting` template that the human merge reviewer pastes into the PR body (FR-014); also carries the reviewer-model-heterogeneity guardrail (FR-018/AC-015) |
| `.agents/personas/tech-lead.md` | DoD expanded to satisfy FR-010's 4 mandatory items; verifying bullet ordering matters (T-104 asserts exact token presence) |
| `.agents/personas/devsecops-qa.md` | DoD must carry the 3 FR-009 mandatory items including the PII exclusion and hardening_review.md clean-gate bullet (T-104) |
| `.agents/skills/blueprint-ticket-triage-size/SKILL.md` | FR-015 contract: must document classification enum, bounded-context output field, and next-step naming; also feeds the #338 data feed |
| `.agents/skills/blueprint-sdd-step08-agent-pr-review/SKILL.md` | The one new skill with a slash-command row; carries FR-015a structural sections (Guardrails, Workflow, Required Report Format) verified by `check_sdd_assets.py` |
| `docs/blueprint/autonomous-factory/design-contracts.md` § Contract C8 § Category (c) | 20 new enumeration rows; verify each carries `stable` + `extensible` + `#333` and the consumer-shadow phrasing (T-102 parametrized) |
| `CLAUDE.md` § Skills | Exactly one new row added for `/blueprint-sdd-step08-agent-pr-review`; no other new-skill rows permitted (T-109) |
| `tests/blueprint/personas_skills/test_contracts_schemas_frontmatter.py` | Contains AC-004 parametrized assertions over all 20 C8 paths — most comprehensive single test file |
| `tests/blueprint/personas_skills/test_reviewer_personas.py` | Contains AC-011/AC-012/AC-015 — non-overlap + heterogeneity convention assertions across all 4 reviewer personas |
| `.agents/skills/blueprint-sdd-step02-resolve-questions/SKILL.md` | YAML description field quoted to fix parse error discovered during blueprint-version backfill (Slice 2) |

## Cross-Context Impact Reporting

- Bounded contexts touched: `autonomous-factory` (personas + skills surface, C8 enumeration, ADR); `developer-experience` (CLAUDE.md Skills table)
- Downstream consumers impacted: any consumer repo that shadows personas/skills under `.agents/personas/consumer/` or `.agents/skills/consumer/` — the 20 new paths become available to shadow
- Contract-surface deltas: `docs/blueprint/autonomous-factory/design-contracts.md` § C8 § Category (c) gains 20 `stable` + `extensible` rows; `CLAUDE.md` Skills table gains 1 row for `/blueprint-sdd-step08-agent-pr-review`; 8 existing SDD SKILL.md files gain `## Required Output Schema` + `blueprint-version` (additive-only, no removals)
- Rollback risk: zero migration state. `git revert <commit>` is sufficient for any commit on this branch. No schema changes, no database migrations, no runtime config changes.

## Validation Evidence

```
make quality-sdd-check
  → [quality-sdd-check] validated SDD assets, readiness gates, and language policy  PASS

make quality-hardening-review
  → [METRIC] name=quality_hardening_review_total value=1 status=success  PASS

uv run python3 -m pytest tests/blueprint/personas_skills/ -q
  → 589 passed in 0.38s  PASS

uv run python3 -m pytest tests/blueprint/ -q
  → 1769 passed in 141.90s  PASS
  (one drift failure fixed: bootstrap template mirror re-synced in commit e85db47d)

make docs-build
  → [INFO] docs build complete  PASS

make docs-smoke
  → [METRIC] name=script_duration_seconds value=0 script=docs_smoke status=success  PASS

make quality-docs-sync-all
  → summary: quality-docs-sync-module-contract-summaries (created=0 updated=0 removed=0 skipped=30)  PASS

make quality-docs-check-changed
  → [docs-orchestrator] no matching steps selected; nothing to do  PASS
  → [test-pyramid] ratios unit=97.96% (min>60.00%) integration=1.53% (max<=30.00%) e2e=0.51% (max<=10.00%)  OK

Traceability: 42/42 graph↔spec nodes, 0 orphan requirements, 0 orphan test files
```

## Risk and Rollback

- Rollback strategy: pure content commits on `.md` files only. `git revert <commit>` is sufficient for any commit on this branch. No database migration, no schema change, no consumer-instance state, no runtime config change.
- Blast radius: the 20 new files under `.agents/personas/` and `.agents/skills/` and the 8 backfilled SKILL.md files are read by Claude Code locally and (when Child B `#361` merges) by the orchestrator. Reverting removes the persona/skill surface entirely — the factory falls back to the pre-#360 state with no personas or new skills.
- Feature flag: none needed — pure static doc files, no runtime toggle.
- Child B dependency: the orchestrator (`#361`) reads these persona/skill files at runtime. This PR ships the file surface only; runtime enforcement of reviewer-model-heterogeneity and skill-composition rules is owned by Child B and is out of scope.

## Deferred Proposals

None. Both pre-planned scope exclusions (OQ-1 and OQ-2) were resolved on 2026-06-02
and pulled into scope as FR-019/FR-020. Both are fully implemented in this PR.
