from __future__ import annotations

import importlib.util
import json
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


def _contract_text_for_repo_mode(repo_mode: str) -> str:
    return _read("blueprint/contract.yaml").replace("repo_mode: template-source", f"repo_mode: {repo_mode}", 1)


class QualityContractsTests(unittest.TestCase):
    def test_root_bootstrap_delegates_to_shell_bootstrap(self) -> None:
        bootstrap = _read("scripts/lib/bootstrap.sh")
        self.assertIn('source "$SCRIPT_LIB_DIR/shell/bootstrap.sh"', bootstrap)

    def test_root_semver_delegates_to_quality_semver(self) -> None:
        semver = _read("scripts/lib/semver.sh")
        self.assertIn('scripts/lib/quality/semver.sh', semver)

    def test_make_template_exposes_quality_docs_targets(self) -> None:
        make_template = _read("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl")
        self.assertIn("blueprint-install-codex-skill-sdd-step01-intake", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step02-resolve-questions", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step03-spec-complete", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step04-plan-slicer", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step05-implement", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step06-document-sync", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-step07-pr-packager", make_template)
        self.assertIn("blueprint-install-codex-skill-sdd-traceability-keeper", make_template)
        self.assertIn("quality-hooks-fast", make_template)
        self.assertIn("quality-hooks-strict", make_template)
        self.assertIn("quality-infra-shell-source-graph-check", make_template)
        self.assertIn("spec-scaffold", make_template)
        self.assertIn("spec-impact", make_template)
        self.assertIn("spec-evidence-manifest", make_template)
        self.assertIn("spec-context-pack", make_template)
        self.assertIn("spec-pr-context", make_template)
        self.assertIn("quality-sdd-check", make_template)
        self.assertIn("quality-sdd-sync-all", make_template)
        self.assertIn("quality-sdd-check-all", make_template)
        self.assertIn("quality-hardening-review", make_template)
        self.assertIn("infra-port-forward-start", make_template)
        self.assertIn("infra-port-forward-stop", make_template)
        self.assertIn("infra-port-forward-cleanup", make_template)
        self.assertIn("quality-ci-sync", make_template)
        self.assertIn("quality-ci-check-sync", make_template)
        self.assertIn("quality-docs-lint", make_template)
        self.assertIn("quality-docs-sync-all", make_template)
        self.assertIn("quality-docs-check-changed", make_template)
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
        self.assertIn(
            "@python3 scripts/lib/docs/orchestrate_sync.py --mode check --changed-only\n\t@python3 scripts/bin/quality/check_test_pyramid.py",
            make_template,
        )
        self.assertIn("infra-contract-test-fast", make_template)

    def test_generated_makefile_exposes_quality_docs_targets(self) -> None:
        generated_make = _read("make/blueprint.generated.mk")
        self.assertIn("blueprint-install-codex-skill-sdd-step01-intake", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step02-resolve-questions", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step03-spec-complete", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step04-plan-slicer", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step05-implement", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step06-document-sync", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-step07-pr-packager", generated_make)
        self.assertIn("blueprint-install-codex-skill-sdd-traceability-keeper", generated_make)
        self.assertIn("quality-hooks-fast", generated_make)
        self.assertIn("quality-hooks-strict", generated_make)
        self.assertIn("quality-infra-shell-source-graph-check", generated_make)
        self.assertIn("spec-scaffold", generated_make)
        self.assertIn("spec-impact", generated_make)
        self.assertIn("spec-evidence-manifest", generated_make)
        self.assertIn("spec-context-pack", generated_make)
        self.assertIn("spec-pr-context", generated_make)
        self.assertIn("quality-sdd-check", generated_make)
        self.assertIn("quality-sdd-sync-all", generated_make)
        self.assertIn("quality-sdd-check-all", generated_make)
        self.assertIn("quality-hardening-review", generated_make)
        self.assertIn("infra-port-forward-start", generated_make)
        self.assertIn("infra-port-forward-stop", generated_make)
        self.assertIn("infra-port-forward-cleanup", generated_make)
        self.assertIn("quality-ci-sync", generated_make)
        self.assertIn("quality-ci-check-sync", generated_make)
        self.assertIn("quality-docs-lint", generated_make)
        self.assertIn("quality-docs-sync-all", generated_make)
        self.assertIn("quality-docs-check-changed", generated_make)
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
        self.assertIn(
            "@python3 scripts/lib/docs/orchestrate_sync.py --mode check --changed-only\n\t@python3 scripts/bin/quality/check_test_pyramid.py",
            generated_make,
        )
        self.assertIn("infra-contract-test-fast", generated_make)

    def test_sdd_plan_and_tasks_templates_include_local_smoke_and_positive_path_gates(self) -> None:
        blueprint_plan = _read(".spec-kit/templates/blueprint/plan.md")
        consumer_plan = _read(".spec-kit/templates/consumer/plan.md")
        blueprint_tasks = _read(".spec-kit/templates/blueprint/tasks.md")
        consumer_tasks = _read(".spec-kit/templates/consumer/tasks.md")
        consumer_init_plan_template = _read("scripts/templates/consumer/init/.spec-kit/templates/consumer/plan.md.tmpl")
        consumer_init_tasks_template = _read(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/tasks.md.tmpl"
        )

        expected_plan_markers = (
            "Positive-path filter/transform test gate",
            "Empty-result-only assertions MUST NOT satisfy this gate.",
            "Finding-to-test translation gate",
            "failing automated test first",
            "Local smoke gate (HTTP route/filter changes)",
            "Endpoint | Method | Auth | Result",
        )
        expected_tasks_markers = (
            "T-103 For any new or modified filter/payload-transform route",
            "T-104 Translate any reproducible pre-PR smoke/`curl`/deterministic-check finding",
            "capture evidence in `pr_context.md`",
        )

        for marker in expected_plan_markers:
            self.assertIn(marker, blueprint_plan)
            self.assertIn(marker, consumer_plan)
            self.assertIn(marker, consumer_init_plan_template)

        for marker in expected_tasks_markers:
            self.assertIn(marker, blueprint_tasks)
            self.assertIn(marker, consumer_tasks)
            self.assertIn(marker, consumer_init_tasks_template)

    def test_sdd_control_catalog_includes_local_smoke_and_positive_path_controls(self) -> None:
        catalog_payload = json.loads(_read(".spec-kit/control-catalog.json"))
        self.assertIsInstance(catalog_payload, dict)
        controls = catalog_payload.get("controls", [])
        self.assertIsInstance(controls, list)

        controls_by_id = {str(item.get("id", "")).strip(): item for item in controls if isinstance(item, dict)}
        self.assertIn("SDD-C-022", controls_by_id)
        self.assertIn("SDD-C-023", controls_by_id)
        self.assertIn("SDD-C-024", controls_by_id)

        smoke_control = controls_by_id["SDD-C-022"]
        self.assertIn("local smoke gate", str(smoke_control.get("normative_control", "")).lower())
        self.assertIn("pr_context", str(smoke_control.get("normative_control", "")))

        positive_path_control = controls_by_id["SDD-C-023"]
        self.assertIn("positive-path", str(positive_path_control.get("normative_control", "")).lower())
        self.assertIn("empty-result-only", str(positive_path_control.get("normative_control", "")).lower())

        translation_control = controls_by_id["SDD-C-024"]
        self.assertIn("failing automated regression test first", str(translation_control.get("normative_control", "")).lower())
        self.assertIn("deterministic exceptions", str(translation_control.get("normative_control", "")).lower())

        rendered_catalog = _read(".spec-kit/control-catalog.md")
        self.assertIn("SDD-C-022", rendered_catalog)
        self.assertIn("SDD-C-023", rendered_catalog)
        self.assertIn("SDD-C-024", rendered_catalog)

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
        self.assertIn("quality-infra-shell-source-graph-check", _read("scripts/bin/quality/hooks_fast.sh"))
        self.assertIn("quality-sdd-check-all", _read("scripts/bin/quality/hooks_fast.sh"))
        self.assertIn("quality-docs-check-changed", _read("scripts/bin/quality/hooks_fast.sh"))
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

    def test_validate_contract_rejects_scripts_lib_importing_scripts_bin(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            violating_file = tmp_root / "scripts/lib/example/violating.py"
            violating_file.parent.mkdir(parents=True, exist_ok=True)
            violating_file.write_text("from scripts.bin.infra import validate\n", encoding="utf-8")

            errors = module._validate_python_import_boundaries(tmp_root)

        self.assertTrue(
            any("must not import execution-layer module scripts.bin.infra" in error for error in errors),
            msg="\n".join(errors),
        )

    def test_validate_contract_allows_scripts_lib_internal_imports(self) -> None:
        validate_script = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
        spec = importlib.util.spec_from_file_location("validate_contract_module", validate_script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            compliant_file = tmp_root / "scripts/lib/example/compliant.py"
            compliant_file.parent.mkdir(parents=True, exist_ok=True)
            compliant_file.write_text(
                "from scripts.lib.blueprint.cli_support import resolve_repo_root\n",
                encoding="utf-8",
            )

            errors = module._validate_python_import_boundaries(tmp_root)

        self.assertEqual(errors, [])

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
            "scripts/bin/platform/auth/runtime_identity_doctor.sh",
            "scripts/lib/platform/auth/runtime_identity_doctor_json.py",
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
            "scripts/bin/platform/auth/runtime_identity_doctor.sh",
            "scripts/lib/platform/auth/runtime_identity_doctor_json.py",
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

    def test_module_doc_summary_generator_generated_consumer_skips_template_updates(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_module_contract_summaries.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            modules_root = repo_root / "blueprint/modules"
            docs_modules_root = repo_root / "docs/platform/modules"
            template_postgres = repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/modules/postgres/README.md"

            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(_contract_text_for_repo_mode("generated-consumer"), encoding="utf-8")
            shutil.copytree(REPO_ROOT / "blueprint/modules", modules_root)
            shutil.copytree(REPO_ROOT / "docs/platform/modules", docs_modules_root)

            stale_template = "stale template copy that generated-consumer sync must ignore\n"
            template_postgres.parent.mkdir(parents=True, exist_ok=True)
            template_postgres.write_text(stale_template, encoding="utf-8")

            result = run([sys.executable, str(generator), "--repo-root", str(repo_root)])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(template_postgres.read_text(encoding="utf-8"), stale_template)

    def test_runtime_identity_summary_generator_syncs_source_and_template_docs(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_runtime_identity_contract_summary.py"
        result = run([sys.executable, str(generator), "--check"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        source_doc = _read("docs/platform/consumer/runtime_credentials_eso.md")
        template_doc = _read("scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md")
        self.assertIn("BEGIN GENERATED RUNTIME IDENTITY CONTRACT SUMMARY", source_doc)
        self.assertIn("## Contract Summary (Generated)", source_doc)
        self.assertEqual(source_doc, template_doc)

    def test_runtime_identity_summary_generator_generated_consumer_skips_template_updates(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_runtime_identity_contract_summary.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            runtime_contract = repo_root / "blueprint/runtime_identity_contract.yaml"
            source_doc = repo_root / "docs/platform/consumer/runtime_credentials_eso.md"
            template_doc = repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md"

            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(_contract_text_for_repo_mode("generated-consumer"), encoding="utf-8")
            runtime_contract.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / "blueprint/runtime_identity_contract.yaml", runtime_contract)
            source_doc.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / "docs/platform/consumer/runtime_credentials_eso.md", source_doc)

            stale_template = "stale template copy that generated-consumer sync must ignore\n"
            template_doc.parent.mkdir(parents=True, exist_ok=True)
            template_doc.write_text(stale_template, encoding="utf-8")

            result = run([sys.executable, str(generator), "--repo-root", str(repo_root)])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(template_doc.read_text(encoding="utf-8"), stale_template)

    def test_docs_repo_mode_helper_resolves_mode_specific_doc_paths(self) -> None:
        from scripts.lib.docs.repo_mode import resolve_docs_paths_for_context, resolve_docs_repo_context

        source_doc = Path("docs/platform/consumer/runtime_credentials_eso.md")
        template_doc = Path("scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md")

        with tempfile.TemporaryDirectory() as tmpdir:
            generated_repo = Path(tmpdir) / "generated-consumer"
            generated_contract = generated_repo / "blueprint/contract.yaml"
            generated_contract.parent.mkdir(parents=True, exist_ok=True)
            generated_contract.write_text(_contract_text_for_repo_mode("generated-consumer"), encoding="utf-8")

            generated_context = resolve_docs_repo_context(generated_repo)
            self.assertEqual(generated_context.repo_mode, "generated-consumer")
            self.assertFalse(generated_context.template_sync_enabled)
            self.assertEqual(
                resolve_docs_paths_for_context(
                    context=generated_context,
                    source_path=source_doc,
                    template_path=template_doc,
                ),
                (source_doc,),
            )

            source_repo = Path(tmpdir) / "template-source"
            source_contract = source_repo / "blueprint/contract.yaml"
            source_contract.parent.mkdir(parents=True, exist_ok=True)
            source_contract.write_text(_contract_text_for_repo_mode("template-source"), encoding="utf-8")

            source_context = resolve_docs_repo_context(source_repo)
            self.assertEqual(source_context.repo_mode, "template-source")
            self.assertTrue(source_context.template_sync_enabled)
            self.assertEqual(
                resolve_docs_paths_for_context(
                    context=source_context,
                    source_path=source_doc,
                    template_path=template_doc,
                ),
                (source_doc, template_doc),
            )

    def test_docs_repo_mode_helper_rejects_unsupported_repo_mode(self) -> None:
        from scripts.lib.docs.repo_mode import resolve_docs_repo_context

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(
                _read("blueprint/contract.yaml").replace("repo_mode: template-source", "repo_mode: invalid-mode", 1),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "spec.repository.repo_mode") as exc:
                resolve_docs_repo_context(repo_root)
            self.assertIn("template-source", str(exc.exception))
            self.assertIn("generated-consumer", str(exc.exception))

    def test_platform_seed_sync_rejects_non_repo_relative_contract_roots(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_platform_seed_docs.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_text = _contract_text_for_repo_mode("generated-consumer")
            contract_path.write_text(
                contract_text.replace("root: docs/platform", "root: ../outside-platform", 1),
                encoding="utf-8",
            )

            result = run([sys.executable, str(generator), "--repo-root", str(repo_root), "--check"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("docs_contract.platform_docs.root must not contain parent-directory traversal", result.stderr)

    def test_platform_seed_sync_rejects_required_seed_file_traversal(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_platform_seed_docs.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_text = _contract_text_for_repo_mode("generated-consumer")
            modified_contract_text = contract_text.replace(
                "      required_seed_files:\n        - docs/platform/consumer/first_30_minutes.md",
                "      required_seed_files:\n        - docs/platform/../outside.md",
                1,
            )
            self.assertIn("docs/platform/../outside.md", modified_contract_text)
            contract_path.write_text(
                modified_contract_text,
                encoding="utf-8",
            )

            result = run([sys.executable, str(generator), "--repo-root", str(repo_root), "--check"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required_seed_files entries must not contain parent-directory traversal", result.stderr)

    def test_platform_seed_sync_generated_consumer_moves_orphan_template_docs(self) -> None:
        generator = REPO_ROOT / "scripts/lib/docs/sync_platform_seed_docs.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            source_root = repo_root / "docs/platform"
            template_root = repo_root / "scripts/templates/blueprint/bootstrap/docs/platform"

            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(_contract_text_for_repo_mode("generated-consumer"), encoding="utf-8")

            quickstart_source = source_root / "consumer/quickstart.md"
            quickstart_source.parent.mkdir(parents=True, exist_ok=True)
            quickstart_source.write_text("# quickstart source\n", encoding="utf-8")
            quickstart_template = template_root / "consumer/quickstart.md"
            quickstart_template.parent.mkdir(parents=True, exist_ok=True)
            quickstart_template.write_text("# quickstart template seed\n", encoding="utf-8")

            orphan_missing_source_template = template_root / "consumer/custom-guide.md"
            orphan_missing_source_template.write_text("# custom guide from template orphan\n", encoding="utf-8")
            orphan_existing_source_template = template_root / "consumer/manual-notes.md"
            orphan_existing_source_template.write_text("# duplicated manual notes copy\n", encoding="utf-8")
            orphan_directory_template = template_root / "consumer/folderized-guide"
            orphan_directory_template.write_text("# stale template file that must be removed\n", encoding="utf-8")

            existing_source = source_root / "consumer/manual-notes.md"
            existing_source.parent.mkdir(parents=True, exist_ok=True)
            existing_source.write_text("# canonical source manual notes\n", encoding="utf-8")
            existing_directory_source = source_root / "consumer/folderized-guide"
            existing_directory_source.mkdir(parents=True, exist_ok=True)
            (existing_directory_source / "README.md").write_text("# consumer-owned directory\n", encoding="utf-8")

            result = run([sys.executable, str(generator), "--repo-root", str(repo_root)])
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            moved_source = source_root / "consumer/custom-guide.md"
            self.assertTrue(moved_source.exists())
            self.assertEqual(
                moved_source.read_text(encoding="utf-8"),
                "# custom guide from template orphan\n",
            )
            self.assertFalse(orphan_missing_source_template.exists())
            self.assertFalse(orphan_existing_source_template.exists())
            self.assertFalse(orphan_directory_template.exists())
            self.assertTrue(existing_directory_source.is_dir())
            self.assertTrue(quickstart_template.exists(), msg="required seed template file must be preserved")

    def test_platform_seed_check_generated_consumer_reports_orphan_template_docs(self) -> None:
        checker = REPO_ROOT / "scripts/lib/docs/sync_platform_seed_docs.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            source_root = repo_root / "docs/platform"
            template_root = repo_root / "scripts/templates/blueprint/bootstrap/docs/platform"

            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(_contract_text_for_repo_mode("generated-consumer"), encoding="utf-8")
            (source_root / "consumer").mkdir(parents=True, exist_ok=True)
            (template_root / "consumer").mkdir(parents=True, exist_ok=True)

            (source_root / "consumer/quickstart.md").write_text("# quickstart source\n", encoding="utf-8")
            (template_root / "consumer/quickstart.md").write_text("# quickstart template seed\n", encoding="utf-8")
            orphan_template = template_root / "consumer/custom-guide.md"
            orphan_template.write_text("# orphan\n", encoding="utf-8")

            result = run([sys.executable, str(checker), "--repo-root", str(repo_root), "--check"])
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("generated-consumer template orphan", result.stderr)
            self.assertTrue(orphan_template.exists(), msg="check mode must not mutate files")

    def test_blueprint_docs_template_sync_checker_is_repo_rooted(self) -> None:
        checker = REPO_ROOT / "scripts/lib/docs/sync_blueprint_template_docs.py"
        result = run([sys.executable, str(checker), "--check"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("resolve_repo_root", _read("scripts/lib/docs/sync_blueprint_template_docs.py"))

    def test_prune_globs_must_be_documented_in_ownership_matrix_source_only_rows(self) -> None:
        from scripts.lib.blueprint.contract_schema import load_blueprint_contract
        from scripts.lib.blueprint.contract_validators.docs_sync import validate_source_artifact_prune_globs_documented

        contract_text = _read("blueprint/contract.yaml")
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "blueprint/contract.yaml"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(contract_text, encoding="utf-8")

            ownership_path = repo_root / "docs/blueprint/governance/ownership_matrix.md"
            ownership_path.parent.mkdir(parents=True, exist_ok=True)
            ownership_path.write_text(
                (
                    "| Area | Ownership | Edit Mode | Notes |\n"
                    "|---|---|---|---|\n"
                    "| `docs/blueprint/architecture/decisions/ADR-*.md` | Blueprint source only | Controlled | test |\n"
                ),
                encoding="utf-8",
            )

            contract = load_blueprint_contract(contract_path)
            errors = validate_source_artifact_prune_globs_documented(repo_root, contract)
            self.assertTrue(
                any("source_artifact_prune_globs_on_init pattern must be documented" in error for error in errors),
                msg=f"expected ownership matrix documentation error, got: {errors}",
            )

            ownership_path.write_text(
                (
                    "| Area | Ownership | Edit Mode | Notes |\n"
                    "|---|---|---|---|\n"
                    "| `foo/specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.bak`, "
                    "`docs/blueprint/architecture/decisions/ADR-*.md` | "
                    "Blueprint source only | Controlled | test |\n"
                ),
                encoding="utf-8",
            )
            errors = validate_source_artifact_prune_globs_documented(repo_root, contract)
            self.assertTrue(
                any("source_artifact_prune_globs_on_init pattern must be documented" in error for error in errors),
                msg=f"expected exact-token ownership matrix documentation error, got: {errors}",
            )

            ownership_path.write_text(
                (
                    "| Area | Ownership | Edit Mode | Notes |\n"
                    "|---|---|---|---|\n"
                    "| `specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*`, "
                    "`docs/blueprint/architecture/decisions/ADR-*.md` | "
                    "Blueprint source only | Controlled | test |\n"
                ),
                encoding="utf-8",
            )
            errors = validate_source_artifact_prune_globs_documented(repo_root, contract)
            self.assertEqual(errors, [])

    def test_blueprint_docs_template_sync_prunes_source_only_docs(self) -> None:
        checker = REPO_ROOT / "scripts/lib/docs/sync_blueprint_template_docs.py"
        spec = importlib.util.spec_from_file_location("sync_blueprint_template_docs_module", checker)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_root = repo_root / "docs"
            source_blueprint_root = docs_root / "blueprint"
            template_blueprint_root = repo_root / "scripts/templates/blueprint/bootstrap/docs/blueprint"
            template_docs_root = repo_root / "scripts/templates/blueprint/bootstrap/docs"
            contract_path = repo_root / "blueprint/contract.yaml"

            (docs_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
            (docs_root / "README.md").write_text("# docs index\n", encoding="utf-8")
            (template_docs_root / "README.md").parent.mkdir(parents=True, exist_ok=True)
            (template_docs_root / "README.md").write_text("# stale docs index\n", encoding="utf-8")
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text((REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"), encoding="utf-8")

            allowlist = module.resolve_blueprint_docs_template_allowlist(repo_root)
            for relative in allowlist:
                source_path = source_blueprint_root / relative
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_text(f"# source {relative}\n", encoding="utf-8")
                template_path = template_blueprint_root / relative
                template_path.parent.mkdir(parents=True, exist_ok=True)
                template_path.write_text(f"# stale {relative}\n", encoding="utf-8")

            source_only_paths = (
                "architecture/decisions/ADR-20260417-source-only.md",
                "governance/non_allowlisted_source_only.md",
            )
            for relative in source_only_paths:
                source_path = source_blueprint_root / relative
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_text(f"# source-only {relative}\n", encoding="utf-8")
                template_path = template_blueprint_root / relative
                template_path.parent.mkdir(parents=True, exist_ok=True)
                template_path.write_text(f"# stale source-only {relative}\n", encoding="utf-8")

            result = run(
                [sys.executable, str(checker), "--repo-root", str(repo_root)],
                cwd=repo_root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            for relative in allowlist:
                self.assertEqual(
                    (source_blueprint_root / relative).read_text(encoding="utf-8"),
                    (template_blueprint_root / relative).read_text(encoding="utf-8"),
                )

            self.assertFalse((template_blueprint_root / source_only_paths[0]).exists())
            self.assertFalse((template_blueprint_root / source_only_paths[1]).exists())

    def test_init_repo_source_artifact_prune_globs_apply_only_on_initial_mode(self) -> None:
        helper = REPO_ROOT / "scripts/lib/blueprint/init_repo_contract.py"
        spec = importlib.util.spec_from_file_location("init_repo_contract_module", helper)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        prune_globs = [
            "specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*",
            "docs/blueprint/architecture/decisions/ADR-*.md",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            specs_path = repo_root / "specs/2026-04-17-blueprint-source-only"
            adr_path = repo_root / "docs/blueprint/architecture/decisions/ADR-20260417-source-only.md"

            specs_path.mkdir(parents=True, exist_ok=True)
            (specs_path / "spec.md").write_text("source-only spec", encoding="utf-8")
            adr_path.parent.mkdir(parents=True, exist_ok=True)
            adr_path.write_text("source-only adr", encoding="utf-8")

            module.prune_source_artifacts_on_initial_init(
                repo_root=repo_root,
                summary=module.ChangeSummary("test"),
                dry_run=False,
                repo_mode="template-source",
                mode_from="template-source",
                prune_globs=prune_globs,
            )

            self.assertFalse(specs_path.exists())
            self.assertFalse(adr_path.exists())

            specs_path.mkdir(parents=True, exist_ok=True)
            (specs_path / "spec.md").write_text("consumer-owned spec", encoding="utf-8")
            adr_path.parent.mkdir(parents=True, exist_ok=True)
            adr_path.write_text("consumer-owned adr", encoding="utf-8")

            module.prune_source_artifacts_on_initial_init(
                repo_root=repo_root,
                summary=module.ChangeSummary("test"),
                dry_run=False,
                repo_mode="generated-consumer",
                mode_from="template-source",
                prune_globs=prune_globs,
            )

            self.assertTrue(specs_path.exists())
            self.assertTrue(adr_path.exists())

    def test_init_repo_source_artifact_prune_blocks_unsafe_patterns_and_out_of_root_symlinks(self) -> None:
        helper = REPO_ROOT / "scripts/lib/blueprint/init_repo_contract.py"
        spec = importlib.util.spec_from_file_location("init_repo_contract_module", helper)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            repo_root = tmp_root / "repo"
            outside_root = tmp_root / "outside"
            repo_root.mkdir(parents=True, exist_ok=True)
            outside_root.mkdir(parents=True, exist_ok=True)

            inside_keep = repo_root / "keep.txt"
            inside_keep.write_text("keep", encoding="utf-8")
            outside_file = outside_root / "escape.txt"
            outside_file.write_text("outside", encoding="utf-8")

            symlink_to_outside = repo_root / "escape-link"
            symlink_to_outside.symlink_to(outside_root, target_is_directory=True)

            module.prune_source_artifacts_on_initial_init(
                repo_root=repo_root,
                summary=module.ChangeSummary("test"),
                dry_run=False,
                repo_mode="template-source",
                mode_from="template-source",
                prune_globs=[
                    "../outside/*",
                    "..\\outside\\*",
                    str(outside_root / "*"),
                    "escape-link",
                ],
            )

            self.assertTrue(inside_keep.exists())
            self.assertTrue(outside_root.exists())
            self.assertTrue(outside_file.exists())
            self.assertTrue(symlink_to_outside.exists())

    def test_core_targets_generator_uses_make_help(self) -> None:
        generator = _read("scripts/bin/quality/render_core_targets_doc.py")
        self.assertIn('["make", "help"]', generator)
        self.assertIn("--check", generator)

    def test_core_targets_generator_escapes_mdx_sensitive_table_tokens(self) -> None:
        generator = REPO_ROOT / "scripts/bin/quality/render_core_targets_doc.py"
        spec = importlib.util.spec_from_file_location("render_core_targets_doc_module", generator)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        rendered = module._render_markdown(
            [("spec-scaffold", "set SPEC_BRANCH=<name>|A&B for scaffold contract checks")]
        )

        self.assertIn("SPEC_BRANCH=&lt;name&gt;\\|A&amp;B", rendered)
        self.assertNotIn("SPEC_BRANCH=<name>", rendered)

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
        self.assertIn("tests/docs/test_orchestrate_sync.py", contract)
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
        opensearch_apply = _read("scripts/bin/infra/opensearch_apply.sh")
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
        self.assertIn('scripts/lib/infra/module_execution.sh', opensearch_apply)
        self.assertIn('resolve_optional_module_execution "opensearch" "apply"', opensearch_apply)
        self.assertNotIn("if is_stackit_profile; then", opensearch_apply)
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
        postcheck_wrapper = _read("scripts/bin/blueprint/upgrade_consumer_postcheck.sh")
        upgrade_lib = _read("scripts/lib/blueprint/upgrade_consumer.py")
        postcheck_lib = _read("scripts/lib/blueprint/upgrade_consumer_postcheck.py")
        reconcile_lib = _read("scripts/lib/blueprint/upgrade_reconcile_report.py")
        validate_lib = _read("scripts/lib/blueprint/upgrade_consumer_validate.py")
        runtime_edges = _read("scripts/lib/blueprint/runtime_dependency_edges.py")

        self.assertIn("emit_upgrade_report_metrics()", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_plan_entries_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_apply_status_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_required_manual_action_total", upgrade_wrapper)
        self.assertIn("blueprint_upgrade_reconcile_bucket_total", upgrade_wrapper)
        self.assertIn("BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH", upgrade_wrapper)
        self.assertIn("BLUEPRINT_UPGRADE_ENGINE_MODE", upgrade_wrapper)
        self.assertIn("source-ref", upgrade_wrapper)
        self.assertIn('local plan_report_path="${1:-}"', upgrade_wrapper)
        self.assertIn('local apply_report_path="${2:-}"', upgrade_wrapper)
        self.assertIn('local reconcile_report_path="${3:-}"', upgrade_wrapper)
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
        self.assertIn("emit_postcheck_report_metrics()", postcheck_wrapper)
        self.assertIn("blueprint_upgrade_postcheck_status_total", postcheck_wrapper)
        self.assertIn("upgrade_consumer_postcheck.py", postcheck_wrapper)
        self.assertIn("from scripts.lib.blueprint.merge_markers import find_merge_markers", upgrade_lib)
        self.assertIn("from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES", upgrade_lib)
        self.assertIn("build_upgrade_reconcile_report", upgrade_lib)
        self.assertIn("required_manual_actions", upgrade_lib)
        self.assertIn("from scripts.lib.blueprint.merge_markers import find_merge_markers", validate_lib)
        self.assertIn("from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES", validate_lib)
        self.assertIn("find_merge_markers(repo_root)", postcheck_lib)
        self.assertIn("_docs_hook_targets_for_repo_mode", postcheck_lib)
        self.assertIn("RECONCILE_BUCKET_ORDER", reconcile_lib)
        self.assertIn("build_merge_risk_classification", reconcile_lib)
        self.assertIn("runtime_dependency_edge_check", validate_lib)
        self.assertIn("RUNTIME_DEPENDENCY_EDGES", runtime_edges)

    def test_required_files_excludes_consumer_seeded_paths_for_generated_repo_mode(self) -> None:
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

        # README.md is in both required_files and consumer_seeded_paths.
        # In generated-consumer mode it must be excluded from disk-presence checks
        # so that a consumer who has taken ownership can delete it without
        # triggering a validate_contract failure.
        self.assertNotIn("README.md", required_files)
        self.assertNotIn("AGENTS.md", required_files)


    def test_render_ci_includes_permissions_block(self) -> None:
        """FR-015/FR-016: generated ci.yml must contain a workflow-level permissions block with contents: read."""
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location(
            "render_ci_workflow",
            REPO_ROOT / "scripts/lib/quality/render_ci_workflow.py",
        )
        module = _ilu.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        rendered = module._render_ci("main")

        # FR-015: permissions block must be present
        self.assertIn("permissions:", rendered, msg="generated ci.yml must contain a workflow-level permissions: block")
        # FR-016: contents: read must be set
        self.assertIn("contents: read", rendered, msg="permissions block must set contents: read")

        # FR-015: permissions block must appear after 'on:' and before 'jobs:'
        on_pos = rendered.index("on:\n")
        perm_pos = rendered.index("permissions:")
        jobs_pos = rendered.index("jobs:\n")
        self.assertGreater(perm_pos, on_pos, msg="permissions block must appear after on: block")
        self.assertLess(perm_pos, jobs_pos, msg="permissions block must appear before jobs: section")

    def test_ci_workflow_file_contains_permissions_block(self) -> None:
        """FR-015/FR-016: committed .github/workflows/ci.yml must contain the permissions block."""
        workflow = _read(".github/workflows/ci.yml")
        self.assertIn("permissions:", workflow, msg=".github/workflows/ci.yml must contain permissions: block")
        self.assertIn("contents: read", workflow, msg=".github/workflows/ci.yml must set contents: read")


if __name__ == "__main__":
    unittest.main()
