# PR Context

## Summary
- Work item: 2026-05-22-sdd-toolchain-consistency
- Objective: Eliminate recurring `quality-sdd-check` failures caused by three classes of mismatch between skill runbooks/templates and what the check scripts actually enforce.
- Scope boundaries: Skill runbooks (step01, step02, step03), consumer-init seed templates, `.spec-kit/templates/` artifact templates, `AGENTS.backlog.md`. No check scripts, contract, AGENTS.md, or runtime code changed.

## Requirement Coverage
- Requirement IDs covered: REQ-001, REQ-002, REQ-003, REQ-004
- Acceptance criteria covered: AC-001, AC-002, AC-003, AC-004
- Contract surfaces changed: none — documentation and template fixes only.

## Key Reviewer Files
- Primary files to review first:
  - `.agents/skills/blueprint-sdd-step01-intake/SKILL.md` — new `## Bypass Track` section + clarification marker fixes
  - `.spec-kit/templates/blueprint/plan.md` — slice, app-onboarding-impact, risk placeholders
  - `.spec-kit/templates/blueprint/pr_context.md` — Deferred Proposals placeholder
- Supporting files:
  - `.agents/skills/blueprint-sdd-step02-resolve-questions/SKILL.md` — clarification marker fixes
  - `.agents/skills/blueprint-sdd-step03-spec-complete/SKILL.md` — bypass track guardrail #7
  - `scripts/templates/consumer/init/.agents/skills/blueprint-sdd-step01-intake/SKILL.md.tmpl` — mirror of step01 changes
  - `.spec-kit/templates/consumer/plan.md` and `pr_context.md` — same placeholder fixes as blueprint

## Validation Evidence
- Required commands executed:
  - `make quality-sdd-check SPEC_DIR=specs/2026-04-15-sdd-golden-example` — passed
  - `python3 -m pytest tests/blueprint/ -x -q` — 1061 passed
- Result summary: all existing tests pass; golden example check clean.
- Artifact references: none

## Risk and Rollback
- Main risks: very low — no runtime, infra, application, or check-script code changed. All changes are to documentation and markdown templates.
- Rollback strategy: revert the commit. Templates will revert to scaffold-and-immediately-fail behavior; bypass track will return to being invisible in step01.

## Deferred Proposals
- Proposal 1 (not implemented): Theme 2 — document undocumented check-script rules (pr_context.md inline fields, evidence_manifest.json schema, graph.json node schema, accessibility gate, P-001/P-002/P-003 tasks). Deferred — user explicitly chose no-op for Theme 2.
