# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement ID | Control IDs | Design Element | Implementation Path(s) | Test Evidence | Documentation Evidence | Operational Evidence |
|---|---|---|---|---|---|---|
| FR-001 | SDD-C-005, SDD-C-015 | Descriptor ownership class | `blueprint/contract.yaml`; `scripts/templates/blueprint/bootstrap/blueprint/contract.yaml` | contract parity tests | generated contract metadata | `infra-validate` |
| FR-002 | SDD-C-005, SDD-C-015 | Consumer init seed | `scripts/templates/consumer/init/apps/descriptor.yaml.tmpl` | init template tests | `docs/platform/consumer/quickstart.md` | `blueprint-init-repo` dry-run evidence |
| FR-003 | SDD-C-004, SDD-C-009 | Descriptor schema | `scripts/lib/blueprint/app_descriptor.py` (`load_app_descriptor`) | `tests/blueprint/test_app_descriptor_loader.py::AppDescriptorLoaderSchemaTests` | `docs/platform/consumer/app_onboarding.md` | validation stderr |
| FR-004 | SDD-C-004, SDD-C-009 | Explicit refs and convention defaults | `scripts/lib/blueprint/app_descriptor.py` (`_resolve_manifest_path`) | `tests/blueprint/test_app_descriptor_loader.py::AppDescriptorConventionAndMultiComponentTests` | app onboarding docs | validation stderr |
| FR-005 | SDD-C-007, SDD-C-015 | Multi-component topology | `scripts/lib/blueprint/app_descriptor.py` (`_collect_app_components`) | `test_app_with_multiple_components_loads_each` | app onboarding docs | validation stderr |
| FR-006 | SDD-C-009, SDD-C-010, SDD-C-012 | App runtime validation | `scripts/lib/blueprint/contract_validators/app_runtime_gitops.py` (calls `validate_app_descriptor`) | `tests/blueprint/test_app_descriptor_loader.py::AppDescriptorPathExistenceAndKustomizationTests`, `AppDescriptorAppRuntimeGitopsIntegrationTests` | troubleshooting docs | `infra-validate` |
| FR-007 | SDD-C-007, SDD-C-015 | Compatibility catalog renderer input | `scripts/lib/platform/apps/catalog_scaffold_renderer.py` (`render_delivery_workloads_block`, `render_gitops_workloads_block`, `cmd_render`); `scripts/bin/platform/apps/bootstrap.sh` (`--app-descriptor-path` + `--component-image[-env-var]`) | `tests/blueprint/test_app_catalog_descriptor_rendering.py::CatalogManifestEndToEndRenderingTests`, `DescriptorWorkloadBlockRenderingTests` | quickstart docs | `apps-bootstrap`; `apps-smoke` |
| FR-008 | SDD-C-011, SDD-C-012 | App catalog deprecation | `scripts/templates/platform/apps/catalog/manifest.yaml.tmpl` (DEPRECATED header comment naming apps/descriptor.yaml + two-minor-release window); rendered `apps/catalog/manifest.yaml` carries the same header | `tests/blueprint/test_consumer_app_descriptor_deprecations.py::CatalogManifestDeprecationTests` | quickstart/troubleshooting docs | apps smoke artifact |
| FR-009 | SDD-C-010, SDD-C-012 | Upgrade diagnostics | `scripts/lib/blueprint/upgrade_consumer.py` (`_descriptor_referenced_paths`, `_classify_entries` consumer-app-descriptor branch, `_summarize_apply` consumer_app_descriptor_count) | `tests/blueprint/test_consumer_app_descriptor_upgrade.py::DescriptorOwnershipPruneGuardTests` | execution model docs | apply artifact `consumer_app_descriptor_count`; reconcile/postcheck JSON |
| FR-010 | SDD-C-007, SDD-C-012 | Bridge guard deprecation | `scripts/lib/blueprint/upgrade_consumer.py` (`_is_consumer_owned_workload` retained as fallback after `consumer-app-descriptor` branch); `AGENTS.backlog.md` decommission entries | `tests/blueprint/test_upgrade_consumer.py` prune guard regression tests | ADR | upgrade apply artifact |
| FR-011 | SDD-C-010, SDD-C-012 | Suggested descriptor artifact | `scripts/lib/blueprint/upgrade_consumer.py` (`generate_suggested_descriptor`, `write_suggested_descriptor_artifact`, apply-flow wiring) | `tests/blueprint/test_consumer_app_descriptor_upgrade.py::SuggestedDescriptorArtifactTests` | troubleshooting docs | `artifacts/blueprint/app_descriptor.suggested.yaml` |
| NFR-SEC-001 | SDD-C-009 | Safe YAML and path constraints | `scripts/lib/blueprint/app_descriptor.py` (`yaml.safe_load`, `_validate_manifest_path`) | `tests/blueprint/test_app_descriptor_loader.py::AppDescriptorUnsafeIdAndPathTests` | app onboarding docs | validation failure artifact |
| NFR-OBS-001 | SDD-C-010 | Deterministic diagnostics | `scripts/lib/blueprint/app_descriptor.py` (`verify_resolved_manifests_exist`, `verify_kustomization_membership`) | `test_missing_resolved_deployment_manifest_reports_named_error`, `test_missing_kustomization_membership_reports_named_error` | troubleshooting docs | diagnostics output |
| NFR-REL-001 | SDD-C-012 | Two-minor-release fallback | validators and upgrade flow | absent-descriptor tests | quickstart upgrade notes | upgrade warning evidence |
| NFR-OPS-001 | SDD-C-010, SDD-C-011 | Runbook guidance | docs | docs validation | quickstart/app_onboarding/troubleshooting | operator runbook evidence |
| AC-001 | SDD-C-012 | Consumer-seeded descriptor | contract/template paths | contract parity tests | generated contract metadata | `infra-validate` |
| AC-002 | SDD-C-009 | Unsafe ID/path rejection | `scripts/lib/blueprint/app_descriptor.py` (`_SAFE_ID_RE`, `_validate_manifest_path`) | `tests/blueprint/test_app_descriptor_loader.py::AppDescriptorUnsafeIdAndPathTests` | troubleshooting docs | validation stderr |
| AC-003 | SDD-C-012 | Missing resolved manifest rejection | `scripts/lib/blueprint/app_descriptor.py` (`verify_resolved_manifests_exist`) | `test_missing_resolved_deployment_manifest_reports_named_error` | troubleshooting docs | validation stderr |
| AC-004 | SDD-C-012 | Kustomization drift rejection | `scripts/lib/blueprint/app_descriptor.py` (`verify_kustomization_membership`) | `test_missing_kustomization_membership_reports_named_error` | troubleshooting docs | validation stderr |
| AC-005 | SDD-C-015 | Descriptor-driven compatibility catalog render | `scripts/lib/platform/apps/catalog_scaffold_renderer.py` (no baseline ID literals) | `test_renderer_module_has_no_hardcoded_baseline_ids`, `test_non_baseline_descriptor_renders_descriptor_components` | quickstart docs | `apps-bootstrap` evidence |
| AC-006 | SDD-C-010 | Descriptor ownership diagnostics | `scripts/lib/blueprint/upgrade_consumer.py` (`_classify_entries` consumer-app-descriptor branch + summary counter); `scripts/lib/blueprint/schemas/upgrade_apply.schema.json` (`consumer_app_descriptor_count`) | `test_classify_descriptor_listed_path_marks_consumer_app_descriptor`, `test_descriptor_guard_takes_precedence_over_kustomization_ref`, `test_apply_summary_counts_consumer_app_descriptor` | execution model docs | apply artifact `consumer_app_descriptor_count` |
| AC-007 | SDD-C-012 | Baseline smoke preservation | template smoke and app smoke; `apps/descriptor.yaml` seeded at blueprint root | `test_baseline_descriptor_renders_two_workloads_with_baseline_ids`; `apps-smoke` | app onboarding docs | `apps-smoke` (catalog disabled + enabled) |
| AC-008 | SDD-C-010, SDD-C-012 | Suggested descriptor for existing consumers | `scripts/lib/blueprint/upgrade_consumer.py` (`generate_suggested_descriptor` emits review-guidance comments + `team:` placeholder marker; `write_suggested_descriptor_artifact` writes to artifacts/blueprint/ only) | `test_suggested_descriptor_includes_review_guidance_comments`, `test_apply_writes_suggested_descriptor_when_descriptor_absent`, `test_apply_skips_suggested_descriptor_when_descriptor_present` | troubleshooting docs | `artifacts/blueprint/app_descriptor.suggested.yaml` |
| AC-009 | SDD-C-011, SDD-C-012 | Decommission diagnostics | `scripts/lib/blueprint/upgrade_consumer.py` (DEPRECATED docstring on `_is_consumer_owned_workload`); `scripts/templates/platform/apps/catalog/manifest.yaml.tmpl` (DEPRECATED header); `AGENTS.backlog.md` (two `decommission:` entries with `after: consumer-app-descriptor-adoption` triggers) | `tests/blueprint/test_consumer_app_descriptor_deprecations.py::BridgeGuardDeprecationTests`, `BacklogDecommissionTrackingTests` | ADR; backlog | upgrade/app smoke diagnostics |

## Graph Linkage
- Graph file: `graph.json`
- Every `FR-###`, `NFR-*-###`, and `AC-###` listed in this file MUST have a corresponding node in `graph.json`.
- Node IDs referenced:
  - FR-001
  - FR-002
  - FR-003
  - FR-004
  - FR-005
  - FR-006
  - FR-007
  - FR-008
  - FR-009
  - FR-010
  - FR-011
  - NFR-SEC-001
  - NFR-OBS-001
  - NFR-REL-001
  - NFR-OPS-001
  - AC-001
  - AC-002
  - AC-003
  - AC-004
  - AC-005
  - AC-006
  - AC-007
  - AC-008
  - AC-009

## Validation Summary
- Required bundles executed: intake and plan slicing; `make quality-sdd-check` passed.
- Result summary: implementation not started; `SPEC_READY=true` is recorded and Step 04 planning is dependency-ordered.
- Traceability keeper result: clean for planning scope. FR, NFR, and AC rows map to design elements, planned implementation paths, automated test evidence, documentation evidence, and operational evidence.
- Documentation validation:
  - `make docs-build`
  - `make docs-smoke`

## Evidence Manifest
- Manifest file: `evidence_manifest.json`
- Context export: `context_pack.md`
- PR context export: `pr_context.md`
- Hardening review export: `hardening_review.md`

## Open Risks and Follow-Ups
- Follow-up 1: remove deprecated `apps/catalog/manifest.yaml` compatibility output after two blueprint minor releases.
- Follow-up 2: remove deprecated `_is_consumer_owned_workload()` bridge guard after two blueprint minor releases or once descriptor coverage becomes mandatory, whichever is later.
