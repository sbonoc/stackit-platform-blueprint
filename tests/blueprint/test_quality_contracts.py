from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.helpers import REPO_ROOT, run


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


class QualityContractsTests(unittest.TestCase):
    def test_root_bootstrap_delegates_to_shell_bootstrap(self) -> None:
        bootstrap = _read("scripts/lib/bootstrap.sh")
        self.assertIn('scripts/lib/shell/bootstrap.sh', bootstrap)

    def test_root_semver_delegates_to_quality_semver(self) -> None:
        semver = _read("scripts/lib/semver.sh")
        self.assertIn('scripts/lib/quality/semver.sh', semver)

    def test_make_template_exposes_quality_docs_targets(self) -> None:
        make_template = _read("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl")
        self.assertIn("quality-hooks-fast", make_template)
        self.assertIn("quality-hooks-strict", make_template)
        self.assertIn("quality-ci-sync", make_template)
        self.assertIn("quality-ci-check-sync", make_template)
        self.assertIn("quality-docs-lint", make_template)
        self.assertIn("quality-docs-sync-blueprint-template", make_template)
        self.assertIn("quality-docs-check-blueprint-template-sync", make_template)
        self.assertIn("quality-docs-sync-platform-seed", make_template)
        self.assertIn("quality-docs-check-platform-seed-sync", make_template)
        self.assertIn("quality-docs-sync-core-targets", make_template)
        self.assertIn("quality-docs-check-core-targets-sync", make_template)
        self.assertIn("quality-docs-sync-contract-metadata", make_template)
        self.assertIn("quality-docs-check-contract-metadata-sync", make_template)
        self.assertIn("quality-docs-sync-runtime-identity-summary", make_template)
        self.assertIn("quality-docs-check-runtime-identity-summary-sync", make_template)
        self.assertIn("quality-docs-sync-module-contract-summaries", make_template)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", make_template)
        self.assertIn("quality-test-pyramid", make_template)
        self.assertIn("infra-contract-test-fast", make_template)

    def test_generated_makefile_exposes_quality_docs_targets(self) -> None:
        generated_make = _read("make/blueprint.generated.mk")
        self.assertIn("quality-hooks-fast", generated_make)
        self.assertIn("quality-hooks-strict", generated_make)
        self.assertIn("quality-ci-sync", generated_make)
        self.assertIn("quality-ci-check-sync", generated_make)
        self.assertIn("quality-docs-lint", generated_make)
        self.assertIn("quality-docs-sync-blueprint-template", generated_make)
        self.assertIn("quality-docs-check-blueprint-template-sync", generated_make)
        self.assertIn("quality-docs-sync-platform-seed", generated_make)
        self.assertIn("quality-docs-check-platform-seed-sync", generated_make)
        self.assertIn("quality-docs-sync-core-targets", generated_make)
        self.assertIn("quality-docs-check-core-targets-sync", generated_make)
        self.assertIn("quality-docs-sync-contract-metadata", generated_make)
        self.assertIn("quality-docs-check-contract-metadata-sync", generated_make)
        self.assertIn("quality-docs-sync-runtime-identity-summary", generated_make)
        self.assertIn("quality-docs-check-runtime-identity-summary-sync", generated_make)
        self.assertIn("quality-docs-sync-module-contract-summaries", generated_make)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", generated_make)
        self.assertIn("quality-test-pyramid", generated_make)
        self.assertIn("infra-contract-test-fast", generated_make)

    def test_docs_generator_supports_check_mode(self) -> None:
        generator = _read("scripts/lib/docs/generate_contract_docs.py")
        self.assertIn("--check", generator)
        self.assertNotIn("Generated at:", generator)
        self.assertIn("resolve_repo_root", generator)

    def test_ci_workflow_renderer_is_contract_driven(self) -> None:
        renderer = _read("scripts/lib/quality/render_ci_workflow.py")
        workflow = _read(".github/workflows/ci.yml")
        contract = _read("blueprint/contract.yaml")
        self.assertIn("load_blueprint_contract", renderer)
        self.assertIn("default_branch", renderer)
        self.assertIn("quality-ci-check-sync", _read("scripts/bin/quality/hooks_fast.sh"))
        self.assertIn("branches:", workflow)
        self.assertIn("  push:", workflow)
        self.assertIn("default_branch: main", contract)

    def test_required_files_filter_source_only_paths_for_generated_repo_mode(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            contract_path.write_text(
                _read("blueprint/contract.yaml").replace(
                    "repo_mode: template-source",
                    "repo_mode: generated-consumer",
                    1,
                ),
                encoding="utf-8",
            )
            contract = load_blueprint_contract(contract_path)
            required_files = module._required_files_for_repo_mode(contract)

        self.assertFalse(any(path.startswith("tests/blueprint/") for path in required_files))
        self.assertIn("tests/_shared/helpers.py", required_files)

    def test_cert_manager_values_use_crds_enabled_without_deprecated_key(self) -> None:
        source_values = _read("infra/local/helm/core/cert-manager.values.yaml")
        template_values = _read("scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml")

        def has_crds_enabled_true(content: str) -> bool:
            parent_pattern = re.compile(r"^\s*crds\s*:\s*(?:#[^\n]*)?$")
            enabled_pattern = re.compile(r"^\s*enabled\s*:\s*true\s*(?:#.*)?$")

            lines = content.splitlines()
            for idx, line in enumerate(lines):
                if not parent_pattern.match(line):
                    continue
                parent_indent = len(line) - len(line.lstrip(" "))
                cursor = idx + 1
                while cursor < len(lines):
                    candidate = lines[cursor]
                    stripped = candidate.strip()
                    if not stripped or stripped.startswith("#"):
                        cursor += 1
                        continue
                    candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                    if candidate_indent <= parent_indent:
                        break
                    if enabled_pattern.match(candidate):
                        return True
                    cursor += 1
                return False
            return False

        deprecated_pattern = re.compile(r"(?m)^\s*installCRDs\s*:")

        self.assertNotRegex(source_values, deprecated_pattern)
        self.assertTrue(has_crds_enabled_true(source_values))
        self.assertNotRegex(template_values, deprecated_pattern)
        self.assertTrue(has_crds_enabled_true(template_values))
        self.assertEqual(source_values, template_values)

    def test_validate_contract_rejects_deprecated_cert_manager_values_key(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            cert_manager_values = tmp_root / "infra/local/helm/core/cert-manager.values.yaml"
            cert_manager_values.parent.mkdir(parents=True, exist_ok=True)
            cert_manager_values.write_text("installCRDs: true\n", encoding="utf-8")

            errors = module._validate_core_chart_values_contract(tmp_root)

        self.assertIn(
            "infra/local/helm/core/cert-manager.values.yaml uses deprecated values key 'installCRDs'; use "
            "'crds.enabled' instead",
            errors,
        )

    def test_validate_contract_requires_enabled_under_crds_mapping(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            cert_manager_values = tmp_root / "infra/local/helm/core/cert-manager.values.yaml"
            cert_manager_values.parent.mkdir(parents=True, exist_ok=True)
            cert_manager_values.write_text(
                "crds: # comment only\n"
                "prometheus:\n"
                "  enabled: false\n",
                encoding="utf-8",
            )

            errors = module._validate_core_chart_values_contract(tmp_root)

        self.assertIn(
            "infra/local/helm/core/cert-manager.values.yaml missing required values key mapping: crds.enabled",
            errors,
        )

    def test_keycloak_local_manifest_defaults_to_manual_sync_policy(self) -> None:
        local_core_manifest = _read("infra/gitops/argocd/core/local/keycloak.yaml")
        local_overlay_manifest = _read("infra/gitops/argocd/overlays/local/keycloak.yaml")
        local_overlay_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/keycloak.yaml")
        keycloak_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl")
        infra_bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        keycloak_lib = _read("scripts/lib/infra/keycloak.sh")

        for content in (local_core_manifest, local_overlay_manifest, local_overlay_template):
            self.assertIn("syncPolicy:", content)
            self.assertNotIn("\n    automated:\n", content)
            self.assertIn("\n    syncOptions:\n", content)

        for env_name in ("dev", "stage", "prod"):
            non_local_manifest = _read(f"infra/gitops/argocd/core/{env_name}/keycloak.yaml")
            self.assertIn("\n    automated:\n", non_local_manifest)

        self.assertIn("{{KEYCLOAK_SYNC_AUTOMATED_BLOCK}}", keycloak_template)
        self.assertIn("KEYCLOAK_SYNC_AUTOMATED_BLOCK=$keycloak_sync_automated_block", infra_bootstrap)
        self.assertIn("keycloak_sync_automated_block()", keycloak_lib)

    def test_validate_contract_rejects_local_keycloak_automated_sync(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        required_files = [
            "blueprint/runtime_identity_contract.yaml",
            "docs/platform/consumer/runtime_credentials_eso.md",
            "infra/gitops/platform/base/extensions/kustomization.yaml",
            "infra/gitops/platform/base/security/kustomization.yaml",
            "infra/gitops/platform/base/security/runtime-source-store.yaml",
            "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
            "infra/gitops/platform/base/kustomization.yaml",
            "infra/gitops/argocd/core/local/keycloak.yaml",
            "infra/gitops/argocd/core/dev/keycloak.yaml",
            "infra/gitops/argocd/core/stage/keycloak.yaml",
            "infra/gitops/argocd/core/prod/keycloak.yaml",
            "infra/gitops/argocd/overlays/local/keycloak.yaml",
            "infra/gitops/argocd/overlays/local/kustomization.yaml",
            "infra/gitops/argocd/overlays/dev/kustomization.yaml",
            "infra/gitops/argocd/overlays/stage/kustomization.yaml",
            "infra/gitops/argocd/overlays/prod/kustomization.yaml",
            "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
            "scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl",
            "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/keycloak.yaml",
            "scripts/templates/blueprint/bootstrap/blueprint/runtime_identity_contract.yaml",
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            for relative in required_files:
                destination = tmp_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / relative, destination)

            local_manifest = tmp_root / "infra/gitops/argocd/core/local/keycloak.yaml"
            local_content = local_manifest.read_text(encoding="utf-8")
            local_manifest.write_text(
                local_content.replace(
                    "  syncPolicy:\n    syncOptions:\n",
                    "  syncPolicy:\n    automated:\n      prune: true\n      selfHeal: true\n    syncOptions:\n",
                    1,
                ),
                encoding="utf-8",
            )

            errors = module._validate_runtime_credentials_contract(tmp_root)

        self.assertIn(
            "infra/gitops/argocd/core/local/keycloak.yaml must keep syncPolicy manual (syncPolicy.automated absent) "
            "until runtime credentials are reconciled",
            errors,
        )

    def test_runtime_security_manifests_use_external_secrets_v1(self) -> None:
        runtime_source_store = _read("infra/gitops/platform/base/security/runtime-source-store.yaml")
        runtime_external_secrets = _read("infra/gitops/platform/base/security/runtime-external-secrets-core.yaml")
        template_source_store = _read("scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-source-store.yaml")
        template_external_secrets = _read(
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml"
        )
        runtime_identity_renderer = _read("scripts/lib/infra/runtime_identity_contract.py")

        for content in (
            runtime_source_store,
            runtime_external_secrets,
            template_source_store,
            template_external_secrets,
        ):
            self.assertIn("external-secrets.io/v1", content)
            self.assertNotIn("external-secrets.io/v1beta1", content)

        self.assertIn('EXTERNAL_SECRETS_API_VERSION = "external-secrets.io/v1"', runtime_identity_renderer)
        self.assertNotIn("external-secrets.io/v1beta1", runtime_identity_renderer)

    def test_validate_contract_rejects_external_secrets_v1beta1_runtime_manifest(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        required_files = [
            "blueprint/runtime_identity_contract.yaml",
            "docs/platform/consumer/runtime_credentials_eso.md",
            "infra/gitops/platform/base/extensions/kustomization.yaml",
            "infra/gitops/platform/base/security/kustomization.yaml",
            "infra/gitops/platform/base/security/runtime-source-store.yaml",
            "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
            "infra/gitops/platform/base/kustomization.yaml",
            "infra/gitops/argocd/core/local/keycloak.yaml",
            "infra/gitops/argocd/core/dev/keycloak.yaml",
            "infra/gitops/argocd/core/stage/keycloak.yaml",
            "infra/gitops/argocd/core/prod/keycloak.yaml",
            "infra/gitops/argocd/overlays/local/keycloak.yaml",
            "infra/gitops/argocd/overlays/local/kustomization.yaml",
            "infra/gitops/argocd/overlays/dev/kustomization.yaml",
            "infra/gitops/argocd/overlays/stage/kustomization.yaml",
            "infra/gitops/argocd/overlays/prod/kustomization.yaml",
            "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
            "scripts/lib/infra/runtime_identity_contract.py",
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
            "scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl",
            "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/keycloak.yaml",
            "scripts/templates/blueprint/bootstrap/blueprint/runtime_identity_contract.yaml",
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-source-store.yaml",
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            for relative in required_files:
                destination = tmp_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / relative, destination)

            source_store = tmp_root / "infra/gitops/platform/base/security/runtime-source-store.yaml"
            source_store.write_text(
                source_store.read_text(encoding="utf-8").replace(
                    "external-secrets.io/v1",
                    "external-secrets.io/v1beta1",
                    1,
                ),
                encoding="utf-8",
            )

            errors = module._validate_runtime_credentials_contract(tmp_root)

        self.assertIn(
            "infra/gitops/platform/base/security/runtime-source-store.yaml uses deprecated External Secrets apiVersion "
            "external-secrets.io/v1beta1",
            errors,
        )

    def test_module_wrapper_generator_is_repo_rooted(self) -> None:
        generator = REPO_ROOT / "scripts/lib/blueprint/generate_module_wrapper_skeletons.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "generated"
            result = run(
                [sys.executable, str(generator), "--output-root", str(output_root)],
                cwd=Path(tmpdir),
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue((output_root / "postgres" / "postgres_plan.sh.tmpl").exists())
            self.assertIn("generated", result.stdout)
            self.assertIn("resolve_repo_root", _read("scripts/lib/blueprint/generate_module_wrapper_skeletons.py"))

    def test_module_doc_summary_generator_syncs_source_and_template_docs(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_module_contract_summaries.py"
        result = run([sys.executable, str(generator), "--check"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        postgres_doc = _read("docs/platform/modules/postgres/README.md")
        postgres_template = _read("scripts/templates/blueprint/bootstrap/docs/platform/modules/postgres/README.md")
        self.assertIn("BEGIN GENERATED MODULE CONTRACT SUMMARY", postgres_doc)
        self.assertIn("## Contract Summary", postgres_doc)
        self.assertEqual(postgres_doc, postgres_template)

    def test_runtime_identity_summary_generator_syncs_source_and_template_docs(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_runtime_identity_contract_summary.py"
        result = run([sys.executable, str(generator), "--check"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        source_doc = _read("docs/platform/consumer/runtime_credentials_eso.md")
        template_doc = _read("scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md")
        self.assertIn("BEGIN GENERATED RUNTIME IDENTITY CONTRACT SUMMARY", source_doc)
        self.assertIn("## Contract Summary (Generated)", source_doc)
        self.assertEqual(source_doc, template_doc)

    def test_blueprint_docs_template_sync_checker_is_repo_rooted(self) -> None:
        checker = REPO_ROOT / "scripts/lib/docs/sync_blueprint_template_docs.py"
        result = run([sys.executable, str(checker), "--check"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("resolve_repo_root", _read("scripts/lib/docs/sync_blueprint_template_docs.py"))

    def test_core_targets_generator_uses_make_help(self) -> None:
        generator = _read("scripts/bin/quality/render_core_targets_doc.py")
        self.assertIn('["make", "help"]', generator)
        self.assertIn("--check", generator)

    def test_core_targets_generator_uses_default_module_surface(self) -> None:
        generator = REPO_ROOT / "scripts/bin/quality/render_core_targets_doc.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "core_targets.generated.md"
            result = run(
                [sys.executable, str(generator), "--output", str(output)],
                {"OBSERVABILITY_ENABLED": "true", "WORKFLOWS_ENABLED": "true"},
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            content = output.read_text(encoding="utf-8")

        self.assertIn("`quality-test-pyramid`", content)
        self.assertNotIn("`infra-observability-plan`", content)
        self.assertNotIn("`infra-stackit-workflows-plan`", content)

    def test_docs_linter_validates_governance_links(self) -> None:
        linter = _read("scripts/bin/quality/lint_docs.py")
        self.assertIn("VALID_GOVERNANCE_LINK_BASENAMES", linter)
        self.assertIn("non-canonical governance file reference", linter)

    def test_test_pyramid_contract_tracks_repo_classification(self) -> None:
        contract = _read("scripts/lib/quality/test_pyramid_contract.json")
        self.assertIn('"unit_min_exclusive"', contract)
        self.assertIn('"integration_max_inclusive"', contract)
        self.assertIn('"e2e_max_inclusive"', contract)
        self.assertIn("tests/blueprint/test_contract_stackit_runtime.py", contract)
        self.assertIn("tests/blueprint/test_init_repo_env.py", contract)
        self.assertIn("tests/blueprint/test_upgrade_consumer.py", contract)
        self.assertIn("tests/infra/test_async_message_contracts.py", contract)
        self.assertIn("tests/blueprint/test_optional_runtime_contract_validation.py", contract)
        self.assertIn("tests/infra/test_workload_health_check.py", contract)
        self.assertIn("tests/e2e/test_vertical_slice.py", contract)

    def test_test_pyramid_checker_skips_generated_consumer_repos(self) -> None:
        checker = _read("scripts/bin/quality/check_test_pyramid.py")
        self.assertIn("load_blueprint_contract", checker)
        self.assertIn('repo_mode == "generated-consumer"', checker)
        self.assertIn("[test-pyramid] skipped for generated-consumer repo", checker)

    def test_governance_aggregate_module_uses_load_tests_guard(self) -> None:
        governance_module = _read("tests/blueprint/contract_refactor_governance_cases.py")
        self.assertIn("def load_tests(", governance_module)
        self.assertIn("loader.loadTestsFromTestCase(GovernanceRefactorCases)", governance_module)

    def test_optional_module_wrappers_use_shared_execution_library(self) -> None:
        module_execution = _read("scripts/lib/infra/module_execution.sh")
        fallback_runtime = _read("scripts/lib/infra/fallback_runtime.sh")
        postgres_apply = _read("scripts/bin/infra/postgres_apply.sh")
        rabbitmq_plan = _read("scripts/bin/infra/rabbitmq_plan.sh")
        kms_destroy = _read("scripts/bin/infra/kms_destroy.sh")

        self.assertIn("resolve_optional_module_execution", module_execution)
        self.assertIn("optional_module_execution_mode_total", module_execution)
        self.assertIn("optional_module_values_render_total", fallback_runtime)
        self.assertIn("optional_module_secret_render_total", fallback_runtime)
        self.assertIn('scripts/lib/infra/module_execution.sh', postgres_apply)
        self.assertIn('resolve_optional_module_execution "postgres" "apply"', postgres_apply)
        self.assertNotIn("if is_stackit_profile; then", postgres_apply)
        self.assertIn('resolve_optional_module_execution "rabbitmq" "plan"', rabbitmq_plan)
        self.assertIn('scripts/lib/infra/fallback_runtime.sh', rabbitmq_plan)
        self.assertNotIn("elif is_local_profile; then", rabbitmq_plan)
        self.assertIn('resolve_optional_module_execution "kms" "destroy"', kms_destroy)

    def test_runtime_credentials_reconcile_uses_nounset_safe_contract_iteration(self) -> None:
        reconcile_script = _read("scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh")
        self.assertIn("eso_secret_contract_count()", reconcile_script)
        self.assertIn('for contract_entry in "${ESO_SECRET_CONTRACTS[@]-}"; do', reconcile_script)
        self.assertIn("eso_contract_count=\"$(eso_secret_contract_count)\"", reconcile_script)
        self.assertIn("contracts=$eso_contract_count", reconcile_script)

    def test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports(self) -> None:
        upgrade_wrapper = _read("scripts/bin/blueprint/upgrade_consumer.sh")
        validate_wrapper = _read("scripts/bin/blueprint/upgrade_consumer_validate.sh")
        upgrade_lib = _read("scripts/lib/blueprint/upgrade_consumer.py")
        validate_lib = _read("scripts/lib/blueprint/upgrade_consumer_validate.py")
        runtime_edges = _read("scripts/lib/blueprint/runtime_dependency_edges.py")

        self.assertIn("emit_upgrade_report_metrics()", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_plan_entries_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_apply_status_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_required_manual_action_total", upgrade_wrapper)
        self.assertIn("BLUEPRINT_UPGRADE_ENGINE_MODE", upgrade_wrapper)
        self.assertIn("source-ref", upgrade_wrapper)
        self.assertIn('local plan_report_path="${1:-}"', upgrade_wrapper)
        self.assertIn('local apply_report_path="${2:-}"', upgrade_wrapper)
        self.assertIn("skipping report metrics emission", upgrade_wrapper)
        self.assertIn("upgrade_report_metrics.py", upgrade_wrapper)
        self.assertNotIn("python3 - \"$plan_report_path\" \"$apply_report_path\" <<'PY'", upgrade_wrapper)
        self.assertIn("remote.upstream.url", upgrade_wrapper)
        self.assertIn("remote.origin.url", upgrade_wrapper)
        self.assertIn("emit_validate_report_metrics()", validate_wrapper)
        self.assertIn("blueprint_upgrade_validate_status_total", validate_wrapper)
        self.assertIn("blueprint_upgrade_validate_merge_markers_total", validate_wrapper)
        self.assertIn("blueprint_upgrade_validate_runtime_dependency_missing_total", validate_wrapper)
        self.assertIn("upgrade_report_metrics.py", validate_wrapper)
        self.assertNotIn("python3 - \"$validate_report_path\" <<'PY'", validate_wrapper)
        self.assertIn("from scripts.lib.blueprint.merge_markers import find_merge_markers", upgrade_lib)
        self.assertIn("from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES", upgrade_lib)
        self.assertIn("required_manual_actions", upgrade_lib)
        self.assertIn("from scripts.lib.blueprint.merge_markers import find_merge_markers", validate_lib)
        self.assertIn("from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES", validate_lib)
        self.assertIn("runtime_dependency_edge_check", validate_lib)
        self.assertIn("RUNTIME_DEPENDENCY_EDGES", runtime_edges)


if __name__ == "__main__":
    unittest.main()
