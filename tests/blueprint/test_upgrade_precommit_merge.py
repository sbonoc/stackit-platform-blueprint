from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.lib.blueprint import upgrade_consumer
from tests._shared.helpers import REPO_ROOT

FIXTURES = REPO_ROOT / "tests/blueprint/fixtures/upgrade_precommit"

SOURCE_BASELINE = (FIXTURES / "source_baseline.yaml").read_text(encoding="utf-8")
TARGET_CONSUMER_ADDED = (FIXTURES / "target_consumer_added.yaml").read_text(encoding="utf-8")
TARGET_CONSUMER_ADDED_MULTI = (FIXTURES / "target_consumer_added_multi.yaml").read_text(encoding="utf-8")
TARGET_MALFORMED = (FIXTURES / "target_malformed.yaml").read_text(encoding="utf-8")

# Syntactically invalid YAML (used inline — cannot live as a fixture file
# because the check-yaml pre-commit hook would reject it at commit time).
_YAML_SYNTAX_ERROR = "repos:\n  - {id: bad\n"

CONSUMER_HOOK_ID = "backend-test-unit-pre-push"
CONSUMER_HOOK_ID_1 = "touchpoints-test-unit-pre-push"
CONSUMER_HOOK_ID_2 = "backend-test-unit-pre-push"


def _merge(source: str, target: str, baseline: str | None = None) -> str:
    content, _ = upgrade_consumer._yaml_merge_precommit_hooks(source, target, baseline)
    return content


def _merge_ids(source: str, target: str, baseline: str | None = None) -> list[str]:
    _, ids = upgrade_consumer._yaml_merge_precommit_hooks(source, target, baseline)
    return ids


class TestYamlMergePrecommitHooks(unittest.TestCase):
    """T-101 through T-110: YAML-aware hook-preserving merge for .pre-commit-config.yaml."""

    def test_t101_consumer_only_hook_survives(self) -> None:
        """T-101: consumer hook ID absent from source appears in merged output."""
        merged = _merge(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        self.assertIn(CONSUMER_HOOK_ID, merged)

    def test_t101_preserved_ids_returned(self) -> None:
        """T-101 (supplemental): preserved hook IDs returned in tuple."""
        ids = _merge_ids(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        self.assertIn(CONSUMER_HOOK_ID, ids)

    def test_t102_consumer_hook_appended_after_last_blueprint_hook(self) -> None:
        """T-102: consumer-only hook appears after the last source-side hook in output."""
        merged = _merge(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        last_blueprint_pos = merged.rfind("quality-consumer-pre-push")
        consumer_pos = merged.find(CONSUMER_HOOK_ID)
        self.assertGreater(consumer_pos, last_blueprint_pos)

    def test_t103_multiple_consumer_hooks_all_preserved_in_order(self) -> None:
        """T-103: N>=2 consumer-only hooks all present in their original relative order."""
        merged = _merge(SOURCE_BASELINE, TARGET_CONSUMER_ADDED_MULTI)
        pos1 = merged.find(CONSUMER_HOOK_ID_1)
        pos2 = merged.find(CONSUMER_HOOK_ID_2)
        self.assertGreater(pos1, 0, "touchpoints hook must be present")
        self.assertGreater(pos2, 0, "backend hook must be present")
        self.assertLess(pos1, pos2, "touchpoints must appear before backend (original order)")

    def test_t104_missing_repos_key_raises_sentinel(self) -> None:
        """T-104 (structural): target missing 'repos' key raises PrecommitYamlParseError."""
        with self.assertRaises(upgrade_consumer.PrecommitYamlParseError):
            upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, TARGET_MALFORMED)

    def test_t104_malformed_source_raises_sentinel(self) -> None:
        """T-104 (source side): structurally invalid source raises PrecommitYamlParseError."""
        with self.assertRaises(upgrade_consumer.PrecommitYamlParseError):
            upgrade_consumer._yaml_merge_precommit_hooks(TARGET_MALFORMED, TARGET_CONSUMER_ADDED)

    def test_t104_yaml_syntax_error_raises_sentinel(self) -> None:
        """T-104 (yaml.YAMLError branch): syntactically unparsable YAML raises PrecommitYamlParseError."""
        with self.assertRaises(upgrade_consumer.PrecommitYamlParseError):
            upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, _YAML_SYNTAX_ERROR)

    def test_t105_idempotency(self) -> None:
        """T-105: applying merge to its own output returns the same string."""
        first_pass, _ = upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        second_pass, _ = upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, first_pass)
        self.assertEqual(first_pass, second_pass)

    def test_t107_no_duplicate_hook_on_second_upgrade(self) -> None:
        """T-107: consumer hook ID appears exactly once after running merge twice."""
        first_pass, _ = upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        second_pass, _ = upgrade_consumer._yaml_merge_precommit_hooks(SOURCE_BASELINE, first_pass)
        count = second_pass.count(CONSUMER_HOOK_ID)
        self.assertEqual(count, 1, f"expected 1 occurrence of {CONSUMER_HOOK_ID!r}, got {count}")

    def test_t108_write_summary_lists_preserved_hooks(self) -> None:
        """T-108: _write_summary includes preserved consumer hook IDs."""
        _, preserved_hooks = upgrade_consumer._yaml_merge_precommit_hooks(
            SOURCE_BASELINE, TARGET_CONSUMER_ADDED
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "upgrade_summary.md"
            repo_root = Path(tmpdir)

            upgrade_consumer._write_summary(
                summary_path=summary_path,
                repo_root=repo_root,
                source="git@github.com:test/blueprint.git",
                ref="v1.12.3",
                resolved_commit="abc1234",
                baseline_ref="v1.12.2",
                plan_summary={},
                apply_summary={},
                apply_enabled=True,
                results=[],
                required_manual_actions=[],
                entries=None,
                preserved_precommit_hooks=preserved_hooks,
            )

            summary_text = summary_path.read_text(encoding="utf-8")
            self.assertIn(CONSUMER_HOOK_ID, summary_text)
            self.assertIn("Preserved Consumer Hooks", summary_text)

    def test_t109_blueprint_hook_key_order_preserved(self) -> None:
        """T-109: yaml.dump with sort_keys=False preserves key order of blueprint hooks."""
        merged = _merge(SOURCE_BASELINE, TARGET_CONSUMER_ADDED)
        # The fixture defines hooks with 'id' before 'name' before 'language' before 'entry'.
        # With sort_keys=False those keys must not be reordered alphabetically.
        # 'entry' sorts before 'id' alphabetically; verify 'id' still comes before 'entry'.
        id_pos = merged.find("id: bash-syntax")
        entry_pos = merged.find("entry: bash -n")
        self.assertGreater(id_pos, 0, "id: bash-syntax must appear in merged output")
        self.assertGreater(entry_pos, 0, "entry: bash -n must appear in merged output")
        self.assertLess(id_pos, entry_pos, "id: must precede entry: (sort_keys=False)")

    def test_t110_baseline_hook_not_reinserted_after_removal(self) -> None:
        """T-110: a hook removed from blueprint source is not re-added even if consumer still has it."""
        # baseline has 'bash-syntax'; new source dropped it; consumer still diverged
        baseline_with_extra = SOURCE_BASELINE  # bash-syntax is in baseline
        new_source_without_bash = SOURCE_BASELINE.replace(
            "      - id: bash-syntax\n"
            "        name: bash syntax check\n"
            "        language: system\n"
            "        entry: bash -n\n"
            "        types: [shell]\n",
            "",
        )
        # consumer still has both the old baseline hook and a custom one
        merged = _merge(new_source_without_bash, TARGET_CONSUMER_ADDED, baseline_with_extra)
        # bash-syntax was in baseline → blueprint removal; must NOT appear in merged output
        self.assertNotIn("bash-syntax", merged)
        # custom consumer hook must still be preserved
        self.assertIn(CONSUMER_HOOK_ID, merged)


class TestClassifyEntriesPrecommit(unittest.TestCase):
    """T-106: _classify_entries returns merge-required for consumer-diverged .pre-commit-config.yaml."""

    def test_t106_classify_returns_merge_required_for_consumer_diverged(self) -> None:
        """T-106: consumer file with extra hook gets action=merge-required from _classify_entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            source_repo = tmp_root / "source"
            target_repo = tmp_root / "target"
            source_repo.mkdir()
            target_repo.mkdir()

            # Source repo: baseline .pre-commit-config.yaml
            _init_git_repo(source_repo)
            _write(source_repo / ".pre-commit-config.yaml", SOURCE_BASELINE)
            _commit_all(source_repo, "baseline")
            _git(source_repo, "tag", "v1.12.2")

            # Advance source to a new commit (simulate new blueprint version)
            _write(source_repo / ".pre-commit-config.yaml", SOURCE_BASELINE)
            _commit_all(source_repo, "head")

            # Target repo: consumer added a hook
            _init_git_repo(target_repo)
            _write(target_repo / ".pre-commit-config.yaml", TARGET_CONSUMER_ADDED)
            _commit_all(target_repo, "initial")

            baseline_ref = "v1.12.2"
            baseline_cache: dict[str, str | None] = {}

            entries = upgrade_consumer._classify_entries(
                repo_root=target_repo,
                source_repo=source_repo,
                all_paths=[".pre-commit-config.yaml"],
                required_files={".pre-commit-config.yaml"},
                source_only=set(),
                consumer_seeded=set(),
                init_managed=set(),
                conditional_entries=set(),
                managed_dir_roots=set(),
                protected_roots=set(),
                baseline_ref=baseline_ref,
                baseline_cache=baseline_cache,
                allow_delete=False,
            )

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].action, upgrade_consumer.ACTION_MERGE_REQUIRED)


def _init_git_repo(path: Path) -> None:
    import subprocess
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True, capture_output=True)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit_all(path: Path, message: str) -> None:
    import subprocess
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", message, "--allow-empty"],
        check=True,
        capture_output=True,
    )


def _git(path: Path, *args: str) -> None:
    import subprocess
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
