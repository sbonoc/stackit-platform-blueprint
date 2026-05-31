# Ownership Matrix

This matrix clarifies which areas are blueprint-managed and which are platform-owned.

| Area | Ownership | Edit Mode | Notes |
|---|---|---|---|
| `blueprint/contract.yaml` | Blueprint | Controlled | Canonical implementation contract. |
| `make/blueprint.generated.mk` | Blueprint | Generated | Re-render with `make blueprint-render-makefile`. |
| `scripts/bin/blueprint/**` | Blueprint | Controlled | Lifecycle/bootstrap/render tooling. |
| `scripts/templates/blueprint/bootstrap/**` | Blueprint | Controlled | Template seeds for docs/make/hygiene and init metadata. |
| `scripts/templates/consumer/init/**` | Blueprint | Controlled | First-init consumer seeds for root docs/governance and CI. |
| `scripts/templates/infra/bootstrap/**` | Blueprint | Controlled | Infra/dags/tests scaffolding templates. |
| `README.md`, `AGENTS*.md`, `docs/README.md`, `.spec-kit/**`, `specs/**`, `.github/{CODEOWNERS,pull_request_template.md,ISSUE_TEMPLATE/**}`, `.github/workflows/ci.yml` | Consumer after first init | Editable | Source repo keeps blueprint-maintainer versions; generated repos get consumer-owned replacements during `make blueprint-init-repo`. |
| `blueprint/repo.init.env` | Consumer tracked | Editable, versioned | `make blueprint-init-repo` creates or refreshes non-sensitive defaults here, including required non-sensitive inputs for enabled optional modules. Init/placeholder/infra commands auto-load it when present. |
| `blueprint/repo.init.secrets.example.env` | Consumer tracked | Editable, placeholder-only | Tracked scaffold for sensitive inputs, including required sensitive placeholders for enabled optional modules. Copy to `blueprint/repo.init.secrets.env` before first live execution. |
| `blueprint/repo.init.secrets.env` | Consumer local | Editable, gitignored | Local sensitive overrides loaded after `blueprint/repo.init.env`; explicit shell env still wins. |
| `blueprint/contract.yaml`, `docs/docusaurus.config.js`, repo identity files under `infra/gitops/argocd/**`, STACKIT tfvars/backend files | Blueprint init-managed in generated repos | Controlled | `make blueprint-init-repo` owns these files. `make blueprint-bootstrap` and `make infra-bootstrap` validate presence but do not recreate them in generated repos. |
| `tests/blueprint/**`, `tests/docs/**` | Blueprint source only | Controlled | Maintainer-only blueprint contract and docs test suites; pruned from generated repos during first init. See **Test Directory Taxonomy** below. |
| `tests/infra/test_*.py` | Consumer tracked | Required seed | Consumer-runtime integration tests delivered via `spec.repository.required_files`. Must contain only consumer-runtime assertions. See **Test Directory Taxonomy** below. |
| `specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*`, `docs/blueprint/architecture/decisions/ADR-*.md` | Blueprint source only | Controlled | Maintainer-only SDD work-item history and blueprint ADR records; pruned from generated repos during first init. |
| `artifacts/c7/*.jsonl` | Blueprint source only | Controlled | Blueprint-run C7 audit trail (human SDD sessions on the blueprint itself); pruned from generated consumer repos during first init so consumers do not inherit upstream emission history. |
| `.github/actions/**` | Blueprint | Controlled | Shared local GitHub Actions support for source and generated-repo CI workflows. |
| `make/platform.mk`, `make/platform/*.mk` | Platform | Editable | Consumer-facing project targets. |
| `scripts/bin/platform/**`, `scripts/lib/platform/**` | Platform | Editable | Application/runtime-specific automation (for example `scripts/bin/platform/touchpoints/test_e2e.sh`). |
| `docs/blueprint/**` | Blueprint | Template-synchronized | Governed by strict template sync policy. |
| `docs/platform/**` | Platform | Editable after seed | Seeded if missing by `make blueprint-bootstrap`. |

## Test Directory Taxonomy (Normative)

A test file's correct home is determined by what it asserts against:

| Criterion | Directory | Delivered to consumers? |
|---|---|---|
| References `blueprint/modules/`, `scripts/lib/blueprint/`, or `scripts/bin/blueprint/` | `tests/blueprint/` | No (`source_only`) |
| Asserts against the consumer's running infrastructure (K8s, Argo, secrets, runtime identity) | `tests/infra/` | Yes (via `required_files`) |

**Rule:** A new `tests/infra/test_*.py` file that imports any symbol from `blueprint/modules/`, `scripts/lib/blueprint/`, or `scripts/bin/blueprint/` must be placed in `tests/blueprint/` instead and removed from `spec.repository.required_files` in `blueprint/contract.yaml`.

This rule is enforced automatically by `TestOwnershipContractTests.test_required_seed_files_contain_no_blueprint_module_refs` in `tests/blueprint/test_quality_contracts.py` (FR-005, issue #270).

## Rule of Thumb
- If a path is template-generated or part of blueprint governance, change it intentionally and update docs/tests/contract in the same change.
- If a path is platform-owned, treat it as the solution layer for generated repositories.

## Ownership Helper Commands
- Path lookup helper (CI triage-friendly):
  ```bash
  make blueprint-ownership-check OWNERSHIP_PATHS="scripts/bin/platform/touchpoints/test_e2e.sh"
  ```
- Machine-readable ownership metadata (`pattern -> owner`):
  ```bash
  make blueprint-ownership-metadata
  ```
