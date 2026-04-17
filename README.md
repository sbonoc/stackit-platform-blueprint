# STACKIT Platform Blueprint

Opinionated GitHub template for teams that want deterministic platform delivery with clear governance, managed-service-first runtime posture, and AI-assisted execution that remains auditable.

## Why This Blueprint
- Reduce setup/rework cost: bootstrap once, follow canonical contracts.
- Increase delivery predictability: Spec-Driven Development (SDD) with explicit readiness gates.
- Keep operations sane: deterministic Make targets, artifacted diagnostics, and runbook-aligned docs.
- Keep architecture intentional: DDD + Clean Architecture/Clean Code + SOLID guardrails adapted to stack.
- Keep adoption flexible: Codex skills are included, but the core workflow is tool-agnostic.

## What Is Opinionated
- Architecture direction:
  - strict dependency direction and bounded-context thinking
  - typed contracts and deterministic wrappers
- Delivery lifecycle:
  - `Discover -> High-Level Architecture -> Specify -> Plan -> Implement -> Verify -> Document -> Operate -> Publish`
- Runtime posture:
  - managed-service-first for `stackit-*` profiles
  - explicit approved exception required for non-managed alternatives
- Quality posture:
  - shift-left testing and pyramid governance
  - docs/contracts/tests kept in sync as part of Definition of Done

## Quick Start
1. Create repository from template and clone.
2. Initialize identity:
   ```bash
   make blueprint-init-repo-interactive
   ```
3. Bootstrap and validate:
   ```bash
   make blueprint-bootstrap
   make infra-bootstrap
   make infra-validate
   ```
4. Optional smoke:
   ```bash
   make infra-smoke
   ```

## Working Model (Consumer or Maintainer)
- SDD is default-required for assistant-executed work unless the user explicitly opts out for that task.
- Start each new SDD work item from `specs/**` using:
  - `make spec-scaffold SPEC_SLUG=<work-item-slug>`
  - default behavior creates and checks out a dedicated branch (`codex/<YYYY-MM-DD>-<slug>`)
  - explicit opt-out requires `SPEC_NO_BRANCH=true`
- Keep `SPEC_READY=false` until requirements and sign-offs are explicit.
- Run canonical validation before handoff/review:
  - `make quality-hooks-run`
  - `make infra-validate`

## AI Skills (Optional Accelerators)
- Install all bundled skills:
  - `make blueprint-install-codex-skills`
- Included skill families:
  - consumer operations and upgrade workflows
  - SDD intake/decomposition, clarification gate, plan slicing, traceability, and document-phase sync
- Skills accelerate execution, but governance remains contract-driven via `AGENTS.md`, `blueprint/contract.yaml`, `.spec-kit/**`, and Make targets.

## Multi-Agent Compatibility
- Works with Codex, Claude Code, Copilot, and others when they follow repository contracts.
- If an assistant cannot load Codex skills, use `SKILL.md` files as plain runbooks and execute the same commands.
- Compatibility guidance:
  - [docs/blueprint/governance/assistant_compatibility.md](docs/blueprint/governance/assistant_compatibility.md)

## Ownership Model
| Area | Edit Policy |
|---|---|
| `apps/**` | Project implementation |
| `docs/platform/**` | Project-facing docs |
| `make/platform.mk`, `make/platform/*.mk` | Platform-owned targets |
| `scripts/bin/platform/**`, `scripts/lib/platform/**` | Platform-owned implementation |
| `.github/actions/**` | Blueprint-managed shared CI support |
| `make/blueprint.generated.mk` | Generated, do not edit manually |
| `scripts/bin/blueprint/**`, `scripts/templates/**`, `blueprint/contract.yaml` | Blueprint-managed |

## Contributing
- Read governance first: [AGENTS.md](AGENTS.md)
- Keep backlog and decisions synchronized:
  - [AGENTS.backlog.md](AGENTS.backlog.md)
  - [AGENTS.decisions.md](AGENTS.decisions.md)
- Run quality and validation locally before requesting review:
  - `make quality-hooks-run`
  - `make infra-validate`

## Documentation Map
- Main docs index: [docs/README.md](docs/README.md)
- Consumer onboarding: [docs/platform/consumer/quickstart.md](docs/platform/consumer/quickstart.md)
- Blueprint governance: [docs/blueprint/governance/spec_driven_development.md](docs/blueprint/governance/spec_driven_development.md)
- SDD workspace guide: [specs/README.md](specs/README.md)
