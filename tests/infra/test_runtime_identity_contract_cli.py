from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


SCRIPT = REPO_ROOT / "scripts/lib/infra/runtime_identity_contract.py"


class RuntimeIdentityContractCliTests(unittest.TestCase):
    def test_runtime_env_defaults_include_key_runtime_contract_knobs(self) -> None:
        result = run_command(
            [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), "runtime-env-defaults"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertTrue(any(line.startswith("RUNTIME_CREDENTIALS_SOURCE_NAMESPACE\t") for line in lines))
        self.assertTrue(any(line.startswith("RUNTIME_CREDENTIALS_REQUIRED\t") for line in lines))
        self.assertTrue(any(line.startswith("ARGOCD_REPO_USERNAME\t") for line in lines))

    def test_keycloak_realms_command_exposes_contract_rows(self) -> None:
        result = run_command(
            [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), "keycloak-realms"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        rows = [line.split("\t") for line in result.stdout.splitlines() if line.strip()]
        self.assertTrue(any(row[0] == "workflows" for row in rows))
        self.assertTrue(any(row[0] == "langfuse" for row in rows))
        self.assertTrue(any(row[0] == "iap" for row in rows))
        for row in rows:
            self.assertGreaterEqual(len(row), 10)

    def test_render_eso_manifest_check_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runtime-external-secrets.yaml"
            render = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "render-eso-manifest",
                    "--output",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            self.assertTrue(output_path.exists())

            check = run_command(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo-root",
                    str(REPO_ROOT),
                    "render-eso-manifest",
                    "--output",
                    str(output_path),
                    "--check",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(check.returncode, 0, msg=check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
