# Architecture

## Context
- Work item: 2026-04-27-issue-217-template-descriptor-kustomization-sync
- Owner: blueprint maintainer
- Date: 2026-04-27

## Stack and Execution Model
- Backend stack profile: explicit-consumer-exception (blueprint Python tooling only)
- Frontend stack profile: not-applicable-stackit-runtime
- Test automation profile: explicit-consumer-exception (pytest blueprint tests)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: `template_smoke_assertions.py` does not cross-check that `apps/descriptor.yaml` and `infra/gitops/platform/base/apps/kustomization.yaml` in the generated temp repo reference the same manifest filenames. The membership check exists in `infra-validate` (via `verify_kustomization_membership`), but the Python smoke assertions step runs after `infra-validate` and does not produce its own human-readable message. Adding an explicit assertion in `template_smoke_assertions.py` makes drift visible without requiring the operator to inspect infra-validate stderr, and prevents future template edits from silently introducing the same regression.
- Scope boundaries: single-file change to `scripts/lib/blueprint/template_smoke_assertions.py`; one new unit test asserting template file consistency; no changes to consumer-facing APIs or make targets.
- Out of scope: changes to `validate_contract.py`, `app_descriptor.py`, consumer contract, or template file content.

## Bounded Contexts and Responsibilities
- Context A — template smoke assertions (`template_smoke_assertions.py`): responsible for verifying that the generated temp repo produced by the full `blueprint-init-repo → infra-bootstrap → infra-validate` chain satisfies expected structural invariants. Extended here to assert descriptor-kustomization filename agreement.
- Context B — descriptor and kustomization templates: the infra bootstrap kustomization template and the consumer init descriptor template are the source-of-truth for which manifest filenames are expected. The new assertion is a consistency check between these two sources after they are materialized in the generated repo.

## High-Level Component Design
- Domain layer: no change — domain logic lives in `app_descriptor.py` which already validates membership in consumer repos.
- Application layer: `template_smoke_assertions.py:main()` extended with an additional assertion block that reads the generated `apps/descriptor.yaml` (parsed with `yaml.safe_load`), extracts manifest filenames from each component's `manifests.deployment` and `manifests.service` paths using `Path(...).name`, and checks each against the already-computed `app_manifest_names` set (kustomization resources parsed earlier in the function).
- Infrastructure adapters: no new I/O patterns — the assertion reads files already within the generated temp repo `repo_root` argument.
- Presentation/API/workflow boundaries: `make blueprint-template-smoke` exit code is the only externally observable behavior change; it now fails with a named Python AssertionError instead of relying on `infra-validate` stderr alone.

## Integration and Dependency Edges
- Upstream dependencies: `yaml.safe_load` (already imported), `Path` (already imported), `app_manifest_names` list (already computed in the same function scope).
- Downstream dependencies: `make blueprint-template-smoke` → `make blueprint-upgrade-consumer-validate` → `make blueprint-upgrade-fresh-env-gate` (unchanged; the assertion only adds an earlier-stage failure path for drift that would already cause infra-validate to fail).
- Data/API/event contracts touched: none.

## Non-Functional Architecture Notes
- Security: assertion reads only the generated temp repo under `repo_root`; no network I/O, no subprocess calls, no path escapes possible given `yaml.safe_load` and `Path(rel_path).name` extraction.
- Observability: AssertionError messages include the descriptor path, kustomization path, and exact missing filename so CI logs are self-explanatory.
- Reliability and rollback: the assertion is additive; removing it reverts to the pre-patch behavior where infra-validate still catches the mismatch but with less readable output. Rollback is a one-line revert.
- Monitoring/alerting: no runtime monitoring changes; this is a CI-only assertion.

## Risks and Tradeoffs
- Risk 1: if `apps/descriptor.yaml` uses convention-default manifest paths (no explicit `manifests:` block), the assertion must handle the `None` manifests case and derive the convention default name `{component_id}-{kind}.yaml` as `app_descriptor.py` does — otherwise the assertion would incorrectly report drift for convention-default components. Mitigation: copy the same defaulting logic from `_resolve_manifest_path` when extracting filenames from the descriptor.
- Tradeoff 1: inline implementation (Option A) vs extracted helper (Option B). Option A is chosen because the assertion is smoke-specific; exporting it to `app_descriptor.py` would couple a generated-repo-scope check with the live-repo validation library.
