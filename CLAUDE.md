# Claude Code — Governance Delegation

Read `AGENTS.md` before starting any work. All lifecycle rules, SDD guardrails,
quality gates, ownership boundaries, and the sign-off policy are defined there
and apply to this assistant without exception.

SDD is enabled by default. Do not bypass the SDD lifecycle unless the user
explicitly says not to follow SDD for the current task.

When starting a new SDD work item, begin with `make spec-scaffold
SPEC_SLUG=<work-item-slug>` so work starts on a dedicated non-default branch.
Only skip branch creation when the user explicitly requests that opt-out.

For filter or payload-transform changes, require positive-path unit assertions
with matching fixture/request values; empty-result-only assertions are
insufficient. For HTTP route/query/filter/new-endpoint scope, require local
smoke via `make test-smoke-all-local` and capture pass/fail as test evidence
in `pr_context.md`.
Translate reproducible pre-PR smoke/deterministic-check failures into
failing automated tests first, then turn them green with the fix, or document
a deterministic exception rationale and follow-up owner in publish artifacts.

## Skills

Skill runbooks are in `.agents/skills/<name>/SKILL.md`. Apply them proactively
when the context matches. They are also available as slash commands:

| Slash command | Steps | Runbook | Actor |
|---|---|---|---|
| `/blueprint-consumer-ops` | — | `.agents/skills/blueprint-consumer-ops/SKILL.md` | Platform Engineer |
| `/blueprint-consumer-upgrade` | — | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` | Platform Engineer |
| `/blueprint-sdd-step01-intake` | 1–2 | `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` | Any stakeholder |
| `/blueprint-sdd-step03-resolve-questions` | 3 | `.agents/skills/blueprint-sdd-step03-resolve-questions/SKILL.md` | Any stakeholder |
| `/blueprint-sdd-step04-spec-complete` | 4 | `.agents/skills/blueprint-sdd-step04-spec-complete/SKILL.md` | Software Engineer · CTO / Architect |
| `/blueprint-sdd-step05-plan-slicer` | 5 (optional) | `.agents/skills/blueprint-sdd-step05-plan-slicer/SKILL.md` | Software Engineer |
| `/blueprint-sdd-step06-implement` | 6 | `.agents/skills/blueprint-sdd-step06-implement/SKILL.md` | Software Engineer |
| `/blueprint-sdd-step07-document-sync` | 7 | `.agents/skills/blueprint-sdd-step07-document-sync/SKILL.md` | Software Engineer |
| `/blueprint-sdd-step08-pr-packager` | 8–9 | `.agents/skills/blueprint-sdd-step08-pr-packager/SKILL.md` | Software Engineer |
| `/blueprint-sdd-traceability-keeper` | Cross-cutting | `.agents/skills/blueprint-sdd-traceability-keeper/SKILL.md` | Software Engineer |
