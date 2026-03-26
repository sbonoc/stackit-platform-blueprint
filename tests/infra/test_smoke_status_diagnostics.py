from __future__ import annotations

import json
import unittest

from tests._shared.helpers import REPO_ROOT, module_flags_env, restore_default_generated_state, run


class SmokeStatusDiagnosticsTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset = restore_default_generated_state()
        self.assertEqual(reset.returncode, 0, msg=reset.stdout + reset.stderr)

    def test_smoke_and_status_json_emit_diagnostics_for_both_observability_states(self) -> None:
        for observability in ("false", "true"):
            with self.subTest(observability=observability):
                env = module_flags_env(profile="local-full", observability=observability)

                provision = run(["make", "infra-provision"], env)
                self.assertEqual(provision.returncode, 0, msg=provision.stdout + provision.stderr)

                deploy = run(["make", "infra-deploy"], env)
                self.assertEqual(deploy.returncode, 0, msg=deploy.stdout + deploy.stderr)

                smoke = run(["make", "infra-smoke"], env)
                self.assertEqual(smoke.returncode, 0, msg=smoke.stdout + smoke.stderr)

                status_json = run(["make", "infra-status-json"], env)
                self.assertEqual(status_json.returncode, 0, msg=status_json.stdout + status_json.stderr)

                smoke_result = REPO_ROOT / "artifacts" / "infra" / "smoke_result.json"
                smoke_diagnostics = REPO_ROOT / "artifacts" / "infra" / "smoke_diagnostics.json"
                status_snapshot = REPO_ROOT / "artifacts" / "infra" / "infra_status_snapshot.json"

                self.assertTrue(smoke_result.exists(), msg="smoke result artifact not found")
                self.assertTrue(smoke_diagnostics.exists(), msg="smoke diagnostics artifact not found")
                self.assertTrue(status_snapshot.exists(), msg="status snapshot artifact not found")

                smoke_result_payload = json.loads(smoke_result.read_text(encoding="utf-8"))
                smoke_diagnostics_payload = json.loads(smoke_diagnostics.read_text(encoding="utf-8"))
                status_snapshot_payload = json.loads(status_snapshot.read_text(encoding="utf-8"))

                expected_observability = observability == "true"
                self.assertEqual(smoke_result_payload["status"], "success")
                self.assertEqual(smoke_result_payload["observabilityEnabled"], expected_observability)
                self.assertEqual(smoke_diagnostics_payload["observabilityEnabled"], expected_observability)
                self.assertEqual(status_snapshot_payload["observabilityEnabled"], expected_observability)
                self.assertEqual(status_snapshot_payload["latestSmoke"]["status"], "success")
                self.assertTrue(status_snapshot_payload["latestSmoke"]["resultPresent"])
                self.assertTrue(status_snapshot_payload["latestSmoke"]["diagnosticsPresent"])

                if expected_observability:
                    self.assertIn("observability", smoke_result_payload["enabledModules"])
                else:
                    self.assertNotIn("observability", smoke_result_payload["enabledModules"])


if __name__ == "__main__":
    unittest.main()
