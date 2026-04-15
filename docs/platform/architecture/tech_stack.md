# Platform Technology Stack Baseline

This file declares the default stack profile expected by blueprint-generated consumers.

## Backend Profile
- Primary: `python_plus_fastapi_pydantic_v2`
- Also allowed by contract when explicitly selected in spec:
  - `go_plus_gin`
  - `kotlin_plus_ktor`

## Frontend Profile
- Vue latest stable
- Vue Router latest stable
- Pinia
- Onyx Design System

## Test Automation Profile
- Unit, integration, contract (Pact), and e2e are all required layers.
- Preferred frameworks:
  - `pytest`
  - `vitest`
  - `playwright`
  - `pact`

## Spec Annotation Requirement
Each work-item `spec.md` should declare:
- Backend stack profile
- Frontend stack profile
- Test automation profile
- Agent execution model

## Specialized Agent Guidance
When parallelizing implementation:
- Split ownership by bounded context and contract boundaries.
- Use isolated worktrees for concurrent specialist agents.
- Require validation evidence per ownership slice before integration.
