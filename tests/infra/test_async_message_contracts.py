from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests._shared.helpers import run


class AsyncMessageContractsTests(unittest.TestCase):
    def test_async_contract_lanes_skip_when_feature_disabled(self) -> None:
        result = run(
            ["make", "test-contracts-async-all"],
            {
                "ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED": "false",
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertIn("feature toggle disabled", combined)
        self.assertIn("status=skipped", combined)

    def test_async_contract_lanes_fail_when_enabled_without_verify_entrypoints(self) -> None:
        result = run(
            ["make", "test-contracts-async-all"],
            {
                "ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED": "true",
                "ASYNC_PACT_PRODUCER_VERIFY_CMD": "",
                "ASYNC_PACT_CONSUMER_VERIFY_CMD": "",
            },
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("verification entrypoint is missing", combined)
        self.assertIn("ASYNC_PACT_PRODUCER_VERIFY_CMD", combined)

    def test_async_contract_lanes_run_verify_and_optional_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            producer_artifacts = tmp_path / "producer"
            consumer_artifacts = tmp_path / "consumer"
            result = run(
                ["make", "test-contracts-async-all"],
                {
                    "ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED": "true",
                    "ASYNC_PACT_PRODUCER_ARTIFACT_DIR": str(producer_artifacts),
                    "ASYNC_PACT_CONSUMER_ARTIFACT_DIR": str(consumer_artifacts),
                    "ASYNC_PACT_PRODUCER_VERIFY_CMD": 'echo producer-ok > "$ASYNC_PACT_ARTIFACT_DIR/producer.txt"',
                    "ASYNC_PACT_CONSUMER_VERIFY_CMD": 'echo consumer-ok > "$ASYNC_PACT_ARTIFACT_DIR/consumer.txt"',
                    "ASYNC_PACT_BROKER_PUBLISH_CMD": 'echo publish-ok > "$ASYNC_PACT_ARTIFACT_DIR/publish.txt"',
                    "ASYNC_PACT_CAN_I_DEPLOY_CMD": 'echo deploy-ok > "$ASYNC_PACT_ARTIFACT_DIR/deploy.txt"',
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

            self.assertEqual((producer_artifacts / "producer.txt").read_text(encoding="utf-8").strip(), "producer-ok")
            self.assertEqual((producer_artifacts / "publish.txt").read_text(encoding="utf-8").strip(), "publish-ok")
            self.assertEqual((consumer_artifacts / "consumer.txt").read_text(encoding="utf-8").strip(), "consumer-ok")
            self.assertEqual((consumer_artifacts / "deploy.txt").read_text(encoding="utf-8").strip(), "deploy-ok")

    def test_contracts_all_target_runs_async_lane_first(self) -> None:
        dry_run = run(["make", "-n", "test-contracts-all"])
        self.assertEqual(dry_run.returncode, 0, msg=dry_run.stdout + dry_run.stderr)
        self.assertIn("scripts/bin/blueprint/test_async_message_contracts_all.sh", dry_run.stdout)
        self.assertIn("scripts/bin/platform/test/contracts_all.sh", dry_run.stdout)


if __name__ == "__main__":
    unittest.main()
