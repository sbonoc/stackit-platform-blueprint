from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


LINTER = REPO_ROOT / "scripts/bin/quality/lint_docs.py"
FIXTURES = REPO_ROOT / "tests/docs/fixtures"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class DocsLintTests(unittest.TestCase):
    def test_repo_docs_lint_passes(self) -> None:
        result = run(["make", "quality-docs-lint"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_valid_fixture_passes(self) -> None:
        fixture = FIXTURES / "lint_valid"
        result = run([sys.executable, str(LINTER), "--repo-root", str(fixture)])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_invalid_fixture_fails(self) -> None:
        fixture = FIXTURES / "lint_invalid"
        result = run([sys.executable, str(LINTER), "--repo-root", str(fixture)])
        self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("broken local markdown link", result.stderr)
        self.assertIn("unknown make target reference", result.stderr)
        self.assertIn("non-canonical governance file reference", result.stderr)

    def test_rabbitmq_family_contract_passes_when_docs_match_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "scripts/lib/infra/versions.sh",
                'RABBITMQ_LOCAL_IMAGE_TAG="4.0.9-debian-12-r1"\n',
            )
            _write(
                repo_root / "docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            _write(
                repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                    "--doc-glob",
                    "scripts/templates/blueprint/bootstrap/docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_rabbitmq_family_contract_fails_when_family_line_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "scripts/lib/infra/versions.sh",
                'RABBITMQ_LOCAL_IMAGE_TAG="4.0.9-debian-12-r1"\n',
            )
            _write(
                repo_root / "docs/platform/modules/rabbitmq/README.md",
                "No family line here.\n",
            )
            _write(
                repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                    "--doc-glob",
                    "scripts/templates/blueprint/bootstrap/docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("missing RabbitMQ managed family contract line", result.stderr)

    def test_rabbitmq_family_contract_fails_when_docs_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "scripts/lib/infra/versions.sh",
                'RABBITMQ_LOCAL_IMAGE_TAG="4.0.9-debian-12-r1"\n',
            )
            _write(
                repo_root / "docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `3.13`\n",
            )
            _write(
                repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                    "--doc-glob",
                    "scripts/templates/blueprint/bootstrap/docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("RabbitMQ managed-service major-family drift", result.stderr)

    def test_rabbitmq_family_contract_fails_when_versions_source_unreadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "scripts/lib/infra/versions.sh",
                'RABBITMQ_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/rabbitmq"\n',
            )
            _write(
                repo_root / "docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            _write(
                repo_root / "scripts/templates/blueprint/bootstrap/docs/platform/modules/rabbitmq/README.md",
                "RabbitMQ managed-service major family: `4.0`\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                    "--doc-glob",
                    "scripts/templates/blueprint/bootstrap/docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("unable to derive RabbitMQ managed-service major family", result.stderr)

    def test_generated_core_targets_fails_when_raw_angle_bracket_tokens_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "docs/reference/generated/core_targets.generated.md",
                "\n".join(
                    [
                        "# Core Make Targets",
                        "| Target | Description |",
                        "| --- | --- |",
                        "| `spec-scaffold` | set SPEC_BRANCH=<name> |",
                    ]
                )
                + "\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("raw angle-bracket token in generated core targets row", result.stderr)

    def test_generated_core_targets_passes_when_angle_bracket_tokens_are_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(
                repo_root / "docs/reference/generated/core_targets.generated.md",
                "\n".join(
                    [
                        "# Core Make Targets",
                        "| Target | Description |",
                        "| --- | --- |",
                        "| `spec-scaffold` | set SPEC_BRANCH=&lt;name&gt; |",
                    ]
                )
                + "\n",
            )
            result = run(
                [
                    sys.executable,
                    str(LINTER),
                    "--repo-root",
                    str(repo_root),
                    "--doc-glob",
                    "docs/**/*.md",
                ],
                cwd=repo_root,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
