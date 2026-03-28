# Decisions Log

## Current Baseline
- `blueprint/contract.yaml` is the executable source of truth for repository behavior, ownership boundaries, and required automation.
- The pre-release template keeps a single current-state baseline. It does not carry release-note generation, upgrade automation, or compatibility machinery before the first published template release.
- Repository ownership is explicit:
  - this source repository is maintained as the blueprint
  - generated repositories replace consumer-owned root files on first init
  - blueprint-managed surfaces stay controlled and should change intentionally
- Generated repositories should optimize for project delivery work, not blueprint history.
  - Default work scope for human and AI contributors is `apps/**`, `docs/platform/**`, `make/platform*.mk`, `scripts/bin/platform/**`, and `scripts/lib/platform/**`.
  - Blueprint-managed paths are reference and tooling surfaces; consult them only when the task explicitly touches bootstrap, contract, validation, or inherited blueprint behavior.
  - Blueprint-maintainer test suites under `tests/blueprint/**` and `tests/docs/**` stay source-only and are pruned during first init.
- Optional modules use the simplest truthful execution model available:
  - provider-backed STACKIT foundation modules: `observability`, `opensearch`, `postgres`, `object-storage`, `rabbitmq`, `dns`, `secrets-manager`, `kms`
  - runtime/API modules: `workflows`, `langfuse`, `neo4j`, `public-endpoints`, `identity-aware-proxy`
  - generated repositories persist their chosen optional-module set in `blueprint/contract.yaml` during `make blueprint-init-repo`; later commands read that contract by default, and env flags act as explicit overrides
  - OpenSearch is a blueprint-owned platform capability target; OpenMetadata remains consumer/product-owned and is out of blueprint scope unless a future decision records otherwise
- Runtime dependency policy keeps pinned latest-stable versions, with one explicit vendor exception:
  - current multi-arch Bitnami images published under `bitnamilegacy/*` are allowed when the pinned tag is the supported stable line validated by this repo
- Quality gates are split by operator intent:
  - `make quality-hooks-fast` for default local and PR feedback
  - `make quality-hooks-strict` for slower audit lanes
  - `make quality-hooks-run` as the full composed gate
- Backlog entries represent open work only. Change history lives in Git; finished work does not stay in the backlog.
