from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


SCRIPT = REPO_ROOT / "scripts/lib/infra/state_artifact_contract.py"


class StateArtifactContractTests(unittest.TestCase):
    def test_render_and_validate_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            env_file = tmp_root / "sample.env"
            json_file = tmp_root / "sample.json"
            env_file.write_text(
                "profile=local-full\nstatus=success\ntimestamp_utc=2026-04-08T12:00:00Z\n",
                encoding="utf-8",
            )

            render = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "render",
                    "--name",
                    "sample",
                    "--namespace",
                    "infra",
                    "--env-file",
                    str(env_file),
                    "--output-json",
                    str(json_file),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            self.assertTrue(json_file.exists())

            payload = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact"]["name"], "sample")
            self.assertEqual(payload["artifact"]["namespace"], "infra")
            self.assertEqual(payload["entryCount"], 3)
            self.assertEqual(payload["entries"]["status"], "success")

            validate = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "validate",
                    "--json-file",
                    str(json_file),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)

    def test_render_fails_on_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            env_file = tmp_root / "sample.env"
            json_file = tmp_root / "sample.json"
            env_file.write_text("status=success\nstatus=failure\n", encoding="utf-8")

            render = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "render",
                    "--name",
                    "sample",
                    "--namespace",
                    "infra",
                    "--env-file",
                    str(env_file),
                    "--output-json",
                    str(json_file),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(render.returncode, 1)
            self.assertIn("duplicates key", render.stderr)

    def test_validate_fails_when_numeric_minimum_is_violated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_file = tmp_root / "sample.json"
            json_file.write_text(
                json.dumps(
                    {
                        "schemaVersion": "1.0.0",
                        "artifact": {
                            "name": "sample",
                            "namespace": "infra",
                            "envPath": "artifacts/infra/sample.env",
                            "jsonPath": "artifacts/infra/sample.json",
                        },
                        "entryCount": -1,
                        "entryOrder": [],
                        "entries": {},
                    }
                ),
                encoding="utf-8",
            )

            validate = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "validate",
                    "--json-file",
                    str(json_file),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(validate.returncode, 1)
            self.assertIn("$.entryCount: expected value >= 0", validate.stderr)

    def test_validate_fails_when_entry_order_and_entries_keys_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_file = tmp_root / "sample.json"
            json_file.write_text(
                json.dumps(
                    {
                        "schemaVersion": "1.0.0",
                        "artifact": {
                            "name": "sample",
                            "namespace": "infra",
                            "envPath": "artifacts/infra/sample.env",
                            "jsonPath": "artifacts/infra/sample.json",
                        },
                        "entryCount": 1,
                        "entryOrder": ["status"],
                        "entries": {"status": "success", "extra": "unexpected"},
                    }
                ),
                encoding="utf-8",
            )

            validate = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "validate",
                    "--json-file",
                    str(json_file),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(validate.returncode, 1)
            self.assertIn("$.entryOrder/$.entries key mismatch", validate.stderr)


if __name__ == "__main__":
    unittest.main()
