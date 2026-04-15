# Assistant Compatibility Contract

This blueprint supports multi-assistant execution as long as all assistants follow the same repository contracts.

## Canonical Tool-Agnostic Contract

Every assistant (Codex, Claude Code, Copilot, others) must treat these as authoritative:
- `AGENTS.md` governance and lifecycle order
- `blueprint/contract.yaml` executable contract
- `.spec-kit/**` template packs and control catalog
- `specs/**` work-item artifacts
- canonical Make/validation commands

## Skill Interoperability

- Codex skills under `.agents/skills/**` are optional accelerators.
- If an assistant cannot load Codex skills natively:
  - open the corresponding `SKILL.md`
  - use it as a plain-text runbook
  - execute the same repository commands and quality gates
- Skill availability must not change lifecycle gates, evidence requirements, or validation standards.

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
- Normative sections must avoid ambiguous language.
- Managed-service-first policy applies for `stackit-*` runtime capabilities unless an approved explicit exception is recorded.
- Any deviation from contract/gate policy is a blocking condition, not a warning.
