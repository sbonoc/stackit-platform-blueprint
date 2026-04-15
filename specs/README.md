# Specs Workspace

Use this directory for Spec-Driven Development work items.

## Canonical Layout

Create one folder per work item:

```text
specs/<YYYY-MM-DD>-<work-item-slug>/
  architecture.md
  spec.md
  plan.md
  tasks.md
  traceability.md
  graph.yaml
  evidence_manifest.json
  context_pack.md
  pr_context.md
  hardening_review.md
```

## How To Start

1. Pick the template pack:
   - Blueprint maintainer work: `.spec-kit/templates/blueprint/*`
   - Consumer delivery work: `.spec-kit/templates/consumer/*`
2. Copy templates into the new work-item folder.
3. Fill `Discover` and `High-Level Architecture` before implementation.
4. Keep `traceability.md` updated as code/tests/docs change.
5. Start implementation only when the readiness gate in `spec.md` has `SPEC_READY=true`.
6. Record the finalized architecture choice as an ADR using `.spec-kit/templates/<track>/adr.md`.
7. Run the `Document` phase before closing the work item by updating `docs/blueprint/**` and/or `docs/platform/**` as applicable.
8. Run the `Publish` phase by completing `hardening_review.md` and `pr_context.md` before opening a PR.

Reference baseline:
- `specs/2026-04-15-sdd-golden-example/` is a canonical template-expanded work item you can copy/adapt when starting new specs.

## Guardrails

- Capture security, observability, monitoring/alerting, reliability, and operability requirements in `spec.md`.
- Keep architecture and implementation aligned with SOLID, Clean Architecture/Clean Code, and DDD constraints from `AGENTS.md`.
- Use shift-left test automation and avoid duplicate test intent across layers.
- If requirements are incomplete, use `BLOCKED_MISSING_INPUTS` and keep `SPEC_READY=false`.
- Declare applicable `SDD-C-###` control IDs in the `Applicable Guardrail Controls` section of `spec.md`.
- Declare backend/frontend/test stack profiles and `Agent execution model` in the `Implementation Stack Profile` section of `spec.md`.
- Declare `Managed service preference` in `spec.md`; default is `stackit-managed-first` and any `explicit-consumer-exception` requires an explicit rationale.
- Declare local-first runtime fields in `spec.md`:
  - `Runtime profile`
  - `Local Kubernetes context policy`
  - `Local provisioning stack`
  - `Runtime identity baseline`
  - `Local-first exception rationale`
- Keep `plan.md` and `tasks.md` aligned with the app onboarding minimum target contract, including port-forward wrappers.
- Keep `graph.yaml`, `traceability.md`, and `spec.md` requirement/acceptance IDs synchronized.
- Use `[NEEDS CLARIFICATION: ...]` markers for unresolved requirements and keep `Open clarification markers count` at `0` before setting `SPEC_READY=true`.
- Keep blueprint-defect escalation lifecycle fields explicit when temporary consumer workarounds are required (`Upstream issue URL`, `Temporary workaround path`, `Replacement trigger`, `Workaround review date`).
- Complete repository-wide hardening review in `hardening_review.md` and keep proposals in a non-implemented section.
- In normative sections, avoid ambiguous wording (`should`, `may`, `could`, `might`, `either`, `and/or`, `as needed`, `approximately`, `etc.`).
