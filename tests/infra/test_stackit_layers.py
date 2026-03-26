from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, module_flags_env, run_make


class StackitLayerContractTests(unittest.TestCase):
    def test_stackit_preflight_uses_layered_terraform_contract(self) -> None:
        env = module_flags_env(profile="stackit-dev")

        bootstrap = run_make("infra-stackit-bootstrap-preflight", env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        bootstrap_state = (REPO_ROOT / "artifacts" / "infra" / "stackit_bootstrap_preflight.env").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            f"terraform_dir={REPO_ROOT}/infra/cloud/stackit/terraform/bootstrap",
            bootstrap_state,
        )
        self.assertIn(
            f"backend_file={REPO_ROOT}/infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl",
            bootstrap_state,
        )
        self.assertIn(
            f"var_file={REPO_ROOT}/infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars",
            bootstrap_state,
        )
        self.assertIn("tfstate_credential_source=dry-run-placeholder", bootstrap_state)

        foundation = run_make("infra-stackit-foundation-preflight", env)
        self.assertEqual(foundation.returncode, 0, msg=foundation.stdout + foundation.stderr)
        foundation_state = (REPO_ROOT / "artifacts" / "infra" / "stackit_foundation_preflight.env").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            f"terraform_dir={REPO_ROOT}/infra/cloud/stackit/terraform/foundation",
            foundation_state,
        )
        self.assertIn(
            f"backend_file={REPO_ROOT}/infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl",
            foundation_state,
        )
        self.assertIn(
            f"var_file={REPO_ROOT}/infra/cloud/stackit/terraform/foundation/env/dev.tfvars",
            foundation_state,
        )
        self.assertIn("tfstate_credential_source=dry-run-placeholder", foundation_state)


if __name__ == "__main__":
    unittest.main()
