# Blueprint Architecture North Star

This document is the long-lived architecture reference for the blueprint itself.

## Intent
- Keep blueprint evolution deterministic, contract-driven, and maintainable.
- Provide one shared architecture baseline for business stakeholders, maintainers, and operators.

## Audience Views
- Business: predictable delivery with clear contract and upgrade behavior.
- Maintainers: strict ownership boundaries, drift checks, and template synchronization.
- Operators: deterministic runbooks, diagnostics artifacts, and rollback-aware workflows.

## Architecture Invariants
- `blueprint/contract.yaml` is the executable source of truth for behavior contracts.
- Dependency direction MUST follow Clean Architecture boundaries.
- DDD bounded contexts and ownership boundaries MUST remain explicit.
- Changes outside the active contract surface require a recorded decision.

## Decision and Traceability Rules
- Capture architecture options and decisions in ADRs under `docs/blueprint/architecture/decisions/`.
- Work-item specs under `specs/` MUST link to approved ADRs before implementation.
- Guardrail controls MUST be tracked through `.spec-kit/control-catalog.md` and work-item control IDs.

## Documentation Sync Contract
- Documentation updates are a mandatory lifecycle phase: `Document`.
- When behavior/contracts change, update both blueprint docs and consumer-facing docs.
- Required verification commands:
  - `make docs-build`
  - `make docs-smoke`
