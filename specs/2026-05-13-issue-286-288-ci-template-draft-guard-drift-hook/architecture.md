# Architecture

## Context
- Work item: issue-286-288-ci-template-draft-guard-drift-hook
- Owner: sbonoc
- Date: 2026-05-13

## Stack and Execution Model
- Backend stack profile: python_plus_fastapi_pydantic_v2 (validate_contract.py CLI extension)
- Frontend stack profile: none
- Test automation profile: pytest (blueprint contract tests)
- Agent execution model: specialized-subagents-isolated-worktrees

## Problem Statement
- What needs to change and why: (1) `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` lacks the `types: [opened, synchronize, reopened, ready_for_review]` filter and job-level draft guard that blueprint's own `ci.yml` has since commit `dd4e3f9e` (v1.10.0), causing new and upgraded consumer repos to run CI on every draft PR push. (2) `validate_bootstrap_template_sync` runs inside `infra-validate`, which is path-gated by `_QG_INFRA_GATE_PATHS`; root dotfiles don't match any gate prefix, so local changes to tracked managed files silently skip the drift check — CI catches it but local feedback is absent.
- Scope boundaries: Blueprint tooling and templates only. No application runtime, no STACKIT managed services, no Kubernetes provisioning, no frontend.
- Out of scope: Updating existing consumer repos directly; modifying `_QG_INFRA_GATE_PATHS` to add root dotfiles to the infra gate (separate concern); adding `quality-validate-bootstrap-template-drift` to `blueprint/contract.yaml` required_targets.

## Bounded Contexts and Responsibilities
- Context A — Consumer init template: `scripts/templates/consumer/init/` is the source of truth for new-consumer CI workflows. Changes here propagate to new consumers at init time and to existing consumers on next blueprint upgrade.
- Context B — Blueprint tooling and quality hooks: `scripts/bin/blueprint/validate_contract.py`, `make/blueprint.generated.mk.tmpl`, `.pre-commit-config.yaml`, and `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` define the quality gate infrastructure used by both the blueprint source repo and (via managed-file sync) consumer repos.

## High-Level Component Design
- Domain layer: Blueprint contract schema (`contract_schema.py`) and `_validate_bootstrap_template_sync` function — unchanged; exposed via new `--bootstrap-drift-only` flag.
- Application layer: `validate_contract.py` CLI — new fast path flag analogous to `--branch-only`.
- Infrastructure adapters: Make target `quality-validate-bootstrap-template-drift` in `make/blueprint.generated.mk.tmpl` — invokes the CLI fast path.
- Presentation/API/workflow boundaries: pre-commit hook in `.pre-commit-config.yaml` and its bootstrap template mirror — surfaces drift at commit time.

## Integration and Dependency Edges
- Upstream dependencies: `scripts/lib/blueprint/contract_validators/docs_sync.py::validate_bootstrap_template_sync` — existing function, consumed by the new flag path.
- Downstream dependencies: None — the new Make target and pre-commit hook are leaf consumers.
- Data/API/event contracts touched: Make/CLI contract — new `quality-validate-bootstrap-template-drift` target and `--bootstrap-drift-only` flag.

## Non-Functional Architecture Notes
- Security: Hook entry is `make quality-validate-bootstrap-template-drift` (system language); no shell injection surface, no credential access, no remote network calls.
- Observability: Pre-commit stdout/stderr provides immediate developer feedback; no structured logging added.
- Reliability and rollback: Changes are additive; rollback is reverting the four touched files (ci.yml.tmpl, validate_contract.py, blueprint.generated.mk.tmpl + regenerated .mk, both .pre-commit-config.yaml files).
- Monitoring/alerting: None — local pre-commit feedback is self-contained.

## Risks and Tradeoffs
- Risk 1: `validate_contract.py --bootstrap-drift-only` must load the full contract to resolve the managed-files list; if the contract is malformed the hook fails at commit time with a contract parse error. Mitigation: same behavior as the pre-push `--branch-only` path; malformed contract is always a blocking error.
- Tradeoff 1: Commit-stage hook adds ~1–2s per commit touching tracked files. Acceptable: comparable to other commit hooks (`bash-syntax`, `quality-docs-lint`).
