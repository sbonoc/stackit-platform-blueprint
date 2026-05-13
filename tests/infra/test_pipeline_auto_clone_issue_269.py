"""Regression tests for issue #269 — pipeline auto-clone for URL-form BLUEPRINT_UPGRADE_SOURCE.

Tests cover:
- Pipeline normalizes URL-form upgrade_source to a local path before Stage 1b (AC-008)
- Pipeline registers EXIT trap to clean up cloned tmp dir (NFR-REL-001)
- Pipeline validates URL prefix allowlist before cloning (NFR-SEC-001)
- Local-path form continues to work without triggering auto-clone (AC-010)
- Engine (upgrade_consumer.py) skips internal clone when source is already a local .git dir (FR-003)
- Pipeline usage block documents auto-clone behaviour (NFR-OPS-001)
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_PIPELINE_PATH = REPO_ROOT / "scripts/bin/blueprint/upgrade_consumer_pipeline.sh"
_ENGINE_PATH = REPO_ROOT / "scripts/lib/blueprint/upgrade_consumer.py"


class PipelineURLNormalizationBlockTests(unittest.TestCase):
    """Assert the URL normalization block is present in the pipeline script (AC-008, NFR-REL-001, NFR-SEC-001)."""

    def test_pipeline_has_git_dir_guard_before_stage_1b(self) -> None:
        """Pipeline MUST guard on '.git' subdirectory presence before Stage 1b (FR-001, AC-008).

        Without this guard, Stages 1b and 5 receive a URL string as cwd= for git
        subprocess calls, causing Stage 5 to fatal-exit.  The guard detects
        non-local sources before Stage 1b so that auto-clone runs exactly once.
        """
        import re as _re

        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        # The normalization block (containing .git guard) must appear before Stage 1b code.
        # Use DOTALL so the pattern spans newlines between the guard and Stage 1b header.
        match = _re.search(
            r'upgrade_source.*?\.git.*?Stage 1b\s*[-—]+.*?version pin diff',
            pipeline_source,
            _re.DOTALL,
        )
        self.assertIsNotNone(
            match,
            msg=(
                "Pipeline must contain a '.git' directory guard that appears BEFORE Stage 1b "
                "(version pin diff) in the code (FR-001). "
                "Add '! [[ -d \"$upgrade_source/.git\" ]]' before Stage 1b to trigger "
                "auto-clone for URL-form sources."
            ),
        )

    def test_pipeline_registers_cloned_source_exit_trap(self) -> None:
        """Pipeline MUST register an EXIT trap to remove the tmp clone dir (FR-002, NFR-REL-001).

        Without the trap, a partial or failed clone leaves a tmp directory on disk
        across pipeline runs, wasting disk space and causing stale-path confusion.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertIsNotNone(
            re.search(r"trap\s+['\"].*rm\s+-rf\s+.*cloned_source", pipeline_source, re.DOTALL),
            msg=(
                "Pipeline must register 'trap 'rm -rf \"$cloned_source_dir\"' EXIT' "
                "immediately after the git clone in the URL normalization block (FR-002, NFR-REL-001). "
                "This ensures the tmp directory is cleaned up on success, failure, and SIGINT."
            ),
        )

    def test_pipeline_validates_url_prefix_allowlist(self) -> None:
        """Pipeline MUST validate the URL prefix allowlist before cloning (NFR-SEC-001).

        Shell-metacharacter injection is possible if an arbitrary string is passed
        to 'git clone'.  The allowlist (https://, git@, ssh://, /, ./, ../) is the
        normative guard.  Any other form MUST cause the pipeline to abort.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        for prefix in ("https://", "git@", "ssh://"):
            self.assertIn(
                prefix,
                pipeline_source,
                msg=(
                    f"Pipeline URL normalization block must include '{prefix}' in its allowlist "
                    f"validation (NFR-SEC-001).  Add a case/if block that accepts "
                    f"'https://', 'git@', 'ssh://', and local path prefixes before calling git clone."
                ),
            )

    def test_pipeline_clones_with_depth_1_and_branch_flag(self) -> None:
        """Pipeline MUST clone with --depth 1 and --branch $upgrade_ref (FR-001).

        Shallow clone is sufficient because only the target ref content is needed;
        full history wastes time and disk.  The --branch flag ensures the right ref
        is checked out without an extra checkout step.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertRegex(
            pipeline_source,
            r"git\s+clone\s+.*--depth\s+1.*--branch|git\s+clone\s+.*--branch.*--depth\s+1",
            msg=(
                "Pipeline must invoke 'git clone --depth 1 --branch \"$upgrade_ref\"' "
                "in the URL normalization block (FR-001). "
                "Add the clone invocation to scripts/bin/blueprint/upgrade_consumer_pipeline.sh."
            ),
        )

    def test_pipeline_usage_documents_auto_clone_behaviour(self) -> None:
        """Pipeline usage block MUST document the URL auto-clone behaviour (NFR-OPS-001).

        Without usage documentation, operators cannot discover the URL-form behaviour
        from '--help' output and may resort to manual workarounds.
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        self.assertRegex(
            pipeline_source,
            r"(?i)(auto.?clone|url.*clone|clone.*url|depth\s+1\s+clone)",
            msg=(
                "Pipeline usage block must document the auto-clone behaviour for "
                "URL-form BLUEPRINT_UPGRADE_SOURCE (NFR-OPS-001). "
                "Add a sentence describing URL detection and --depth 1 clone to the "
                "usage() function in upgrade_consumer_pipeline.sh."
            ),
        )

    def test_pipeline_local_path_does_not_trigger_auto_clone(self) -> None:
        """Local-path form of BLUEPRINT_UPGRADE_SOURCE MUST NOT trigger auto-clone (FR-004, AC-010).

        The '.git' directory guard must gate the clone block: when upgrade_source
        already points to a local .git directory, the pipeline must skip the clone
        path entirely and use upgrade_source as-is.  This test asserts the guard
        structure (not just presence of the clone invocation).
        """
        pipeline_source = _PIPELINE_PATH.read_text(encoding="utf-8")
        # Guard form: '! [[ -d "$upgrade_source/.git" ]]'
        self.assertRegex(
            pipeline_source,
            r'!\s+\[\[\s+-d',
            msg=(
                "Pipeline URL normalization block must use a '! [[ -d ... ]]' conditional guard "
                "so that git clone is skipped when upgrade_source is already a local .git directory "
                "(FR-004). Add '! [[ -d \"$upgrade_source/.git\" ]]' to wrap the clone invocation "
                "in scripts/bin/blueprint/upgrade_consumer_pipeline.sh."
            ),
        )


class EngineSkipCloneGuardTests(unittest.TestCase):
    """Assert that upgrade_consumer.py skips its internal clone for pre-cloned local paths (FR-003)."""

    def test_engine_fails_explicitly_when_ref_not_found_in_pre_cloned_source(self) -> None:
        """Engine MUST fail explicitly when args.ref cannot be resolved in the pre-cloned source (FR-003).

        Silently coercing None from _resolve_commit to "" allows the upgrade to
        proceed with an empty resolved_commit, corrupting downstream artifacts.
        The engine must emit an error message and return 1 instead.
        """
        engine_source = _ENGINE_PATH.read_text(encoding="utf-8")
        self.assertRegex(
            engine_source,
            r'resolved_commit\s+is\s+None|if\s+resolved_commit\s*is\s+None',
            msg=(
                "upgrade_consumer.py must check whether _resolve_commit returned None "
                "in the pre-cloned source branch and return 1 with a clear error message "
                "(FR-003). Replace 'or \"\"' with an explicit None check and early return."
            ),
        )

    def test_engine_skips_clone_when_source_is_local_git_dir(self) -> None:
        """Engine MUST skip _clone_source_repository when source is already a local .git dir (FR-003, AC-009).

        When the pipeline auto-clones a URL source, it passes the local clone path to the
        engine via BLUEPRINT_UPGRADE_SOURCE.  Without this guard, the engine clones again,
        wasting time and leaving a second tmp directory that is never cleaned up.
        """
        engine_source = _ENGINE_PATH.read_text(encoding="utf-8")
        self.assertRegex(
            engine_source,
            r'\.is_dir\(\).*\.git|is_dir.*source.*\.git|args\.source.*is_dir|Path.*source.*\.git.*is_dir',
            msg=(
                "upgrade_consumer.py must contain a guard that checks whether args.source "
                "is already a local directory with a .git subdirectory (FR-003). "
                "When the guard matches, skip _clone_source_repository and use the local "
                "path directly.  Add the guard before the _clone_source_repository call "
                "in the main() function of scripts/lib/blueprint/upgrade_consumer.py."
            ),
        )
