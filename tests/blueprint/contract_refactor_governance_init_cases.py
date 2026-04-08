from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class GovernanceInitRepoCases(RefactorContractBase):
    def test_blueprint_template_init_assets_exist(self) -> None:
        init_script = _read("scripts/bin/blueprint/init_repo.sh")
        init_interactive_script = _read("scripts/bin/blueprint/init_repo_interactive.sh")
        init_python = _read("scripts/lib/blueprint/init_repo.py")
        smoke_script = _read("scripts/bin/blueprint/template_smoke.sh")
        placeholder_script = _read("scripts/bin/blueprint/check_placeholders.sh")
        init_env_defaults = _read("blueprint/repo.init.env")
        init_env_secrets_example = _read("blueprint/repo.init.secrets.example.env")

        self.assertIn("blueprint_init_repo", init_script)
        self.assertIn("--dry-run", init_script)
        self.assertIn("--force", init_python)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_script)
        self.assertIn("blueprint_init_force_var_name", init_script)
        self.assertIn("blueprint_load_env_defaults", init_script)
        self.assertIn("BLUEPRINT_REPO_NAME", init_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", init_script)
        self.assertIn("BLUEPRINT_GITHUB_REPO", init_script)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH", init_script)
        self.assertIn("blueprint_init_repo_interactive", init_interactive_script)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_interactive_script)
        self.assertIn("blueprint_init_force_var_name", init_interactive_script)
        self.assertIn("prompt_with_default", init_interactive_script)
        self.assertIn("contract_runtime.sh", init_script)
        self.assertIn("contract_runtime.sh", init_interactive_script)
        self.assertIn("contract_runtime.sh", placeholder_script)
        self.assertIn("blueprint_load_env_defaults", placeholder_script)
        self.assertIn('scripts/bin/blueprint/render_makefile.sh', init_script)
        self.assertIn("_render_contract", init_python)
        self.assertIn("_render_docusaurus_config", init_python)
        self.assertIn("_ensure_defaults_env_file", init_python)
        self.assertIn("_ensure_secrets_example_env_file", init_python)
        self.assertIn("_ensure_local_secrets_env_file", init_python)
        self.assertIn("init_repo_contract", init_python)
        self.assertIn("init_repo_renderers", init_python)
        self.assertIn("init_repo_env", init_python)
        self.assertIn("init_repo_io", init_python)
        self.assertIn("--dry-run", init_python)
        self.assertIn("blueprint_template_smoke", smoke_script)
        self.assertIn("make blueprint-bootstrap", smoke_script)
        self.assertIn("make blueprint-check-placeholders", smoke_script)
        self.assertIn("make infra-provision-deploy", smoke_script)
        self.assertIn("make infra-status-json", smoke_script)
        self.assertIn("blueprint_sanitize_init_placeholder_defaults", smoke_script)
        self.assertIn("BLUEPRINT_TEMPLATE_SMOKE_SCENARIO", smoke_script)
        self.assertIn("assert_template_smoke_repo_state", smoke_script)
        self.assertIn("APP_RUNTIME_MIN_WORKLOADS", smoke_script)
        self.assertIn("blueprint_check_placeholders", placeholder_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", placeholder_script)
        self.assertIn("BLUEPRINT_REPO_NAME=", init_env_defaults)
        self.assertIn("BLUEPRINT_GITHUB_ORG=", init_env_defaults)
        self.assertIn("BLUEPRINT_GITHUB_REPO=", init_env_defaults)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_REGION=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TENANT_SLUG=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_PLATFORM_SLUG=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_PROJECT_ID=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_BUCKET=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX=", init_env_defaults)
        self.assertIn("KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED=true", init_env_defaults)
        self.assertIn("EVENT_MESSAGING_BASELINE_ENABLED=false", init_env_defaults)
        self.assertIn("ZERO_DOWNTIME_EVOLUTION_ENABLED=false", init_env_defaults)
        self.assertIn("TENANT_CONTEXT_PROPAGATION_ENABLED=false", init_env_defaults)
        self.assertIn("APP_CATALOG_SCAFFOLD_ENABLED=false", init_env_defaults)
        self.assertIn("APP_RUNTIME_GITOPS_ENABLED=true", init_env_defaults)
        self.assertIn("APP_RUNTIME_MIN_WORKLOADS=1", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_SOURCE_NAMESPACE=security", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_TARGET_NAMESPACE=apps", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT=180", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_REQUIRED=false", init_env_defaults)
        self.assertIn("ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=false", init_env_defaults)
        self.assertIn("ASYNC_PACT_PRODUCER_VERIFY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_CONSUMER_VERIFY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_BROKER_PUBLISH_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_CAN_I_DEPLOY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_PRODUCER_ARTIFACT_DIR=artifacts/contracts/async/pact/producer", init_env_defaults)
        self.assertIn("ASYNC_PACT_CONSUMER_ARTIFACT_DIR=artifacts/contracts/async/pact/consumer", init_env_defaults)
        self.assertIn("STACKIT_SERVICE_ACCOUNT_KEY=", init_env_secrets_example)
        self.assertIn("STACKIT_TFSTATE_ACCESS_KEY_ID=", init_env_secrets_example)
        self.assertIn("defaults_env_file: blueprint/repo.init.env", _read("blueprint/contract.yaml"))
        self.assertIn(
            "secrets_example_env_file: blueprint/repo.init.secrets.example.env",
            _read("blueprint/contract.yaml"),
        )
        self.assertIn("secrets_env_file: blueprint/repo.init.secrets.env", _read("blueprint/contract.yaml"))
        self.assertIn("force_env_var: BLUEPRINT_INIT_FORCE", _read("blueprint/contract.yaml"))
        self.assertIn("consumer_init:", _read("blueprint/contract.yaml"))
        self.assertIn("ownership_path_classes:", _read("blueprint/contract.yaml"))
        self.assertIn("app_catalog_scaffold_contract:", _read("blueprint/contract.yaml"))
        self.assertIn("app_runtime_gitops_contract:", _read("blueprint/contract.yaml"))

    def test_blueprint_init_python_updates_contract_and_docs(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/root").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/environments/dev").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/overlays/local").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/modules").mkdir(parents=True, exist_ok=True)
            (tmp_root / "dags").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/modules/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/infra/modules/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/contract.yaml").write_text(
                _read("blueprint/contract.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "README.md").write_text("source readme", encoding="utf-8")
            (tmp_root / "AGENTS.md").write_text("source agents", encoding="utf-8")
            (tmp_root / "AGENTS.backlog.md").write_text("source backlog", encoding="utf-8")
            (tmp_root / "AGENTS.decisions.md").write_text("source decisions", encoding="utf-8")
            (tmp_root / "docs/README.md").write_text("source docs index", encoding="utf-8")
            (tmp_root / ".github/CODEOWNERS").write_text("source codeowners", encoding="utf-8")
            (tmp_root / ".github/pull_request_template.md").write_text("source pr template", encoding="utf-8")
            (tmp_root / ".github/ISSUE_TEMPLATE/bug_report.yml").write_text("source bug template", encoding="utf-8")
            (tmp_root / ".github/ISSUE_TEMPLATE/feature_request.yml").write_text(
                "source feature template",
                encoding="utf-8",
            )
            (tmp_root / ".github/ISSUE_TEMPLATE/config.yml").write_text("blank_issues_enabled: false\n", encoding="utf-8")
            (tmp_root / ".github/workflows/ci.yml").write_text("source ci", encoding="utf-8")
            (tmp_root / "tests/blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/blueprint/placeholder.py").write_text("source blueprint tests", encoding="utf-8")
            (tmp_root / "tests/docs/placeholder.py").write_text("source docs tests", encoding="utf-8")
            (tmp_root / "dags/.airflowignore").write_text("apps/**\n", encoding="utf-8")
            (tmp_root / "infra/cloud/stackit/terraform/modules/workflows/main.tf").write_text("", encoding="utf-8")
            (tmp_root / "tests/infra/modules/workflows/README.md").write_text("workflow test", encoding="utf-8")
            for template_path in (
                "README.md.tmpl",
                "AGENTS.md.tmpl",
                "AGENTS.backlog.md.tmpl",
                "AGENTS.decisions.md.tmpl",
                "docs/README.md.tmpl",
                ".github/CODEOWNERS.tmpl",
                ".github/pull_request_template.md.tmpl",
                ".github/ISSUE_TEMPLATE/bug_report.yml.tmpl",
                ".github/ISSUE_TEMPLATE/feature_request.yml.tmpl",
                ".github/ISSUE_TEMPLATE/config.yml.tmpl",
                ".github/workflows/ci.yml.tmpl",
            ):
                source_path = REPO_ROOT / "scripts/templates/consumer/init" / template_path
                target_path = tmp_root / "scripts/templates/consumer/init" / template_path
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            for template_path in INIT_MANAGED_RESTORE_TEMPLATE_PATHS:
                _copy_repo_text_path(tmp_root, template_path)
            for source_path in (REPO_ROOT / "blueprint/modules").glob("*/module.contract.yaml"):
                target_path = tmp_root / source_path.relative_to(REPO_ROOT)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").write_text(
                _read("docs/docusaurus.config.js"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml").write_text(
                _read("infra/gitops/argocd/root/applicationset-platform-environments.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/environments/dev/platform-application.yaml").write_text(
                _read("infra/gitops/argocd/environments/dev/platform-application.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/overlays/local/application-platform-local.yaml").write_text(
                _read("infra/gitops/argocd/overlays/local/application-platform-local.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").write_text(
                _read("infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/foundation/env/dev.tfvars").write_text(
                _read("infra/cloud/stackit/terraform/foundation/env/dev.tfvars"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl").write_text(
                _read("infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl").write_text(
                _read("infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl"),
                encoding="utf-8",
            )

            result = run_command(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                ],
                cwd=REPO_ROOT,
                env={
                    "POSTGRES_ENABLED": "true",
                    "OBJECT_STORAGE_ENABLED": "true",
                    "PUBLIC_ENDPOINTS_ENABLED": "true",
                    "IDENTITY_AWARE_PROXY_ENABLED": "true",
                },
                timeout_seconds=TEST_SUBPROCESS_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            updated_contract = (tmp_root / "blueprint/contract.yaml").read_text(encoding="utf-8")
            updated_docs_config = (tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8")
            updated_argocd_root = (
                tmp_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml"
            ).read_text(encoding="utf-8")
            updated_argocd_environment_dev = (
                tmp_root / "infra/gitops/argocd/environments/dev/platform-application.yaml"
            ).read_text(encoding="utf-8")
            updated_argocd_local_application = (
                tmp_root / "infra/gitops/argocd/overlays/local/application-platform-local.yaml"
            ).read_text(encoding="utf-8")
            updated_bootstrap_tfvars = (
                tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars"
            ).read_text(encoding="utf-8")
            updated_foundation_tfvars = (
                tmp_root / "infra/cloud/stackit/terraform/foundation/env/dev.tfvars"
            ).read_text(encoding="utf-8")
            updated_bootstrap_backend = (
                tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl"
            ).read_text(encoding="utf-8")
            updated_foundation_backend = (
                tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl"
            ).read_text(encoding="utf-8")
            defaults_env = (tmp_root / "blueprint/repo.init.env").read_text(encoding="utf-8")
            local_secrets_env = (tmp_root / "blueprint/repo.init.secrets.env").read_text(encoding="utf-8")
            seeded_readme = (tmp_root / "README.md").read_text(encoding="utf-8")
            seeded_docs_readme = (tmp_root / "docs/README.md").read_text(encoding="utf-8")
            seeded_codeowners = (tmp_root / ".github/CODEOWNERS").read_text(encoding="utf-8")
            seeded_pr_template = (tmp_root / ".github/pull_request_template.md").read_text(encoding="utf-8")
            seeded_bug_template = (tmp_root / ".github/ISSUE_TEMPLATE/bug_report.yml").read_text(encoding="utf-8")
            optional_modules_section = _extract_yaml_section(updated_contract.splitlines(), "optional_modules")
            optional_module_entries = _extract_yaml_section(optional_modules_section, "modules")
            self.assertIn("name: acme-platform", updated_contract)
            self.assertIn("repo_mode: generated-consumer", updated_contract)
            self.assertIn("default_branch: main", updated_contract)
            self.assertEqual(_extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "postgres"), "enabled_by_default"), "true")
            self.assertEqual(
                _extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "object-storage"), "enabled_by_default"),
                "true",
            )
            self.assertEqual(
                _extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "public-endpoints"), "enabled_by_default"),
                "true",
            )
            self.assertEqual(
                _extract_yaml_scalar(
                    _extract_yaml_section(optional_module_entries, "identity-aware-proxy"),
                    "enabled_by_default",
                ),
                "true",
            )
            self.assertIn('title: "Acme Platform Blueprint"', updated_docs_config)
            self.assertIn('tagline: "Acme reusable platform blueprint"', updated_docs_config)
            self.assertIn('organizationName: "acme"', updated_docs_config)
            self.assertIn('projectName: "acme-platform"', updated_docs_config)
            self.assertIn(
                'editUrl: "https://github.com/acme/acme-platform/edit/main/docs/"',
                updated_docs_config,
            )
            self.assertIn("repoURL: https://github.com/acme/acme-platform.git", updated_argocd_root)
            self.assertIn(
                "repoURL: https://github.com/acme/acme-platform.git",
                updated_argocd_environment_dev,
            )
            self.assertIn(
                "repoURL: https://github.com/acme/acme-platform.git",
                updated_argocd_local_application,
            )
            self.assertIn('stackit_region   = "eu02"', updated_bootstrap_tfvars)
            self.assertIn('tenant_slug      = "acme"', updated_bootstrap_tfvars)
            self.assertIn('platform_slug    = "marketplace"', updated_bootstrap_tfvars)
            self.assertIn('stackit_project_id = "acme-marketplace-dev"', updated_bootstrap_tfvars)
            self.assertNotIn("tfstate_bucket_name", updated_bootstrap_tfvars)
            self.assertIn('state_key_prefix = "iac/tfstate"', updated_bootstrap_tfvars)
            self.assertIn('stackit_project_id = "acme-marketplace-dev"', updated_foundation_tfvars)
            self.assertIn('stackit_region     = "eu02"', updated_foundation_tfvars)
            self.assertIn('bucket       = "acme-marketplace-tf-state"', updated_bootstrap_backend)
            self.assertIn('key          = "iac/tfstate/dev/bootstrap.tfstate"', updated_bootstrap_backend)
            self.assertIn('region       = "eu02"', updated_bootstrap_backend)
            self.assertIn('s3 = "https://object.storage.eu02.onstackit.cloud"', updated_bootstrap_backend)
            self.assertIn('bucket       = "acme-marketplace-tf-state"', updated_foundation_backend)
            self.assertIn('key          = "iac/tfstate/dev/foundation.tfstate"', updated_foundation_backend)
            self.assertIn('region       = "eu02"', updated_foundation_backend)
            self.assertIn('s3 = "https://object.storage.eu02.onstackit.cloud"', updated_foundation_backend)
            self.assertIn("BLUEPRINT_REPO_NAME=acme-platform", defaults_env)
            self.assertIn("BLUEPRINT_DOCS_TITLE='Acme Platform Blueprint'", defaults_env)
            self.assertIn("POSTGRES_ENABLED=true", defaults_env)
            self.assertIn("OBJECT_STORAGE_ENABLED=true", defaults_env)
            self.assertIn("PUBLIC_ENDPOINTS_ENABLED=true", defaults_env)
            self.assertIn("IDENTITY_AWARE_PROXY_ENABLED=true", defaults_env)
            self.assertIn("POSTGRES_INSTANCE_NAME=blueprint-postgres", defaults_env)
            self.assertIn("POSTGRES_DB_NAME=platform", defaults_env)
            self.assertIn("POSTGRES_USER=platform", defaults_env)
            self.assertIn("OBJECT_STORAGE_BUCKET_NAME=marketplace-assets", defaults_env)
            self.assertIn("PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.local", defaults_env)
            self.assertIn("IAP_UPSTREAM_URL=http://catalog.apps.svc.cluster.local:8080", defaults_env)
            self.assertIn("KEYCLOAK_ISSUER_URL=https://auth.example.invalid/realms/iap", defaults_env)
            self.assertIn("KEYCLOAK_CLIENT_ID=iap-client", defaults_env)
            self.assertIn("POSTGRES_PASSWORD=platform-password", local_secrets_env)
            self.assertIn("IAP_COOKIE_SECRET=0123456789abcdef0123456789abcdef", local_secrets_env)
            self.assertIn("KEYCLOAK_CLIENT_SECRET=blueprint-client-secret", local_secrets_env)
            self.assertNotIn("KEYCLOAK_CLIENT_ID=", local_secrets_env)
            self.assertIn("platform project created from the STACKIT Platform Blueprint", seeded_readme)
            self.assertIn("Blueprint Reference Track", seeded_docs_readme)
            self.assertIn("generated repository", seeded_codeowners)
            self.assertIn("Describe the project change.", seeded_pr_template)
            self.assertIn("Project Bug Report", seeded_bug_template)
            self.assertFalse((tmp_root / "tests/blueprint").exists())
            self.assertFalse((tmp_root / "tests/docs").exists())
            self.assertFalse((tmp_root / "dags").exists())
            self.assertFalse((tmp_root / "infra/cloud/stackit/terraform/modules/workflows").exists())
            self.assertFalse((tmp_root / "tests/infra/modules/workflows").exists())

            custom_defaults_env = defaults_env.replace(
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.local",
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.acme.local",
            )
            (tmp_root / "blueprint/repo.init.env").write_text(custom_defaults_env, encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").unlink()
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").unlink()

            restore_result = run_command(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                    "--force",
                ],
                cwd=REPO_ROOT,
                env={
                    "POSTGRES_ENABLED": "true",
                    "OBJECT_STORAGE_ENABLED": "true",
                    "PUBLIC_ENDPOINTS_ENABLED": "true",
                    "IDENTITY_AWARE_PROXY_ENABLED": "true",
                },
                timeout_seconds=TEST_SUBPROCESS_TIMEOUT_SECONDS,
            )

            self.assertEqual(restore_result.returncode, 0, msg=restore_result.stdout + restore_result.stderr)
            self.assertIn('title: "Acme Platform Blueprint"', (tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8"))
            self.assertIn(
                'stackit_region   = "eu02"',
                (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.acme.local",
                (tmp_root / "blueprint/repo.init.env").read_text(encoding="utf-8"),
            )

    def test_blueprint_init_python_dry_run_does_not_mutate_files(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/docs").mkdir(parents=True, exist_ok=True)
            contract_original = _read("blueprint/contract.yaml")
            docs_original = _read("docs/docusaurus.config.js")
            (tmp_root / "blueprint/contract.yaml").write_text(contract_original, encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").write_text(docs_original, encoding="utf-8")
            for template_path in (
                "README.md.tmpl",
                "AGENTS.md.tmpl",
                "AGENTS.backlog.md.tmpl",
                "AGENTS.decisions.md.tmpl",
                "docs/README.md.tmpl",
                ".github/CODEOWNERS.tmpl",
                ".github/pull_request_template.md.tmpl",
                ".github/ISSUE_TEMPLATE/bug_report.yml.tmpl",
                ".github/ISSUE_TEMPLATE/feature_request.yml.tmpl",
                ".github/ISSUE_TEMPLATE/config.yml.tmpl",
                ".github/workflows/ci.yml.tmpl",
            ):
                source_path = REPO_ROOT / "scripts/templates/consumer/init" / template_path
                target_path = tmp_root / "scripts/templates/consumer/init" / template_path
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            for template_path in INIT_MANAGED_RESTORE_TEMPLATE_PATHS:
                _copy_repo_text_path(tmp_root, template_path)

            result = run_command(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
                timeout_seconds=TEST_SUBPROCESS_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("[dry-run] summary:", result.stdout)
            self.assertIn("created:", result.stdout)
            self.assertEqual((tmp_root / "blueprint/contract.yaml").read_text(encoding="utf-8"), contract_original)
            self.assertEqual((tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8"), docs_original)
            self.assertFalse((tmp_root / "blueprint/repo.init.secrets.env").exists())

    def test_blueprint_init_python_requires_force_for_generated_consumer_repo(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            contract_content = _read("blueprint/contract.yaml").replace("repo_mode: template-source", "repo_mode: generated-consumer", 1)
            (tmp_root / "blueprint/contract.yaml").write_text(contract_content, encoding="utf-8")

            result = run_command(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                ],
                cwd=REPO_ROOT,
                timeout_seconds=TEST_SUBPROCESS_TIMEOUT_SECONDS,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("BLUEPRINT_INIT_FORCE=true", result.stderr)

    def test_load_module_contract_resolves_repo_relative_path_through_symlinked_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            real_root = Path(tmpdir) / "real-repo"
            module_dir = real_root / "blueprint/modules/sample"
            module_dir.mkdir(parents=True, exist_ok=True)
            module_path = module_dir / "module.contract.yaml"
            module_path.write_text(
                "\n".join(
                    [
                        "apiVersion: blueprint.module.contract/v1alpha1",
                        "kind: OptionalModuleContract",
                        "metadata:",
                        "  name: sample",
                        "  version: 1.0.0",
                        "spec:",
                        "  module_id: sample",
                        '  purpose: "sample"',
                        "  enabled_by_default: false",
                        "  enable_flag: SAMPLE_ENABLED",
                        "  inputs:",
                        "    required_env: []",
                        "  outputs:",
                        "    produced: []",
                        "  make_targets: {}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            symlink_root = Path(tmpdir) / "repo-link"
            symlink_root.symlink_to(real_root, target_is_directory=True)

            module = load_module_contract(
                symlink_root / "blueprint/modules/sample/module.contract.yaml",
                real_root.resolve(),
            )

            self.assertEqual(module.contract_path, "blueprint/modules/sample/module.contract.yaml")
