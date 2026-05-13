# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-007 | | Inference rule: blueprint-managed + source_exists=True → take_source | `scripts/lib/blueprint/upgrade_consumer.py` `_recommended_action()` | T-001, AC-001 unit test | ADR §Decision | triage JSON recommended_action field |
| FR-002 | SDD-C-005, SDD-C-007 | | Conservative path: blueprint-managed + source_exists=False → human_required | `scripts/lib/blueprint/upgrade_consumer.py` `_recommended_action()` | T-002, AC-002 unit test | ADR §Decision | triage JSON recommended_action field |
| FR-003 | SDD-C-005, SDD-C-008 | | source_exists boolean field in each triage entry | `scripts/lib/blueprint/upgrade_consumer.py` `_write_upgrade_triage()` | T-003, AC-004 unit test | architecture.md §Bounded Context | upgrade_triage.json per-entry field |
| FR-004 | SDD-C-005, SDD-C-008 | | reason field identifies inference basis for promoted entries | `scripts/lib/blueprint/upgrade_consumer.py` `_write_upgrade_triage()` | T-001 (reason assertion) | ADR §Decision D-3 | upgrade_triage.json reason field |
| FR-005 | SDD-C-005, SDD-C-011 | | source_exists optional boolean property on conflict entry schema | `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` | T-010 (schema validation) | ADR §Schema amendment | schema validation via make infra-contract-test-fast |
| FR-006 | SDD-C-005, SDD-C-007 | | Other ownership class mappings unchanged | `scripts/lib/blueprint/upgrade_consumer.py` `_RECOMMENDED_ACTION_MAP` | T-009 full suite GREEN | architecture.md §Bounded Context | existing triage outputs unaffected |
| NFR-REL-001 | SDD-C-007 | | Never more human_required rows than before | `_recommended_action()` returns human_required only for source_exists=False | T-002 (human_required path) | ADR §Consequences | |
| NFR-REL-002 | SDD-C-007 | | Schema version 1, source_exists non-required | `upgrade_triage.schema.json` (not in required array) | T-010 (old file validates) | ADR §Schema amendment | |
| NFR-OPS-001 | SDD-C-008 | | Documented in ADR Consequences with issue #270 reference | `docs/blueprint/architecture/decisions/ADR-issue-265-271-source-exists-inference.md` | — | ADR §Consequences | ADR available at publish |
| NFR-A11Y-001 | — | N/A | N/A — no UI | N/A | N/A | N/A | N/A |
| AC-001 | SDD-C-012 | | blueprint-managed + source_exists=True → take_source in triage JSON | `tests/blueprint/test_upgrade_consumer.py` | test_triage_blueprint_managed_source_exists_true_yields_take_source | — | |
| AC-002 | SDD-C-012 | | blueprint-managed + source_exists=False → human_required in triage JSON | `tests/blueprint/test_upgrade_consumer.py` | test_triage_blueprint_managed_source_exists_false_yields_human_required | — | |
| AC-003 | SDD-C-012 | | resolve target auto-applies take_source entries | `scripts/lib/blueprint/upgrade_consumer_resolve.py` (unchanged — reads recommended_action) | T-009 resolve integration | — | |
| AC-004 | SDD-C-012 | | source_exists boolean present in every conflict entry | `tests/blueprint/test_upgrade_consumer.py` | test_triage_entry_includes_source_exists_field | — | |
| AC-005 | SDD-C-012 | | Other ownership class mappings unaffected | `tests/blueprint/test_upgrade_consumer.py` (existing tests) | T-009 full suite GREEN | — | |
| AC-006 | SDD-C-011 | | Schema validates old and new files | `scripts/lib/blueprint/schemas/upgrade_triage.schema.json` | T-010 | — | schema version 1 unchanged |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-REL-001, NFR-REL-002, NFR-OPS-001, NFR-A11Y-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006

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
- Follow-up 1: Active delete-on-upgrade for consumer-created files in `blueprint_managed_roots` that match a blueprint path — out of scope; consumer must follow the `blueprint_managed_roots` exclusivity contract.
