# STACKIT Platform Blueprint

This repository is a GitHub template for bootstrapping platform repositories that need a clear contract, deterministic setup, and a path from local execution to STACKIT.

## What It Provides
- Repository identity initialization with `make blueprint-init-repo`
- Blueprint-managed bootstrap and validation with `make blueprint-bootstrap` and `make infra-validate`
- A clean ownership split between blueprint-managed surfaces and platform-owned implementation paths
- Lean optional modules that materialize only when enabled

## Who It Is For
- Platform teams starting a new repository with predictable structure and guardrails
- Teams that want local-first development with a clean path to managed STACKIT services

## Quickstart
1. Create a repository from GitHub **Use this template** and clone it.
2. Initialize repository identity:
   ```bash
   make blueprint-init-repo-interactive
   ```
   or
   ```bash
   set -a
   source blueprint/repo.init.example.env
   set +a
   make blueprint-init-repo
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

## Common Commands
- Discover commands: `make help`, `make infra-help-reference`
- Re-render blueprint-managed targets: `make blueprint-render-makefile`
- Reconcile optional-module scaffolding: `make infra-bootstrap`
- Run the end-to-end chain: `make infra-provision-deploy`
- Clean generated artifacts: `make blueprint-clean-generated`

## Docs
- Start here: [docs/README.md](docs/README.md)
- Consumer onboarding: [docs/platform/consumer/first_30_minutes.md](docs/platform/consumer/first_30_minutes.md)
- Quickstart: [docs/platform/consumer/quickstart.md](docs/platform/consumer/quickstart.md)
- Troubleshooting: [docs/platform/consumer/troubleshooting.md](docs/platform/consumer/troubleshooting.md)
- Blueprint maintenance: [docs/blueprint/README.md](docs/blueprint/README.md)
- Ownership boundaries: [docs/blueprint/governance/ownership_matrix.md](docs/blueprint/governance/ownership_matrix.md)
