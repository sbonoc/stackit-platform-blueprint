"""Regression tests for issues #272 and #273 — v1.10.0 docs hotfix.

#272: --ignore-workspace was removed from docs_pnpm_install, docs_pnpm_build,
      and docs_pnpm_start in v1.10.0, causing silent empty docs/node_modules/
      on consumers whose root pnpm-workspace.yaml excludes docs/.

#273: _docs_assert_pnpm_version log_fatal message does not name the root
      package.json packageManager field or the CI corepack prepare pin as
      sources of pnpm version truth, making the error opaque for operators.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_SITE_SH = REPO_ROOT / "scripts" / "lib" / "docs" / "site.sh"


def _extract_function_block(content: str, func_name: str) -> str:
    """Return the text from 'func_name() {' through its matching closing '}'."""
    lines = content.splitlines()
    in_func = False
    depth = 0
    block_lines: list[str] = []
    pattern = re.compile(rf"^{re.escape(func_name)}\s*\(\s*\)\s*\{{")
    for line in lines:
        if not in_func:
            if pattern.match(line):
                in_func = True
                depth = 1
                block_lines.append(line)
        else:
            block_lines.append(line)
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                break
    return "\n".join(block_lines)


class Issue272PnpmIgnoreWorkspaceTests(unittest.TestCase):
    """--ignore-workspace MUST be present in all three pnpm function invocations."""

    def setUp(self) -> None:
        self._content = _SITE_SH.read_text(encoding="utf-8")

    def test_docs_pnpm_install_has_ignore_workspace(self) -> None:
        block = _extract_function_block(self._content, "docs_pnpm_install")
        self.assertIn(
            "--ignore-workspace",
            block,
            msg=(
                "docs_pnpm_install must pass --ignore-workspace to pnpm so that "
                "install is standalone regardless of the consumer's pnpm-workspace.yaml "
                "globs. Regression: v1.10.0 removed this flag (issue #272)."
            ),
        )

    def test_docs_pnpm_build_has_ignore_workspace(self) -> None:
        block = _extract_function_block(self._content, "docs_pnpm_build")
        self.assertIn(
            "--ignore-workspace",
            block,
            msg=(
                "docs_pnpm_build must pass --ignore-workspace to pnpm. "
                "Regression: v1.10.0 removed this flag (issue #272)."
            ),
        )

    def test_docs_pnpm_start_has_ignore_workspace(self) -> None:
        block = _extract_function_block(self._content, "docs_pnpm_start")
        self.assertIn(
            "--ignore-workspace",
            block,
            msg=(
                "docs_pnpm_start must pass --ignore-workspace to pnpm. "
                "Regression: v1.10.0 removed this flag (issue #272)."
            ),
        )


class Issue273PnpmVersionErrorMessageTests(unittest.TestCase):
    """_docs_assert_pnpm_version log_fatal MUST enumerate all three pnpm version sources."""

    def setUp(self) -> None:
        self._content = _SITE_SH.read_text(encoding="utf-8")
        self._func_block = _extract_function_block(
            self._content, "_docs_assert_pnpm_version"
        )

    def test_pnpm_version_error_uses_log_fatal(self) -> None:
        self.assertIn(
            "log_fatal",
            self._func_block,
            msg=(
                "_docs_assert_pnpm_version must emit its error via log_fatal "
                "(NFR-OBS-001: preserve existing log output channel)."
            ),
        )

    def test_pnpm_version_error_mentions_root_package_json(self) -> None:
        self.assertIn(
            "root package.json",
            self._func_block,
            msg=(
                "_docs_assert_pnpm_version log_fatal message must name "
                "'root package.json' as a source of active pnpm version truth "
                "(corepack auto-activation). Regression: v1.10.0 error message "
                "omits this source (issue #273)."
            ),
        )

    def test_pnpm_version_error_mentions_corepack_prepare(self) -> None:
        self.assertIn(
            "corepack prepare",
            self._func_block,
            msg=(
                "_docs_assert_pnpm_version log_fatal message must name "
                "'corepack prepare' as a source of active pnpm version truth "
                "(CI pin). Regression: v1.10.0 error message omits this source "
                "(issue #273)."
            ),
        )
