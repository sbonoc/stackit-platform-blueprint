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

| Slash command | Runbook |
|---|---|
| `/blueprint-consumer-ops` | `.agents/skills/blueprint-consumer-ops/SKILL.md` |
| `/blueprint-consumer-upgrade` | `.agents/skills/blueprint-consumer-upgrade/SKILL.md` |
| `/blueprint-sdd-clarification-gate` | `.agents/skills/blueprint-sdd-clarification-gate/SKILL.md` |
| `/blueprint-sdd-document-sync` | `.agents/skills/blueprint-sdd-document-sync/SKILL.md` |
| `/blueprint-sdd-intake-decompose` | `.agents/skills/blueprint-sdd-intake-decompose/SKILL.md` |
| `/blueprint-sdd-plan-slicer` | `.agents/skills/blueprint-sdd-plan-slicer/SKILL.md` |
| `/blueprint-sdd-po-spec` | `.agents/skills/blueprint-sdd-po-spec/SKILL.md` |
| `/blueprint-sdd-pr-packager` | `.agents/skills/blueprint-sdd-pr-packager/SKILL.md` |
| `/blueprint-sdd-traceability-keeper` | `.agents/skills/blueprint-sdd-traceability-keeper/SKILL.md` |
