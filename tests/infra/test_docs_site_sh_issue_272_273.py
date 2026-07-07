"""Regression tests for issues #272 and #273 — v1.10.0 docs hotfix.

#272: --ignore-workspace was removed from docs_pnpm_install, docs_pnpm_build,
      and docs_pnpm_start in v1.10.0, causing silent empty docs/node_modules/
      on consumers whose root pnpm-workspace.yaml excludes docs/.

#273: _docs_assert_pnpm_version log_fatal message does not name the root
      package.json packageManager field or the CI corepack prepare pin as
      sources of pnpm version truth, making the error opaque for operators.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_SITE_SH = REPO_ROOT / "scripts" / "lib" / "docs" / "site.sh"
_DOCS_PACKAGE_JSON = REPO_ROOT / "docs" / "package.json"
_CI_ACTION = REPO_ROOT / ".github" / "actions" / "prepare-blueprint-ci" / "action.yml"


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


class PnpmVersionSourcesAlignedTests(unittest.TestCase):
    """docs/package.json#packageManager and the CI corepack prepare pin must agree.

    The version mismatch that caused the CI failure on PR #399 slipped through
    local quality gates because the developer's local pnpm (Homebrew) already
    matched docs/package.json, while CI still pinned the old version via corepack.
    This test reads both sources and asserts they carry the same semver so that
    any future bump of one without the other fails in the unit suite before CI.
    """

    def _docs_pnpm_version(self) -> str:
        data = json.loads(_DOCS_PACKAGE_JSON.read_text(encoding="utf-8"))
        pkg_manager = data.get("packageManager", "")
        # "pnpm@11.9.0" → "11.9.0"
        if pkg_manager.startswith("pnpm@"):
            return pkg_manager[len("pnpm@"):]
        raise ValueError(f"packageManager field missing or not pnpm: {pkg_manager!r}")

    def _ci_action_pnpm_version(self) -> str:
        content = _CI_ACTION.read_text(encoding="utf-8")
        # Match exactly: corepack prepare pnpm@<semver>
        m = re.search(r"corepack\s+prepare\s+pnpm@([0-9]+\.[0-9]+\.[0-9]+)", content)
        if not m:
            raise ValueError(
                f"corepack prepare pnpm@<version> not found in {_CI_ACTION}"
            )
        return m.group(1)

    def test_docs_package_json_and_ci_action_pnpm_versions_match(self) -> None:
        docs_ver = self._docs_pnpm_version()
        ci_ver = self._ci_action_pnpm_version()
        self.assertEqual(
            docs_ver,
            ci_ver,
            msg=(
                f"pnpm version mismatch between docs/package.json ({docs_ver}) "
                f"and .github/actions/prepare-blueprint-ci/action.yml ({ci_ver}). "
                "When bumping pnpm, update BOTH sources atomically. "
                "This mismatch caused a CI failure on PR #399: local installs "
                "passed because Homebrew pnpm matched docs/package.json, but CI "
                "used the stale corepack pin and hit _docs_assert_pnpm_version."
            ),
        )


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
