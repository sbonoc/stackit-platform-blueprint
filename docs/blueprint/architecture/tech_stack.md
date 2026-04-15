# Blueprint Technology Stack Baseline

This is the canonical technology baseline for blueprint-maintained paths.

## Backend and Runtime Baseline
- Allowed primary backend stacks:
  - `python_plus_fastapi_pydantic_v2`
  - `go_plus_gin`
  - `kotlin_plus_ktor`
- Runtime dependencies in operational paths MUST be pinned and latest-stable.

## Frontend Baseline
- Required frontend baseline:
  - Vue latest stable
  - Vue Router latest stable
  - Pinia
  - Onyx Design System

## Testing Baseline
- Required testing layers:
  - unit
  - integration
  - contract (Pact)
  - e2e
- Preferred frameworks:
  - `pytest`
  - `vitest`
  - `playwright`
  - `pact`

## Documentation and Architecture Tooling
- Documentation engine: Docusaurus.
- Architecture/workflow diagrams: Mermaid.
- Docs updates are mandatory in the `Document` lifecycle phase.

## Agent Execution Model Baseline
- Specialized agents should be used by bounded context (backend/frontend/ops).
- Parallel specialization should use isolated worktrees to avoid branch/worktree collisions.
- Each delegated slice MUST declare ownership and validation evidence.

## Change Control
- Any baseline change requires:
  - ADR update
  - contract alignment (`blueprint/contract.yaml`)
  - updated SDD templates and validation checks
