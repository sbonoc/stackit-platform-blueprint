# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | | Test file audit — classification table | `architecture.md` §Test File Audit | T-000 audit output | `architecture.md` §Test File Audit | Classification drives all subsequent relocation decisions |
| FR-002 | SDD-C-005, SDD-C-008 | | Fully blueprint-author files moved to `tests/blueprint/` | `tests/blueprint/test_<name>.py` (new/updated) | `test_required_seed_files_contain_no_blueprint_module_refs` (AC-004) | ADR §Decision | `required_seed_files` shrinks; upgrade engine stops writing these files |
| FR-003 | SDD-C-005, SDD-C-008 | | Mixed files split along blueprint-author/consumer-runtime boundary | `tests/blueprint/` (extracted classes), `tests/infra/` (remaining consumer classes) | AC-002, AC-003 | ADR §Decision | Consumer-runtime classes remain in `tests/infra/` and are still delivered |
| FR-004 | SDD-C-005, SDD-C-011 | | `required_seed_files` updated in `blueprint/contract.yaml` | `blueprint/contract.yaml` | AC-005 (`make infra-validate`) | ADR §Files Changed | `make infra-validate` validates schema |
| FR-005 | SDD-C-005, SDD-C-007 | | Contract assertion in `test_quality_contracts.py` | `tests/blueprint/test_quality_contracts.py` | `test_required_seed_files_contain_no_blueprint_module_refs` | — | Commit-time enforcement via pytest |
| FR-006 | SDD-C-005, SDD-C-007 | | Import paths updated for relocated test classes | All relocated `tests/blueprint/test_*.py` files | AC-002 (`uv run python3 -m pytest tests/blueprint/ -v`) | — | Full test suite passes |
| NFR-REL-001 | SDD-C-007 | | Consumer-runtime classes stay in `tests/infra/` | `tests/infra/` (unchanged consumer-runtime files) | AC-003 (`uv run python3 -m pytest tests/infra/ -v`) | — | Consumer CI unaffected |
| NFR-REL-002 | SDD-C-007 | | `required_seed_files` count reduces | `blueprint/contract.yaml` | T-203 (count verified) | — | Upgrade engine scope reduced |
| NFR-OPS-001 | SDD-C-008 | | Taxonomy rule documented | `docs/blueprint/governance/` | T-010 | `docs/blueprint/governance/ownership_matrix.md` | Blueprint maintainers know which directory to use for new tests |
| NFR-A11Y-001 | — | N/A | N/A — no UI | N/A | N/A | N/A | N/A |
| AC-001 | SDD-C-012 | | All `blueprint/modules/`-asserting classes in `tests/blueprint/` | `tests/blueprint/` relocated files | `test_required_seed_files_contain_no_blueprint_module_refs` | — | Contract assertion green |
| AC-002 | SDD-C-012 | | `pytest tests/blueprint/` green | All `tests/blueprint/` files | Slice 2 GREEN run | — | All relocated classes pass |
| AC-003 | SDD-C-012 | | `pytest tests/infra/` green | `tests/infra/` (consumer-runtime only) | Slice 2 GREEN run | — | No consumer test regressions |
| AC-004 | SDD-C-012 | | Contract assertion for `required_seed_files` | `tests/blueprint/test_quality_contracts.py` | `test_required_seed_files_contain_no_blueprint_module_refs` | — | Passes after relocation |
| AC-005 | SDD-C-011 | | `make infra-validate` passes | `blueprint/contract.yaml` | T-202 | — | Contract schema valid |
| AC-006 | SDD-C-008, SDD-C-024 | | `make quality-hooks-fast` passes | All changed paths | T-201 | — | All quality gates pass |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-REL-001, NFR-REL-002, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

## Validation Summary
- Required bundles executed: `uv run python3 -m pytest tests/blueprint/ -v` (GREEN), `uv run python3 -m pytest tests/infra/test_tooling_contracts.py -v` (13 tests PASS), `make infra-contract-test-fast` (68 tests PASS), `make infra-validate` (PASS), `make quality-hooks-fast` (PASS — all checks), `make quality-hardening-review` (PASS)
- Result summary: All validation gates PASS. `required_files` reduced from 16 to 12 entries. Test pyramid within bounds (unit 96.70%, integration 2.48%, e2e 0.83%).
- Documentation validation:
  - `make docs-build` — PASS
  - `make docs-smoke` — PASS

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: Stale copies of relocated files in existing consumer repos (e.g. dhe-marketplace) remain until re-init or manual deletion. No CI failures expected (the files assert against blueprint internals not present in consumer repos), but cleanup is the consumer's responsibility post-upgrade.
- Follow-up 2: Active delete-on-upgrade for relocated paths is deferred — if a consumer has a modified copy of a relocated file and runs upgrade, the modified copy is preserved (not deleted). A future work item can add active cleanup if needed.
