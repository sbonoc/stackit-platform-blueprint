from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, module_flags_env, run_make, run_render_and_infra_bootstrap


class CoreRuntimeBootstrapTests(unittest.TestCase):
    def test_local_provision_bootstraps_crossplane_core(self) -> None:
        env = module_flags_env(profile="local-full")

        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        provision = run_make("infra-provision", env)
        self.assertEqual(provision.returncode, 0, msg=provision.stdout + provision.stderr)

        provision_state = (REPO_ROOT / "artifacts" / "infra" / "provision.env").read_text(encoding="utf-8")
        self.assertIn("foundation_driver=crossplane-helm-bootstrap", provision_state)

        crossplane_state_path = REPO_ROOT / "artifacts" / "infra" / "local_crossplane_bootstrap.env"
        self.assertTrue(crossplane_state_path.exists(), msg="local Crossplane bootstrap state was not created")
        crossplane_state = crossplane_state_path.read_text(encoding="utf-8")
        self.assertIn("crossplane_chart=crossplane-stable/crossplane", crossplane_state)
        self.assertIn("crossplane_values_file=", crossplane_state)

    def test_deploy_bootstraps_argocd_and_external_secrets_core(self) -> None:
        env = module_flags_env(profile="local-full")

        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        deploy = run_make("infra-deploy", env)
        self.assertEqual(deploy.returncode, 0, msg=deploy.stdout + deploy.stderr)

        core_state_path = REPO_ROOT / "artifacts" / "infra" / "core_runtime_bootstrap.env"
        self.assertTrue(core_state_path.exists(), msg="core runtime bootstrap state was not created")
        core_state = core_state_path.read_text(encoding="utf-8")

        self.assertIn("argocd_chart=argo/argo-cd", core_state)
        self.assertIn("external_secrets_chart=external-secrets/external-secrets", core_state)
        self.assertIn("cert_manager_chart=jetstack/cert-manager", core_state)

        smoke = run_make("infra-smoke", env)
        self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)

        smoke_state_path = REPO_ROOT / "artifacts" / "infra" / "core_runtime_smoke.env"
        self.assertTrue(smoke_state_path.exists(), msg="core runtime smoke state was not created")


if __name__ == "__main__":
    unittest.main()
