# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005 | Missing required consumer-owned target detection from source platform make surfaces | `scripts/lib/blueprint/upgrade_consumer.py` (`_collect_missing_platform_make_target_actions`) | `python3 -m unittest tests.blueprint.test_upgrade_consumer` | n/a | `artifacts/blueprint/upgrade_plan.json` required_manual_actions |
| FR-002 | SDD-C-005 | Contract-fallback manual action when invoker reference is unavailable | `scripts/lib/blueprint/upgrade_consumer.py` (`dependency_of` fallback) | `test_upgrade_plan_flags_manual_action_for_missing_required_consumer_make_target_from_contract` | n/a | `make blueprint-upgrade-consumer-preflight` report includes fallback dependency context |
| FR-003 | SDD-C-005 | Deterministic location guidance in manual-action reason | `scripts/lib/blueprint/upgrade_consumer.py` (`_platform_make_location_hint`) | `test_upgrade_plan_flags_manual_action_for_missing_required_consumer_make_target_from_contract` | `docs/platform/consumer/quickstart.md`, `docs/platform/consumer/troubleshooting.md` | required manual action reasons include expected target surfaces |
| FR-004 | SDD-C-005 | Preserve invoker path context with fallback behavior | `scripts/lib/blueprint/upgrade_consumer.py` | `test_upgrade_plan_flags_manual_action_for_missing_platform_ci_bootstrap_target` | n/a | upgrade preflight/readiness doctor consume dependency_of consistently |
| FR-005 | SDD-C-005 | Placeholder safeguards stay active with location guidance | `scripts/lib/blueprint/upgrade_consumer.py` | `test_upgrade_plan_flags_manual_action_for_placeholder_platform_ci_bootstrap_consumer_target`; `test_upgrade_plan_flags_manual_action_for_placeholder_local_post_deploy_consumer_target_when_enabled` | `docs/platform/consumer/troubleshooting.md` | `make blueprint-upgrade-consumer-validate` follow-up command preserved |
| NFR-SEC-001 | SDD-C-009 | Read-only detection path with no new privilege surface | `scripts/lib/blueprint/upgrade_consumer.py` | `python3 -m unittest tests.blueprint.test_upgrade_consumer` | n/a | plan-only diagnostics remain non-mutating |
| NFR-OBS-001 | SDD-C-010 | Deterministic reason/dependency context for machine-readable reports | `scripts/lib/blueprint/upgrade_consumer.py`; `scripts/lib/blueprint/upgrade_preflight.py` | `python3 -m unittest tests.blueprint.test_upgrade_preflight` | docs update explains report usage | `upgrade_preflight.json` fields remain stable |
| NFR-REL-001 | SDD-C-008 | Regression-safe evolution of existing manual-action behavior | `tests/blueprint/test_upgrade_consumer.py` | `python3 -m unittest tests.blueprint.test_upgrade_consumer` | n/a | stable required manual action counts and follow-up commands |
| NFR-OPS-001 | SDD-C-010 | Deterministic remediation guidance and canonical follow-up command | `scripts/lib/blueprint/upgrade_consumer.py` | `python3 -m unittest tests.blueprint.test_upgrade_consumer` | `docs/platform/consumer/quickstart.md`; `docs/platform/consumer/troubleshooting.md` | `make blueprint-upgrade-consumer-validate` |
| AC-001 | SDD-C-012 | Red->green test coverage for new missing-target gap | `tests/blueprint/test_upgrade_consumer.py` | `test_upgrade_plan_flags_manual_action_for_missing_required_consumer_make_target_from_contract` | n/a | CI/unit lane |
| AC-002 | SDD-C-012 | Manual action reason includes target + location guidance | `scripts/lib/blueprint/upgrade_consumer.py` | same as AC-001 | docs mention expected definition locations | preflight checklist readability |
| AC-003 | SDD-C-012 | Invoker-path context + contract fallback behavior | `scripts/lib/blueprint/upgrade_consumer.py` | `test_upgrade_plan_flags_manual_action_for_missing_platform_ci_bootstrap_target`; AC-001 test | n/a | upgrade_preflight manual actions preserve dependency_of semantics |
| AC-004 | SDD-C-012 | Existing placeholder guardrails preserved | `scripts/lib/blueprint/upgrade_consumer.py` | placeholder tests in `tests/blueprint/test_upgrade_consumer.py` | troubleshooting guidance retained | follow-up validate command unchanged |
| AC-005 | SDD-C-012 | Consumer docs clarify preflight required-target checklist behavior | `docs/platform/consumer/quickstart.md`; `docs/platform/consumer/troubleshooting.md` | docs sync checks | same paths | runbook-level guidance for operators |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005

## Validation Summary
- Required bundles executed:
  - `python3 -m unittest tests.blueprint.test_upgrade_consumer`
  - `python3 -m unittest tests.blueprint.test_upgrade_preflight`
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
  - `python3 scripts/lib/docs/sync_platform_seed_docs.py --check`
  - `make quality-hooks-fast`
  - `make quality-hardening-review`
- Result summary:
  - `tests.blueprint.test_upgrade_consumer`: 22 tests passed.
  - `tests.blueprint.test_upgrade_preflight`: 4 tests passed.
  - docs sync checks passed for blueprint template and platform seed mirrors.
  - `make quality-hooks-fast` passed, including `infra-validate` and `infra-contract-test-fast` (21 tests passed, 2 subtests passed).
  - `make quality-hardening-review` passed.
- Documentation validation:
  - `python3 scripts/lib/docs/sync_blueprint_template_docs.py --check`
  - `python3 scripts/lib/docs/sync_platform_seed_docs.py --check`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: monitor operator feedback for checklist volume on legacy repositories with broad target drift.
