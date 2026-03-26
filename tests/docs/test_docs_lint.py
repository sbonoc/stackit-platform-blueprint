from __future__ import annotations

import sys
import unittest

from tests._shared.helpers import REPO_ROOT, run


LINTER = REPO_ROOT / "scripts/bin/quality/lint_docs.py"
FIXTURES = REPO_ROOT / "tests/docs/fixtures"


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


if __name__ == "__main__":
    unittest.main()
