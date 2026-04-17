# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-020, SDD-C-001 | Strict-default SDD governance policy | `AGENTS.md`, `README.md`, `specs/README.md`, `docs/blueprint/governance/spec_driven_development.md`, `docs/blueprint/governance/assistant_compatibility.md`, `CLAUDE.md` | `make quality-sdd-check-all` | same implementation paths plus consumer template mirrors | `make quality-hooks-run` pass on PR branch |
| FR-002 | SDD-C-021, SDD-C-003 | Dedicated-branch scaffold flow | `scripts/bin/blueprint/spec_scaffold.py`, `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`, `blueprint/contract.yaml` | `tests/blueprint/test_spec_scaffold.py` (`test_scaffold_creates_dedicated_branch_by_default`, `test_scaffold_no_create_branch_explicit_opt_out`, `test_scaffold_allows_explicit_branch_override`) | `specs/README.md`, `scripts/bin/infra/help_reference.sh` | deterministic scaffold output lines for branch status |
| NFR-SEC-001 | SDD-C-009, SDD-C-021 | Explicit opt-out/override controls | `scripts/bin/blueprint/spec_scaffold.py`, `blueprint/contract.yaml` | `tests/blueprint/test_spec_scaffold.py` | `AGENTS.md`, `README.md` | branch enforcement prevents default-branch work-item starts |
| NFR-OBS-001 | SDD-C-010 | Deterministic diagnostics for operators | `scripts/bin/blueprint/spec_scaffold.py`, `scripts/bin/quality/check_sdd_assets.py` | `tests/infra/test_sdd_asset_checker.py` | `docs/blueprint/governance/assistant_compatibility.md` | checker and scaffold console output is deterministic |
| NFR-REL-001 | SDD-C-012, SDD-C-021 | Contract-to-tooling consistency checks | `scripts/bin/quality/check_sdd_assets.py`, `.spec-kit/control-catalog.yaml` | `tests/infra/test_sdd_asset_checker.py` | `.spec-kit/policy-mapping.md` | `make infra-validate`, `make quality-hooks-run` pass |
| NFR-OPS-001 | SDD-C-010, SDD-C-018 | Deterministic operator entrypoints | `make/blueprint.generated.mk`, `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`, `scripts/bin/infra/help_reference.sh` | `make quality-sdd-check-all` | `specs/README.md`, consumer README templates | explicit make flags: `SPEC_BRANCH`, `SPEC_NO_BRANCH` |
| AC-001 | SDD-C-021 | Default branch creation + explicit modes | `scripts/bin/blueprint/spec_scaffold.py` | `tests/blueprint/test_spec_scaffold.py` | `specs/README.md` | scaffold command output captured in PR evidence |
| AC-002 | SDD-C-020, SDD-C-021 | Branch contract checker enforcement | `scripts/bin/quality/check_sdd_assets.py` | `tests/infra/test_sdd_asset_checker.py` | `.spec-kit/control-catalog.md` | `make quality-sdd-check-all` pass |

## Graph Linkage
- Graph file: `graph.yaml`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.yaml`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002

## Validation Summary
- Required bundles executed:
  - `make quality-sdd-check-all`
  - `make infra-validate`
  - `make quality-hooks-run`
  - `./.venv/bin/python -m pytest -q tests/blueprint/test_spec_scaffold.py tests/infra/test_sdd_asset_checker.py`
- Result summary: all listed commands passed on `codex/sdd-default-enforcement-and-branching` before draft PR creation.
- Documentation validation:
  - `make docs-build` and `make docs-smoke` were not executed for this work item.
  - Documentation drift checks ran inside `make quality-hooks-run` and passed.

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: complete full docs-site build/smoke in a follow-up change if required by release gate scope.
- Follow-up 2: consider explicit checker support for retrospective work items where implementation predates readiness closure.
