# Platform Architecture North Star

This document is the long-lived architecture reference for generated consumer repositories.

## Intent
- Keep platform delivery aligned with blueprint contracts while preserving consumer-owned implementation flexibility.
- Provide one shared architecture baseline for product, engineering, and operations.

## Audience Views
- Product and business: traceable requirements, deterministic readiness gate, clear delivery status.
- Engineering: bounded contexts, dependency direction, explicit contracts, and testability.
- Operations: observability-first runtime behavior, deterministic diagnostics, and runbook clarity.

## Platform Invariants
- Consumer-owned paths remain the primary implementation surface.
- Architecture choices MUST be recorded via ADRs in `docs/platform/architecture/decisions/`.
- Work-item specs MUST reference applicable `SDD-C-###` controls and approved ADRs before implementation.
- Documentation updates are mandatory in lifecycle phase `Document`.

## Architecture and Delivery Guidance
- Model features by bounded context and explicit integration boundaries.
- Keep Clean Architecture direction explicit across domain/application/infrastructure/presentation boundaries.
- Capture non-functional requirements (security, observability, reliability, operability) in normative spec sections.

## Required Documentation Validation
- `make docs-build`
- `make docs-smoke`
