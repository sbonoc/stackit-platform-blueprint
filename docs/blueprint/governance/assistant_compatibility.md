# Assistant Compatibility Contract

This blueprint supports multi-assistant execution as long as all assistants follow the same repository contracts.

## Canonical Tool-Agnostic Contract

Every assistant (Codex, Claude Code, Copilot, others) must treat these as authoritative:
- `AGENTS.md` governance and lifecycle order
- `blueprint/contract.yaml` executable contract
- `.spec-kit/**` template packs and control catalog
- `specs/**` work-item artifacts
- canonical Make/validation commands
- default SDD behavior: enabled unless the user explicitly opts out
- default work-item branching: `make spec-scaffold` creates a dedicated non-default branch unless explicit opt-out is requested

## Assistant Integration

### Codex

- Reads `AGENTS.md` natively.
- Skills are loaded from `.agents/skills/**` via `agents/openai.yaml` wiring files.
- Skills can be invoked by slash command or natural language.

### Claude Code

- Reads `CLAUDE.md` at startup, which delegates to `AGENTS.md`.
- Skills are invoked via slash commands defined in `.claude/commands/`.
- Each `.claude/commands/<skill-name>.md` file reads and executes the corresponding `.agents/skills/<skill-name>/SKILL.md` runbook.
- Supports both argument mode (`/skill-name <input>`) and conversational mode (no argument — Claude asks).
- Branch naming violations are caught locally via the `quality-validate-branch` pre-push hook
  (`python3 scripts/bin/blueprint/validate_contract.py --branch-only`) before reaching CI.

### Other assistants

- If an assistant cannot load skills natively, open the corresponding `SKILL.md` and use it as a plain-text runbook.
- Execute the same repository commands and quality gates regardless of assistant.
- Skill availability must not change lifecycle gates, evidence requirements, or validation standards.

## Skill Interoperability

| Skill | Steps | Codex | Claude Code | Plain runbook |
|---|---|---|---|---|
| `blueprint-consumer-ops` | — | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-consumer-upgrade` | — | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step01-intake` | 0 + 1–2 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step02-resolve-questions` | 0 + 3 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step03-spec-complete` | 4 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step04-plan-slicer` | 5 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step05-implement` | 6 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step06-document-sync` | 7 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-step07-pr-packager` | 8–9 | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-traceability-keeper` | cross-cutting | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |

Retired skills (no longer present): `blueprint-sdd-clarification-gate`, `blueprint-sdd-document-sync`,
`blueprint-sdd-intake-decompose`, `blueprint-sdd-plan-slicer`, `blueprint-sdd-pr-packager`,
`blueprint-sdd-po-spec`. Their responsibilities are covered by the step-numbered skills above.

## Recommended Cross-Assistant Workflow

1. Intake (`step01-intake`) — any stakeholder:
   - auto-scaffold if the spec directory does not exist (`make spec-scaffold SPEC_SLUG=<slug>`).
   - open a Draft PR; all spec artifacts are committed before PR opens.
   - use `[NEEDS CLARIFICATION: ...]` blocks for any unresolved inputs.
2. Resolve questions (`step02-resolve-questions`) — any stakeholder:
   - PR comment is the universal answer channel; works regardless of assistant.
   - `SPEC_PRODUCT_READY: approved` in a PR comment is the deterministic Product sign-off phrase.
   - keep `SPEC_READY=false` until all blockers are explicitly resolved.
3. Spec complete (`step03-spec-complete`) — Software Engineer / Architect:
   - Architecture, Security, and Operations sign-offs; set `SPEC_READY=true`.
4. Plan (`step04-plan-slicer`) — Software Engineer (optional):
   - refine implementation slices; skip for straightforward work items.
5. Implement (`step05-implement`) — Software Engineer:
   - read `Implementation Stack Profile` from `spec.md`; use canonical Make targets.
   - TDD: write failing tests first, then implementation.
6. Document and Operate (`step06-document-sync`) — Software Engineer:
   - run `make quality-docs-sync-all` and `make docs-build`; fill hardening review.
7. Publish (`step07-pr-packager`) — Software Engineer:
   - fill `pr_context.md` and `hardening_review.md`; file deferred-proposal GitHub issues.
   - run quality gates; mark Draft PR ready; post `@codex review this PR`.

## Determinism Rules

- No assistant may fill missing requirements with assumptions during `Discover`, `High-Level Architecture`, `Specify`, or `Plan`.
- No assistant may bypass SDD unless the user explicitly asks to bypass it for the current task.
- No assistant should start a new SDD work item directly on the default branch; use `make spec-scaffold` branch creation or an equivalent dedicated-branch flow.
- For filter/payload-transform changes, assistants must require positive-path unit assertions (matching fixture/request values) and must reject empty-result-only evidence as sufficient.
- For work touching HTTP route handlers, query/filter logic, or new API endpoints, assistants must run local smoke via `make test-smoke-all-local` with positive-path assertions and capture `Endpoint | Method | Auth | Result` evidence in `pr_context.md`.
- For reproducible pre-PR smoke/`curl`/deterministic-check failures, assistants must require a failing automated regression test first and a green result after the fix, or capture a deterministic exception rationale and follow-up owner in publish artifacts.
- Normative sections must avoid ambiguous language.
- Managed-service-first policy applies for `stackit-*` runtime capabilities unless an approved explicit exception is recorded.
- Any deviation from contract/gate policy is a blocking condition, not a warning.
