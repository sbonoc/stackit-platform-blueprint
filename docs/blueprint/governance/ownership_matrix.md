# Ownership Matrix

This matrix clarifies which areas are blueprint-managed and which are platform-owned.

| Area | Ownership | Edit Mode | Notes |
|---|---|---|---|
| `blueprint/contract.yaml` | Blueprint | Controlled | Canonical implementation contract. |
| `make/blueprint.generated.mk` | Blueprint | Generated | Re-render with `make blueprint-render-makefile`. |
| `scripts/bin/blueprint/**` | Blueprint | Controlled | Lifecycle/bootstrap/render/migration tooling. |
| `scripts/templates/blueprint/bootstrap/**` | Blueprint | Controlled | Template seeds for docs/make/hygiene and init metadata. |
| `scripts/templates/infra/bootstrap/**` | Blueprint | Controlled | Infra/dags/tests scaffolding templates. |
| `make/platform.mk`, `make/platform/*.mk` | Platform | Editable | Consumer-facing project targets. |
| `scripts/bin/platform/**`, `scripts/lib/platform/**` | Platform | Editable | Application/runtime-specific automation. |
| `docs/blueprint/**` | Blueprint | Template-synchronized | Governed by strict template sync policy. |
| `docs/platform/**` | Platform | Editable after seed | Seeded if missing by `make blueprint-bootstrap`. |

## Rule of Thumb
- If a path is template-generated or part of blueprint governance, change it intentionally and update docs/tests/contract in the same change.
- If a path is platform-owned, treat it as the solution layer for generated repositories.
