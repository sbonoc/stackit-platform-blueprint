from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from scripts.lib.infra.argocd_repo_contract import (
    canonical_github_https_repo_url,
    render_argocd_repo_url_replacements,
)
from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


SCRIPT = REPO_ROOT / "scripts/lib/infra/argocd_repo_contract.py"


class ArgoCdRepoContractCliTests(unittest.TestCase):
    def test_validate_passes_on_repo_root(self) -> None:
        result = run_command(
            [sys.executable, str(SCRIPT), "--repo-root", str(REPO_ROOT), "validate"],
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertRegex(result.stdout.strip(), r"^https://github\.com/.+/.+\.git$")

    def test_validate_fails_for_invalid_repo_url_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            manifest = tmp_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                "spec:\n  template:\n    spec:\n      source:\n        repoURL: git@github.com:example/repo.git\n",
                encoding="utf-8",
            )

            result = run_command(
                [sys.executable, str(SCRIPT), "--repo-root", str(tmp_root), "validate"],
                cwd=REPO_ROOT,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("must use HTTPS GitHub URL", result.stderr)

    def test_render_helper_rewrites_repo_url_references(self) -> None:
        content = (
            "repoURL: https://github.com/old-org/old-repo.git\n"
            "sourceRepos:\n"
            "  - https://github.com/old-org/old-repo.git\n"
        )
        repo_url = canonical_github_https_repo_url("new-org", "new-repo")
        rendered = render_argocd_repo_url_replacements(content, repo_url)
        self.assertIn("repoURL: https://github.com/new-org/new-repo.git", rendered)
        self.assertIn("- https://github.com/new-org/new-repo.git", rendered)


if __name__ == "__main__":
    unittest.main()
