# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | WCAG SC | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-011 | — | `stackit_secretsmanager_instance.this` + `stackit_secretsmanager_user.this` in standalone TF module | `infra/cloud/stackit/terraform/modules/secrets-manager/main.tf` | AC-001, AC-002: test_contract.py assertions | ADR-issue-248-secrets-manager-module.md D-1 | n/a |
| FR-002 | SDD-C-005, SDD-C-011 | — | `variables.tf` with six required variables | `infra/cloud/stackit/terraform/modules/secrets-manager/variables.tf` | AC-003: test_contract.py assertion | n/a | n/a |
| FR-003 | SDD-C-005, SDD-C-009 | — | `outputs.tf` with instance_id, username, password (sensitive) | `infra/cloud/stackit/terraform/modules/secrets-manager/outputs.tf` | AC-004: test_contract.py assertion | n/a | n/a |
| FR-004 | SDD-C-005, SDD-C-008 | — | `module.contract.yaml` outputs.produced updated | `blueprint/modules/secrets-manager/module.contract.yaml` | AC-005: test_contract.py assertion | module.contract.yaml | n/a |
| FR-005 | SDD-C-005, SDD-C-011 | — | `secrets_manager_namespace()` | `scripts/lib/infra/secrets_manager.sh` | AC-006: test_contract.py assertion | n/a | n/a |
| FR-006 | SDD-C-005, SDD-C-011 | — | `secrets_manager_auth_method_details()` | `scripts/lib/infra/secrets_manager.sh` | AC-007: test_contract.py assertion | n/a | n/a |
| FR-007 | SDD-C-005, SDD-C-009 | — | `secrets_manager_reconcile_runtime_secret()` + `secrets_manager_delete_runtime_secret()` | `scripts/lib/infra/secrets_manager.sh` | AC-008: test_contract.py assertion | n/a | n/a |
| FR-008 | SDD-C-005, SDD-C-010 | — | `secrets_manager_apply.sh` state write + reconcile call | `scripts/bin/infra/secrets_manager_apply.sh` | AC-009: test_contract.py + test_optional_modules.py | n/a | n/a |
| FR-009 | SDD-C-005, SDD-C-010 | — | `secrets_manager_plan.sh` namespace key | `scripts/bin/infra/secrets_manager_plan.sh` | AC-010: test_contract.py assertion | n/a | n/a |
| FR-010 | SDD-C-005, SDD-C-012 | — | `secrets_manager_smoke.sh` namespace + auth_method_details checks | `scripts/bin/infra/secrets_manager_smoke.sh` | AC-011: test_contract.py assertion | n/a | n/a |
| FR-011 | SDD-C-005, SDD-C-012 | — | `test_contract.py` with >= 10 assertions | `tests/infra/modules/secrets-manager/test_contract.py` | AC-013: pytest PASS | n/a | n/a |
| FR-012 | SDD-C-005, SDD-C-009 | — | `secrets_manager_destroy.sh` calls `secrets_manager_delete_runtime_secret()` | `scripts/bin/infra/secrets_manager_destroy.sh` | AC-014: test_contract.py assertion | n/a | n/a |
| FR-013 | SDD-C-005, SDD-C-012 | — | `test_pyramid_contract.json` entry added before test file creation | `scripts/lib/quality/test_pyramid_contract.json` | AC-015: pre-commit passes | n/a | n/a |
| NFR-SEC-001 | SDD-C-009 | — | Password NEVER in state file; auth_method_details = username only | `secrets_manager_apply.sh` + `secrets_manager.sh` | AC-012: test_contract.py assertion | ADR D-3 | n/a |
| NFR-OBS-001 | SDD-C-010 | — | namespace + auth_method_details in state; smoke validates both keys non-empty; prefixed output | `secrets_manager_smoke.sh` + apply.sh | AC-011: smoke non-empty check | n/a | n/a |
| NFR-REL-001 | SDD-C-012 | — | `lifecycle { create_before_destroy = true }` on instance | `main.tf` | AC-001: test_contract.py structural check | ADR D-1 | n/a |
| NFR-OPS-001 | SDD-C-010 | — | namespace + auth_method_details in runtime state artifact | `secrets_manager_apply.sh` | AC-009: state key assertions | n/a | n/a |
| NFR-A11Y-001 | — | — | N/A — no UI changes | — | — | — | — |
| AC-001 | SDD-C-012 | — | main.tf stackit_secretsmanager_instance.this with lifecycle | test_contract.py | pytest PASS | — | n/a |
| AC-002 | SDD-C-012 | — | main.tf stackit_secretsmanager_user.this | test_contract.py | pytest PASS | — | n/a |
| AC-003 | SDD-C-012 | — | variables.tf six variables | test_contract.py | pytest PASS | — | n/a |
| AC-004 | SDD-C-012 | — | outputs.tf instance_id, username, password (sensitive) | test_contract.py | pytest PASS | — | n/a |
| AC-004b | SDD-C-012 | — | versions.tf declares stackitcloud/stackit required provider with pinned version | test_contract.py | pytest PASS | — | n/a |
| AC-005 | SDD-C-012 | — | module.contract.yaml SECRETS_MANAGER_NAMESPACE + AUTH_METHOD_DETAILS | test_contract.py | pytest PASS | — | n/a |
| AC-006 | SDD-C-012 | — | secrets_manager_namespace() returns instance_name | test_contract.py | pytest PASS | — | n/a |
| AC-007 | SDD-C-012 | — | secrets_manager_auth_method_details() returns username | test_contract.py | pytest PASS | — | n/a |
| AC-008 | SDD-C-012 | — | reconcile_runtime_secret() writes + delete_runtime_secret() removes blueprint-secrets-manager-auth | test_contract.py | pytest PASS | — | n/a |
| AC-009 | SDD-C-012 | — | apply.sh writes namespace + auth_method_details and calls reconcile | test_contract.py + test_optional_modules.py | pytest PASS | — | n/a |
| AC-010 | SDD-C-012 | — | plan.sh writes namespace | test_contract.py | pytest PASS | — | n/a |
| AC-011 | SDD-C-012 | — | smoke.sh exits non-zero if namespace or auth_method_details absent or empty | test_contract.py | pytest PASS | — | n/a |
| AC-012 | SDD-C-009 | — | runtime state MUST NOT contain password | test_contract.py security assertion | pytest PASS | — | n/a |
| AC-013 | SDD-C-012 | — | test_contract.py passes >= 10 assertions | test_contract.py | pytest PASS | — | n/a |
| AC-014 | SDD-C-009 | — | destroy.sh calls delete_runtime_secret() | secrets_manager_destroy.sh | test_contract.py assertion | — | n/a |
| AC-015 | SDD-C-012 | — | test_contract.py in test_pyramid_contract.json | scripts/lib/quality/test_pyramid_contract.json | pre-commit PASS | — | n/a |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013
  - NFR-SEC-001, NFR-OBS-001, NFR-REL-001, NFR-OPS-001, NFR-A11Y-001
  - AC-001, AC-002, AC-003, AC-004, AC-004b, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015

## Validation Summary
- Required bundles executed: (pending implementation)
- Result summary: (pending implementation)
- Documentation validation:
  - `make docs-build`: (pending)
  - `make docs-smoke`: (pending)

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up: Remaining 5 stub modules from #248 (dns, public-endpoints, observability, workflows, identity-aware-proxy) to be implemented in separate work items.
