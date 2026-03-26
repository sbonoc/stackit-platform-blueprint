from __future__ import annotations

import unittest
from tests._shared.helpers import REPO_ROOT, module_flags_env, run, run_blueprint_and_infra_bootstrap


class VerticalSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        baseline_env = module_flags_env()
        baseline_bootstrap = run_blueprint_and_infra_bootstrap(baseline_env)
        self.assertEqual(
            baseline_bootstrap.returncode,
            0,
            msg=baseline_bootstrap.stdout + baseline_bootstrap.stderr,
        )

    def test_help_lists_vertical_slice_targets(self) -> None:
        result = run(["make", "help"])
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("blueprint-init-repo", result.stdout)
        self.assertIn("blueprint-init-repo-interactive", result.stdout)
        self.assertIn("blueprint-check-placeholders", result.stdout)
        self.assertIn("blueprint-template-smoke", result.stdout)
        self.assertIn("blueprint-release-notes", result.stdout)
        self.assertIn("blueprint-migrate", result.stdout)
        self.assertIn("blueprint-bootstrap", result.stdout)
        self.assertIn("blueprint-render-makefile", result.stdout)
        self.assertIn("infra-prereqs", result.stdout)
        self.assertIn("infra-help-reference", result.stdout)
        self.assertIn("infra-bootstrap", result.stdout)
        self.assertIn("infra-validate", result.stdout)
        self.assertIn("infra-audit-version", result.stdout)
        self.assertIn("infra-audit-version-cached", result.stdout)
        self.assertIn("infra-stackit-bootstrap-preflight", result.stdout)
        self.assertIn("infra-stackit-bootstrap-plan", result.stdout)
        self.assertIn("infra-stackit-foundation-preflight", result.stdout)
        self.assertIn("infra-stackit-foundation-plan", result.stdout)
        self.assertIn("infra-stackit-foundation-fetch-kubeconfig", result.stdout)
        self.assertIn("infra-stackit-ci-github-setup", result.stdout)
        self.assertIn("infra-stackit-runtime-prerequisites", result.stdout)
        self.assertIn("infra-stackit-runtime-inventory", result.stdout)
        self.assertIn("infra-stackit-runtime-deploy", result.stdout)
        self.assertIn("infra-stackit-provision-deploy", result.stdout)
        self.assertIn("infra-argocd-topology-render", result.stdout)
        self.assertIn("infra-argocd-topology-validate", result.stdout)
        self.assertIn("infra-doctor", result.stdout)
        self.assertIn("infra-context", result.stdout)
        self.assertIn("infra-status", result.stdout)
        self.assertIn("infra-status-json", result.stdout)
        self.assertIn("quality-hooks-run", result.stdout)
        self.assertIn("apps-publish-ghcr", result.stdout)
        self.assertIn("backend-test-unit", result.stdout)
        self.assertIn("touchpoints-test-unit", result.stdout)
        self.assertIn("test-unit-all", result.stdout)
        self.assertIn("docs-build", result.stdout)

    def test_infra_bootstrap_is_idempotent(self) -> None:
        first = run(["make", "infra-bootstrap"])
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        second = run(["make", "infra-bootstrap"])
        self.assertEqual(second.returncode, 0, msg=second.stderr)

    def test_validate_and_audit_pass(self) -> None:
        validate = run(["make", "infra-validate"])
        self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)
        audit = run(["make", "infra-audit-version"])
        self.assertEqual(audit.returncode, 0, msg=audit.stdout + audit.stderr)
        audit_cached = run(["make", "infra-audit-version-cached"])
        self.assertEqual(audit_cached.returncode, 0, msg=audit_cached.stdout + audit_cached.stderr)

    def test_apps_bootstrap_smoke_and_audit(self) -> None:
        env = module_flags_env(profile="local-lite")
        bootstrap = run(["make", "apps-bootstrap"], env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        smoke = run(["make", "apps-smoke"], env)
        self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)
        audit = run(["make", "apps-audit-versions"], env)
        self.assertEqual(audit.returncode, 0, msg=audit.stdout + audit.stderr)
        audit_cached = run(["make", "apps-audit-versions-cached"], env)
        self.assertEqual(audit_cached.returncode, 0, msg=audit_cached.stdout + audit_cached.stderr)
        publish = run(["make", "apps-publish-ghcr"], env)
        self.assertEqual(publish.returncode, 0, msg=publish.stdout + publish.stderr)

        manifest = REPO_ROOT / "apps" / "catalog" / "manifest.yaml"
        versions_lock = REPO_ROOT / "apps" / "catalog" / "versions.lock"
        apps_bootstrap_state = REPO_ROOT / "artifacts" / "apps" / "apps_bootstrap.env"
        apps_smoke_state = REPO_ROOT / "artifacts" / "apps" / "apps_smoke.env"
        apps_publish_state = REPO_ROOT / "artifacts" / "apps" / "apps_publish_ghcr.env"

        self.assertTrue(manifest.exists(), msg="apps manifest not found")
        self.assertTrue(versions_lock.exists(), msg="apps versions lock not found")
        self.assertTrue(apps_bootstrap_state.exists(), msg="apps bootstrap artifact not found")
        self.assertTrue(apps_smoke_state.exists(), msg="apps smoke artifact not found")
        self.assertTrue(apps_publish_state.exists(), msg="apps publish ghcr artifact not found")

    def test_provision_deploy_smoke_local_lite(self) -> None:
        env = module_flags_env(profile="local-lite")
        provision = run(["make", "infra-provision"], env)
        self.assertEqual(provision.returncode, 0, msg=provision.stdout + provision.stderr)
        deploy = run(["make", "infra-deploy"], env)
        self.assertEqual(deploy.returncode, 0, msg=deploy.stdout + deploy.stderr)
        smoke = run(["make", "infra-smoke"], env)
        self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)

        provision_state = (REPO_ROOT / "artifacts" / "infra" / "provision.env").read_text(encoding="utf-8")
        deploy_state = (REPO_ROOT / "artifacts" / "infra" / "deploy.env").read_text(encoding="utf-8")
        self.assertIn("foundation_driver=crossplane-kustomize", provision_state)
        self.assertIn("tooling_mode=dry-run", provision_state)
        self.assertIn("deploy_driver=argocd-kustomize", deploy_state)

    def test_provision_deploy_smoke_local_full_with_observability(self) -> None:
        env = module_flags_env(observability="true")
        provision = run(["make", "infra-provision"], env)
        self.assertEqual(provision.returncode, 0, msg=provision.stdout + provision.stderr)
        deploy = run(["make", "infra-deploy"], env)
        self.assertEqual(deploy.returncode, 0, msg=deploy.stdout + deploy.stderr)
        smoke = run(["make", "infra-smoke"], env)
        self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)

        observability_runtime = REPO_ROOT / "artifacts" / "infra" / "observability_runtime.env"
        observability_deploy = REPO_ROOT / "artifacts" / "infra" / "observability_deploy.env"
        observability_smoke = REPO_ROOT / "artifacts" / "infra" / "observability_smoke.env"
        self.assertTrue(observability_runtime.exists(), msg="observability runtime artifact not found")
        self.assertTrue(observability_deploy.exists(), msg="observability deploy artifact not found")
        self.assertTrue(observability_smoke.exists(), msg="observability smoke artifact not found")
        self.assertIn("provision_driver=crossplane_plus_helm", observability_runtime.read_text(encoding="utf-8"))

    def test_provision_stackit_profile_uses_terraform_driver(self) -> None:
        env = module_flags_env(profile="stackit-dev", observability="true")
        provision = run(["make", "infra-provision"], env)
        self.assertEqual(provision.returncode, 0, msg=provision.stdout + provision.stderr)
        provision_state = (REPO_ROOT / "artifacts" / "infra" / "provision.env").read_text(encoding="utf-8")
        self.assertIn("foundation_driver=terraform", provision_state)
        self.assertIn("foundation_path=", provision_state)
        observability_plan = (REPO_ROOT / "artifacts" / "infra" / "observability_plan.env").read_text(encoding="utf-8")
        self.assertIn("provision_driver=terraform", observability_plan)

    def test_stackit_operator_wrappers_dry_run(self) -> None:
        env = module_flags_env(profile="stackit-dev")
        steps = [
            "infra-doctor",
            "infra-stackit-bootstrap-preflight",
            "infra-stackit-bootstrap-plan",
            "infra-stackit-foundation-preflight",
            "infra-stackit-foundation-plan",
            "infra-argocd-topology-validate",
            "infra-context",
            "infra-status",
            "infra-status-json",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        status_snapshot = REPO_ROOT / "artifacts" / "infra" / "infra_status_snapshot.json"
        bootstrap_plan = REPO_ROOT / "artifacts" / "infra" / "stackit_bootstrap_plan.env"
        foundation_plan = REPO_ROOT / "artifacts" / "infra" / "stackit_foundation_plan.env"
        self.assertTrue(status_snapshot.exists(), msg="infra status json snapshot not found")
        self.assertTrue(bootstrap_plan.exists(), msg="stackit bootstrap plan state not found")
        self.assertTrue(foundation_plan.exists(), msg="stackit foundation plan state not found")


if __name__ == "__main__":
    unittest.main()
