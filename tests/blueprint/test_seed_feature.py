from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests._shared.helpers import REPO_ROOT


_SEED_FEATURE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/seed_feature.py"

# Fails at module load time (ImportError) when seed_feature.py does not exist yet,
# making all tests in this file fail (red) until Slice 5 implements the script.
if not _SEED_FEATURE_SCRIPT.is_file():
    raise ImportError(
        f"scripts/bin/blueprint/seed_feature.py not found — implement Slice 5 first"
    )


def _load_seed_feature():
    spec = importlib.util.spec_from_file_location("seed_feature", _SEED_FEATURE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_source_repo(source_root: Path, gate_id: str, gate_paths: list[str]) -> None:
    """Populate a fake blueprint source with contract and templates for the gate."""
    contract_yaml = f"""\
spec:
  consumer_seeded_feature_gates:
    - id: {gate_id}
      enable_flag: CLAUDE_AI_ENABLED
      enabled_by_default: false
      consumer_seeded_paths_when_enabled:
{chr(10).join(f"        - {p}" for p in gate_paths)}
"""
    (source_root / "blueprint").mkdir(parents=True, exist_ok=True)
    (source_root / "blueprint/contract.yaml").write_text(contract_yaml, encoding="utf-8")

    for gate_path in gate_paths:
        tmpl_path = source_root / "scripts/templates/consumer/init" / f"{gate_path}.tmpl"
        tmpl_path.parent.mkdir(parents=True, exist_ok=True)
        tmpl_path.write_text(f"# seeded: {gate_path}\n", encoding="utf-8")


def _make_consumer_repo(consumer_root: Path) -> None:
    """Populate a minimal consumer repo directory."""
    (consumer_root / "blueprint").mkdir(parents=True, exist_ok=True)
    (consumer_root / "blueprint/repo.init.env").write_text(
        "BLUEPRINT_UPGRADE_REF=HEAD\n",
        encoding="utf-8",
    )


_GATE_ID = "claude_ai_integration"
_GATE_PATHS = [
    ".github/workflows/claude.yml",
    ".github/workflows/claude-code-review.yml",
]


class SeedFeatureTests(unittest.TestCase):

    def _call_main(self, argv: list[str], *, fake_source_root: Path, consumer_root: Path) -> int:
        sf = _load_seed_feature()
        with patch("sys.argv", [str(_SEED_FEATURE_SCRIPT)] + argv):
            # Patch the clone to return the pre-built fake source directory.
            with patch(
                "scripts.lib.blueprint.upgrade_consumer._clone_source_repository",
                return_value=(fake_source_root, fake_source_root / "source", "abc1234"),
            ):
                try:
                    sf.main()
                    return 0
                except SystemExit as exc:
                    return exc.code if exc.code is not None else 0

    def test_seed_feature_writes_gate_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            consumer_root = Path(tmpdir) / "consumer"
            source_root.mkdir()
            consumer_root.mkdir()

            _make_source_repo(source_root, _GATE_ID, _GATE_PATHS)
            _make_consumer_repo(consumer_root)

            exit_code = self._call_main(
                ["--feature", _GATE_ID, "--repo-root", str(consumer_root)],
                fake_source_root=source_root,
                consumer_root=consumer_root,
            )

            self.assertEqual(exit_code, 0, "seed-feature must exit 0 for a known gate")
            for gate_path in _GATE_PATHS:
                target = consumer_root / gate_path
                self.assertTrue(target.is_file(), f"gate path must exist after seed: {gate_path}")

    def test_seed_feature_unknown_gate_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            consumer_root = Path(tmpdir) / "consumer"
            source_root.mkdir()
            consumer_root.mkdir()

            _make_source_repo(source_root, _GATE_ID, _GATE_PATHS)
            _make_consumer_repo(consumer_root)

            exit_code = self._call_main(
                ["--feature", "nonexistent_gate_xyz", "--repo-root", str(consumer_root)],
                fake_source_root=source_root,
                consumer_root=consumer_root,
            )

            self.assertNotEqual(exit_code, 0, "unknown gate must produce non-zero exit")

    def test_seed_feature_missing_feature_param_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            consumer_root = Path(tmpdir) / "consumer"
            source_root.mkdir()
            consumer_root.mkdir()

            _make_source_repo(source_root, _GATE_ID, _GATE_PATHS)
            _make_consumer_repo(consumer_root)

            exit_code = self._call_main(
                ["--repo-root", str(consumer_root)],
                fake_source_root=source_root,
                consumer_root=consumer_root,
            )

            self.assertNotEqual(exit_code, 0, "missing --feature must produce non-zero exit")

    def test_seed_feature_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            consumer_root = Path(tmpdir) / "consumer"
            source_root.mkdir()
            consumer_root.mkdir()

            _make_source_repo(source_root, _GATE_ID, _GATE_PATHS)
            _make_consumer_repo(consumer_root)

            argv = ["--feature", _GATE_ID, "--repo-root", str(consumer_root)]

            first_code = self._call_main(argv, fake_source_root=source_root, consumer_root=consumer_root)
            self.assertEqual(first_code, 0, "first run must exit 0")

            first_contents = {
                p: (consumer_root / p).read_text(encoding="utf-8")
                for p in _GATE_PATHS
                if (consumer_root / p).is_file()
            }

            second_code = self._call_main(argv, fake_source_root=source_root, consumer_root=consumer_root)
            self.assertEqual(second_code, 0, "second run must also exit 0")

            for gate_path, original in first_contents.items():
                current = (consumer_root / gate_path).read_text(encoding="utf-8")
                self.assertEqual(current, original, f"file content must be identical on second run: {gate_path}")


if __name__ == "__main__":
    unittest.main()
