from __future__ import annotations

from pathlib import Path
import shlex
import tempfile
import unittest

from tests._shared.exec import DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS, run_command


REPO_ROOT = Path(__file__).resolve().parents[2]


class BootstrapTemplateTests(unittest.TestCase):
    def _run_bootstrap_snippet(self, snippet: str):
        return run_command(
            ["bash", "-lc", snippet],
            cwd=REPO_ROOT,
            timeout_seconds=DEFAULT_TEST_COMMAND_TIMEOUT_SECONDS,
        )

    def test_missing_template_fails_without_creating_empty_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            target = repo_root / "infra/local/helm/core/cert-manager.values.yaml"
            # ROOT_DIR must be set AFTER sourcing bootstrap.sh because bootstrap.sh
            # unconditionally overrides ROOT_DIR to its own resolved repo root.
            snippet = "\n".join(
                [
                    "set -euo pipefail",
                    f"source {shlex.quote(str(REPO_ROOT / 'scripts/lib/shell/bootstrap.sh'))}",
                    f"ROOT_DIR={shlex.quote(str(repo_root))}",
                    f"source {shlex.quote(str(REPO_ROOT / 'scripts/lib/blueprint/bootstrap_templates.sh'))}",
                    'ensure_file_from_template "$ROOT_DIR/infra/local/helm/core/cert-manager.values.yaml" infra "infra/local/helm/core/cert-manager.values.yaml"',
                ]
            )
            result = self._run_bootstrap_snippet(snippet)

            combined = f"{result.stdout}\n{result.stderr}"
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing bootstrap template (infra)", combined)
            self.assertFalse(target.exists())

    def test_existing_empty_target_is_repaired_from_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            template = repo_root / "scripts/templates/infra/bootstrap/infra/local/helm/core/cert-manager.values.yaml"
            template.parent.mkdir(parents=True, exist_ok=True)
            template.write_text("crds:\n  enabled: true\n", encoding="utf-8")

            target = repo_root / "infra/local/helm/core/cert-manager.values.yaml"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")

            # ROOT_DIR must be set AFTER sourcing bootstrap.sh because bootstrap.sh
            # unconditionally overrides ROOT_DIR to its own resolved repo root.
            snippet = "\n".join(
                [
                    "set -euo pipefail",
                    f"source {shlex.quote(str(REPO_ROOT / 'scripts/lib/shell/bootstrap.sh'))}",
                    f"ROOT_DIR={shlex.quote(str(repo_root))}",
                    f"source {shlex.quote(str(REPO_ROOT / 'scripts/lib/blueprint/bootstrap_templates.sh'))}",
                    'ensure_file_from_template "$ROOT_DIR/infra/local/helm/core/cert-manager.values.yaml" infra "infra/local/helm/core/cert-manager.values.yaml"',
                ]
            )
            result = self._run_bootstrap_snippet(snippet)

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "crds:\n  enabled: true")
            self.assertIn("rewrote empty bootstrap target from template", f"{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
