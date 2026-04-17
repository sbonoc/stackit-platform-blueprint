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

| Skill | Codex | Claude Code | Plain runbook |
|---|---|---|---|
| `blueprint-consumer-ops` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-consumer-upgrade` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-clarification-gate` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-document-sync` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-intake-decompose` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-plan-slicer` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-pr-packager` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |
| `blueprint-sdd-traceability-keeper` | `agents/openai.yaml` | `.claude/commands/` | `SKILL.md` |

## Recommended Cross-Assistant Workflow

1. Intake and decomposition:
   - run intake using `.spec-kit/templates/**` and `spec-scaffold`.
2. Clarification gate:
   - keep `SPEC_READY=false` until blockers are explicitly resolved.
3. Plan and implementation:
   - follow bounded-context slicing and dependency direction.
4. Verify and document:
   - run required quality/infra/docs checks.
5. Operate:
   - publish runbooks, diagnostics, and rollback guidance.

## Determinism Rules

- No assistant may fill missing requirements with assumptions during `Discover`, `High-Level Architecture`, `Specify`, or `Plan`.
- No assistant may bypass SDD unless the user explicitly asks to bypass it for the current task.
- No assistant should start a new SDD work item directly on the default branch; use `make spec-scaffold` branch creation or an equivalent dedicated-branch flow.
- For filter/payload-transform changes, assistants must require positive-path unit assertions (matching fixture/request values) and must reject empty-result-only evidence as sufficient.
- For work touching HTTP route handlers, query/filter logic, or new API endpoints, assistants must run local smoke with positive-path `curl` assertions and capture `Endpoint | Method | Auth | Result` evidence in `pr_context.md`.
- For reproducible pre-PR smoke/`curl`/deterministic-check failures, assistants must require a failing automated regression test first and a green result after the fix, or capture a deterministic exception rationale and follow-up owner in publish artifacts.
- Normative sections must avoid ambiguous language.
- Managed-service-first policy applies for `stackit-*` runtime capabilities unless an approved explicit exception is recorded.
- Any deviation from contract/gate policy is a blocking condition, not a warning.
