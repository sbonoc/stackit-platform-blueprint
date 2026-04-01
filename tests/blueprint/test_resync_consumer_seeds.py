from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.lib.blueprint.cli_support import render_template
from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


RESYNC_SCRIPT = REPO_ROOT / "scripts/lib/blueprint/resync_consumer_seeds.py"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return run_command(cmd, cwd=cwd)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ResyncConsumerSeedsTests(unittest.TestCase):
    def _prepare_generated_repo(self, tmp_root: Path) -> dict[str, str]:
        contract_content = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8").replace(
            "repo_mode: template-source",
            "repo_mode: generated-consumer",
            1,
        )
        contract_content = contract_content.replace(
            "name: stackit-k8s-reusable-blueprint",
            "name: acme-platform",
            1,
        )
        _write(tmp_root / "blueprint/contract.yaml", contract_content)

        contract = load_blueprint_contract(tmp_root / "blueprint/contract.yaml")
        replacements = {
            "REPO_NAME": "acme-platform",
            "DEFAULT_BRANCH": contract.repository.default_branch,
            "TEMPLATE_VERSION": contract.repository.template_bootstrap.template_version,
        }

        template_root = REPO_ROOT / "scripts/templates/consumer/init"
        for relative_path in contract.repository.consumer_seeded_paths:
            template_path = template_root / f"{relative_path}.tmpl"
            _write(
                tmp_root / "scripts/templates/consumer/init" / f"{relative_path}.tmpl",
                template_path.read_text(encoding="utf-8"),
            )

        _write(tmp_root / "README.md", "# custom README\n")
        _write(tmp_root / "AGENTS.md", "# custom AGENTS\n")
        _write(
            tmp_root / ".github/CODEOWNERS",
            render_template(
                (template_root / ".github/CODEOWNERS.tmpl").read_text(encoding="utf-8"),
                replacements,
            ),
        )
        _write(
            tmp_root / ".github/ISSUE_TEMPLATE/bug_report.yml",
            "name: local bug template customization\n",
        )
        _write(
            tmp_root / ".github/ISSUE_TEMPLATE/feature_request.yml",
            "name: local feature template customization\n",
        )
        _write(
            tmp_root / ".github/ISSUE_TEMPLATE/config.yml",
            "blank_issues_enabled: false\n",
        )

        self.assertEqual(_run(["git", "init"], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "config", "user.email", "tests@example.com"], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "config", "user.name", "Blueprint Tests"], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "add", "."], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "commit", "-m", "initial generated repo"], cwd=tmp_root).returncode, 0)

        # Ensure AGENTS.md is classified as manual-merge by giving it >2 commits.
        _write(tmp_root / "AGENTS.md", "# customized AGENTS history\n")
        self.assertEqual(_run(["git", "add", "AGENTS.md"], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "commit", "-m", "customize agents"], cwd=tmp_root).returncode, 0)
        _write(tmp_root / "AGENTS.md", "# customized AGENTS history again\n")
        self.assertEqual(_run(["git", "add", "AGENTS.md"], cwd=tmp_root).returncode, 0)
        self.assertEqual(_run(["git", "commit", "-m", "customize agents again"], cwd=tmp_root).returncode, 0)
        return replacements

    def test_dry_run_classifies_auto_refresh_and_manual_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_generated_repo(tmp_root)

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("consumer-seed-resync mode=dry-run", result.stdout)
            self.assertIn("auto-refresh: README.md (status=drifted action=update)", result.stdout)
            self.assertIn("manual-merge: AGENTS.md (status=drifted action=update)", result.stdout)
            self.assertIn("auto-refresh: docs/README.md (status=missing action=create)", result.stdout)
            self.assertIn("manual_merge=1", result.stdout)

    def test_apply_safe_updates_only_auto_refresh_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            replacements = self._prepare_generated_repo(tmp_root)

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--apply-safe",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("consumer-seed-resync mode=apply-safe", result.stdout)

            readme_expected = render_template(
                (REPO_ROOT / "scripts/templates/consumer/init/README.md.tmpl").read_text(encoding="utf-8"),
                replacements,
            )
            self.assertEqual((tmp_root / "README.md").read_text(encoding="utf-8"), readme_expected)

            docs_readme_expected = render_template(
                (REPO_ROOT / "scripts/templates/consumer/init/docs/README.md.tmpl").read_text(encoding="utf-8"),
                replacements,
            )
            self.assertEqual((tmp_root / "docs/README.md").read_text(encoding="utf-8"), docs_readme_expected)
            workflow_content = (tmp_root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
            self.assertIn(f"      - {replacements['DEFAULT_BRANCH']}", workflow_content)
            self.assertNotIn("{{DEFAULT_BRANCH}}", workflow_content)

            # AGENTS.md remains unchanged because it is classified as manual-merge.
            self.assertEqual(
                (tmp_root / "AGENTS.md").read_text(encoding="utf-8"),
                "# customized AGENTS history again\n",
            )

    def test_two_commit_drift_is_still_auto_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_generated_repo(tmp_root)

            _write(tmp_root / "README.md", "# custom README second commit\n")
            self.assertEqual(_run(["git", "add", "README.md"], cwd=tmp_root).returncode, 0)
            self.assertEqual(_run(["git", "commit", "-m", "customize readme"], cwd=tmp_root).returncode, 0)

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(
                "auto-refresh: README.md (status=drifted action=update) - one or two commits touched this path; "
                "treated as untouched seed/init rewrite",
                result.stdout,
            )

    def test_report_path_rejects_repo_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_generated_repo(tmp_root)
            escaped_report_path = tmp_root.parent / "escaped-report.json"

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--dry-run",
                    "--report-path",
                    "../escaped-report.json",
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn(
                "--report-path must stay within the repository root when using a relative path",
                result.stderr,
            )
            self.assertFalse(escaped_report_path.exists())

    def test_apply_safe_fails_when_consumer_template_has_unresolved_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_generated_repo(tmp_root)
            workflow_template_path = tmp_root / "scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl"
            workflow_template = workflow_template_path.read_text(encoding="utf-8")
            workflow_template = workflow_template.replace("{{DEFAULT_BRANCH}}", "{{ unresolved_branch_token }}", 1)
            workflow_template_path.write_text(workflow_template, encoding="utf-8")

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--apply-safe",
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn(
                "unresolved consumer template token(s) in .github/workflows/ci.yml "
                "(template scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl): "
                "{{ unresolved_branch_token }}",
                result.stderr,
            )

    def test_refuses_template_source_repo_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            _write(
                tmp_root / "blueprint/contract.yaml",
                (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8"),
            )

            result = _run(
                [
                    sys.executable,
                    str(RESYNC_SCRIPT),
                    "--repo-root",
                    str(tmp_root),
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("only supported for generated-consumer repositories", result.stderr)


if __name__ == "__main__":
    unittest.main()
