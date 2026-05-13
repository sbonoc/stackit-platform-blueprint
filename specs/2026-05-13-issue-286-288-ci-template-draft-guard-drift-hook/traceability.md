# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | | Consumer CI template — `pull_request.types` filter | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_has_draft_pr_types_filter` | ADR §Decision 4 | Consumer CI skips draft PR events |
| FR-002 | SDD-C-005, SDD-C-007 | | Consumer CI template — `quality-fast` job draft guard | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_quality_fast_has_draft_pr_guard` | ADR §Decision 4 | Consumer CI jobs not triggered on draft PRs |
| FR-003 | SDD-C-005, SDD-C-008 | | `quality-validate-bootstrap-template-drift` Make target | `scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl`, `make/blueprint.generated.mk` | `test_make_template_has_quality_validate_bootstrap_drift_target` | — | `make quality-validate-bootstrap-template-drift` exits 0 on parity |
| FR-004 | SDD-C-005, SDD-C-008 | | Commit-stage pre-commit hook | `.pre-commit-config.yaml`, `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_has_bootstrap_drift_hook`, `test_precommit_template_has_bootstrap_drift_hook` | — | Hook fires at commit time when tracked files change |
| FR-005 | SDD-C-005, SDD-C-007 | | `validate_contract.py --bootstrap-drift-only` fast path | `scripts/bin/blueprint/validate_contract.py` | AC-003 + AC-004 (`make quality-validate-bootstrap-template-drift` manual verification) | ADR §Decision 1 | Exit 0 on parity; exit 1 on drift with `[infra-validate] error:` prefix |
| NFR-SEC-001 | SDD-C-009 | | `language: system` + `make` entry in hook | `.pre-commit-config.yaml`, `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | Hook stanza review | ADR §Non-Functional Architecture Notes | No remote exec; no credential exposure |
| NFR-OBS-001 | SDD-C-010 | | N/A | N/A | N/A | N/A | N/A |
| NFR-REL-001 | SDD-C-007 | | Additive changes only; no hook/target removals | All five changed files — new content appended; no existing keys removed | All pre-existing tests remain green | — | `pre-commit install` picks up new hook on next run |
| NFR-OPS-001 | SDD-C-010 | | N/A — no runbook changes required | N/A | N/A | N/A | N/A |
| NFR-A11Y-001 | — | N/A | N/A — CI/quality tooling only; no UI | N/A | N/A | N/A | N/A |
| AC-001 | SDD-C-012 | | `types: [...]` in `ci.yml.tmpl` trigger | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_has_draft_pr_types_filter` | — | Consumer CI event filter active |
| AC-002 | SDD-C-012 | | `if: ... draft == false` on `quality-fast` job | `scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl` | `test_consumer_ci_template_quality_fast_has_draft_pr_guard` | — | Consumer CI draft guard active |
| AC-003 | SDD-C-012 | | `make quality-validate-bootstrap-template-drift` exits 0 | `scripts/bin/blueprint/validate_contract.py`, `make/blueprint.generated.mk` | Manual: `make quality-validate-bootstrap-template-drift` + `make infra-validate` | — | Exit 0 confirmed |
| AC-004 | SDD-C-012 | | `make quality-validate-bootstrap-template-drift` exits 1 on drift | `scripts/bin/blueprint/validate_contract.py` | Manual: introduce deliberate drift and verify exit 1 + error message | — | Drift detection confirmed |
| AC-005 | SDD-C-008, SDD-C-024 | | `.pre-commit-config.yaml` hook stanza | `.pre-commit-config.yaml` | `test_precommit_has_bootstrap_drift_hook` | — | pytest green |
| AC-006 | SDD-C-008, SDD-C-024 | | Template `.pre-commit-config.yaml` hook stanza | `scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml` | `test_precommit_template_has_bootstrap_drift_hook` | — | pytest green |
| AC-007 | SDD-C-008, SDD-C-024 | | 5 new pytest assertions green in `test_quality_contracts.py` | `tests/blueprint/test_quality_contracts.py` | `uv run python3 -m pytest tests/blueprint/test_quality_contracts.py -v` | — | CI test run |
| AC-008 | SDD-C-001, SDD-C-002 | | `make quality-hooks-fast` passes | All changed paths | `QUALITY_HOOKS_KEEP_GOING=true make quality-hooks-fast` output | — | CI quality gate pass |
| AC-009 | SDD-C-011 | | `make infra-validate` passes | All changed paths | `make infra-validate` output | — | CI infra-validate pass |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009

## Validation Summary
- Required bundles executed: (to be filled at publish)
- Result summary: (to be filled at publish)
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Long-term — evaluate adding `.pre-commit-config.yaml` and its sibling root dotfiles to `_QG_INFRA_GATE_PATHS` so local `infra-validate` (not just the new commit hook) catches drift when those files change; deferred as a separate quality infrastructure work item.
