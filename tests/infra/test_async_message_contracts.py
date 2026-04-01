from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


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

    def test_async_contract_wrappers_load_repo_init_defaults(self) -> None:
        repo_init_env_path = REPO_ROOT / "blueprint/repo.init.env"
        original_content = repo_init_env_path.read_text(encoding="utf-8")
        producer_artifact = REPO_ROOT / "artifacts/contracts/async/pact/producer/defaults-from-init.txt"
        appended_defaults = (
            "\nASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=true\n"
            "ASYNC_PACT_PRODUCER_VERIFY_CMD='echo defaults-ok > "
            "\"$ASYNC_PACT_ARTIFACT_DIR/defaults-from-init.txt\"'\n"
        )

        try:
            repo_init_env_path.write_text(original_content + appended_defaults, encoding="utf-8")
            result = run(
                [
                    str(REPO_ROOT / "scripts/bin/blueprint/test_async_message_contracts_producer.sh"),
                ],
                {},
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(producer_artifact.is_file())
            self.assertEqual(producer_artifact.read_text(encoding="utf-8").strip(), "defaults-ok")
        finally:
            repo_init_env_path.write_text(original_content, encoding="utf-8")
            if producer_artifact.exists():
                producer_artifact.unlink()

    def test_async_contract_relative_artifact_dir_is_normalized_to_repo_root(self) -> None:
        producer_artifact = REPO_ROOT / "artifacts/contracts/async/pact/producer/normalized.txt"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_cwd = Path(tmpdir)
                result = run(
                    [
                        str(REPO_ROOT / "scripts/bin/blueprint/test_async_message_contracts_producer.sh"),
                    ],
                    {
                        "ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED": "true",
                        "ASYNC_PACT_PRODUCER_ARTIFACT_DIR": "artifacts/contracts/async/pact/producer",
                        "ASYNC_PACT_PRODUCER_VERIFY_CMD": 'echo normalized-ok > "$ASYNC_PACT_ARTIFACT_DIR/normalized.txt"',
                    },
                    cwd=temp_cwd,
                )
                self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
                self.assertTrue(producer_artifact.is_file())
                self.assertFalse((temp_cwd / "artifacts/contracts/async/pact/producer/normalized.txt").exists())
                self.assertEqual(producer_artifact.read_text(encoding="utf-8").strip(), "normalized-ok")
        finally:
            if producer_artifact.exists():
                producer_artifact.unlink()


if __name__ == "__main__":
    unittest.main()
