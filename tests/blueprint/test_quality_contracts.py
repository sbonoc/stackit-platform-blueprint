from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

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
        self.assertIn("quality-docs-lint", make_template)
        self.assertIn("quality-docs-sync-blueprint-template", make_template)
        self.assertIn("quality-docs-check-blueprint-template-sync", make_template)
        self.assertIn("quality-docs-sync-core-targets", make_template)
        self.assertIn("quality-docs-check-core-targets-sync", make_template)
        self.assertIn("quality-docs-sync-contract-metadata", make_template)
        self.assertIn("quality-docs-check-contract-metadata-sync", make_template)
        self.assertIn("quality-docs-sync-runtime-identity-summary", make_template)
        self.assertIn("quality-docs-check-runtime-identity-summary-sync", make_template)
        self.assertIn("quality-docs-sync-module-contract-summaries", make_template)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", make_template)
        self.assertIn("quality-test-pyramid", make_template)

    def test_generated_makefile_exposes_quality_docs_targets(self) -> None:
        generated_make = _read("make/blueprint.generated.mk")
        self.assertIn("quality-hooks-fast", generated_make)
        self.assertIn("quality-hooks-strict", generated_make)
        self.assertIn("quality-docs-lint", generated_make)
        self.assertIn("quality-docs-sync-blueprint-template", generated_make)
        self.assertIn("quality-docs-check-blueprint-template-sync", generated_make)
        self.assertIn("quality-docs-sync-core-targets", generated_make)
        self.assertIn("quality-docs-check-core-targets-sync", generated_make)
        self.assertIn("quality-docs-sync-contract-metadata", generated_make)
        self.assertIn("quality-docs-check-contract-metadata-sync", generated_make)
        self.assertIn("quality-docs-sync-runtime-identity-summary", generated_make)
        self.assertIn("quality-docs-check-runtime-identity-summary-sync", generated_make)
        self.assertIn("quality-docs-sync-module-contract-summaries", generated_make)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", generated_make)
        self.assertIn("quality-test-pyramid", generated_make)

    def test_docs_generator_supports_check_mode(self) -> None:
        generator = _read("scripts/lib/docs/generate_contract_docs.py")
        self.assertIn("--check", generator)
        self.assertNotIn("Generated at:", generator)
        self.assertIn("resolve_repo_root", generator)

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
        self.assertIn("tests/blueprint/test_optional_runtime_contract_validation.py", contract)
        self.assertIn("tests/infra/test_workload_health_check.py", contract)
        self.assertIn("tests/e2e/test_vertical_slice.py", contract)

    def test_test_pyramid_checker_skips_generated_consumer_repos(self) -> None:
        checker = _read("scripts/bin/quality/check_test_pyramid.py")
        self.assertIn("load_blueprint_contract", checker)
        self.assertIn('repo_mode == "generated-consumer"', checker)
        self.assertIn("[test-pyramid] skipped for generated-consumer repo", checker)

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

    def test_upgrade_workflow_wrappers_emit_metrics_and_parse_reports(self) -> None:
        upgrade_wrapper = _read("scripts/bin/blueprint/upgrade_consumer.sh")
        validate_wrapper = _read("scripts/bin/blueprint/upgrade_consumer_validate.sh")
        upgrade_lib = _read("scripts/lib/blueprint/upgrade_consumer.py")
        validate_lib = _read("scripts/lib/blueprint/upgrade_consumer_validate.py")
        runtime_edges = _read("scripts/lib/blueprint/runtime_dependency_edges.py")

        self.assertIn("emit_upgrade_report_metrics()", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_plan_entries_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_apply_status_total", upgrade_wrapper)
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
        self.assertIn("from scripts.lib.blueprint.merge_markers import find_merge_markers", validate_lib)
        self.assertIn("from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES", validate_lib)
        self.assertIn("runtime_dependency_edge_check", validate_lib)
        self.assertIn("RUNTIME_DEPENDENCY_EDGES", runtime_edges)


if __name__ == "__main__":
    unittest.main()
