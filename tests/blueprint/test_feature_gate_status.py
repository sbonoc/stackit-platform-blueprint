from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/feature_gate_status.py"

if not _SCRIPT.is_file():
    raise ImportError(
        "scripts/bin/blueprint/feature_gate_status.py not found — implement Slice 8 first"
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("feature_gate_status", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GATE_ID = "claude_ai_integration"
_GATE_DESCRIPTION = "Seed Claude Code Review GitHub Actions workflows."
_GATE_PATHS = [
    ".github/workflows/claude.yml",
    ".github/workflows/claude-code-review.yml",
]


def _make_consumer_repo(
    root: Path,
    *,
    repo_init_env: str = "BLUEPRINT_UPGRADE_REF=HEAD\n",
) -> None:
    (root / "blueprint").mkdir(parents=True, exist_ok=True)
    (root / "blueprint/repo.init.env").write_text(repo_init_env, encoding="utf-8")
    contract = f"""\
spec:
  toggles:
    CLAUDE_AI_ENABLED: false
  consumer_seeded_paths:
    - .github/workflows/claude.yml
    - .github/workflows/claude-code-review.yml
  consumer_seeded_feature_gates:
    - id: {_GATE_ID}
      enable_flag: CLAUDE_AI_ENABLED
      enabled_by_default: false
      description: "{_GATE_DESCRIPTION}"
      consumer_seeded_paths_when_enabled:
{chr(10).join(f"        - {p}" for p in _GATE_PATHS)}
"""
    (root / "blueprint/contract.yaml").write_text(contract, encoding="utf-8")


def _call_main(repo_root: Path, *, env_overrides: dict | None = None) -> int:
    m = _load_module()
    import os

    saved = {}
    overrides = env_overrides or {}
    for k, v in overrides.items():
        saved[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        with unittest.mock.patch("sys.argv", [str(_SCRIPT), "--repo-root", str(repo_root)]):
            try:
                m.main()
                return 0
            except SystemExit as exc:
                return exc.code if exc.code is not None else 0
    finally:
        for k, original in saved.items():
            if original is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = original


import unittest.mock  # noqa: E402 (needed after _call_main definition)


class FeatureGateStatusTests(unittest.TestCase):

    def test_gate_status_unadopted_writes_backlog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_consumer_repo(root)

            exit_code = _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})

            self.assertEqual(exit_code, 0, "feature-gate-status must exit 0")
            backlog = root / "AGENTS.backlog.md"
            self.assertTrue(backlog.is_file(), "AGENTS.backlog.md must be created")
            content = backlog.read_text(encoding="utf-8")
            self.assertIn(f"(blueprint-feature) seed: {_GATE_ID}", content)
            self.assertIn("command:", content)
            self.assertIn(f"blueprint-seed-feature FEATURE={_GATE_ID}", content)
            self.assertIn("description:", content)

    def test_gate_status_idempotent_no_duplicate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_consumer_repo(root)

            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})
            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})

            content = (root / "AGENTS.backlog.md").read_text(encoding="utf-8")
            count = content.count(f"(blueprint-feature) seed: {_GATE_ID}")
            self.assertEqual(count, 1, "duplicate backlog entries must not appear on second run")

    def test_gate_status_adopted_via_env_marks_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_consumer_repo(
                root,
                repo_init_env="BLUEPRINT_UPGRADE_REF=HEAD\nCLAUDE_AI_ENABLED=true\n",
            )

            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})

            backlog = root / "AGENTS.backlog.md"
            if backlog.is_file():
                content = backlog.read_text(encoding="utf-8")
                # Must NOT have an open entry for this gate
                self.assertNotIn(f"- [ ] (blueprint-feature) seed: {_GATE_ID}", content)

    def test_gate_status_adopted_via_file_marks_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_consumer_repo(root)

            # Create the gate paths so adoption is detected via file presence
            for gate_path in _GATE_PATHS:
                target = root / gate_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# seeded\n", encoding="utf-8")

            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})

            backlog = root / "AGENTS.backlog.md"
            if backlog.is_file():
                content = backlog.read_text(encoding="utf-8")
                self.assertNotIn(f"- [ ] (blueprint-feature) seed: {_GATE_ID}", content)

    def test_gate_status_exits_zero_always(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Minimal repo — no contract at all (edge case)
            (root / "blueprint").mkdir(parents=True, exist_ok=True)
            (root / "blueprint/repo.init.env").write_text("BLUEPRINT_UPGRADE_REF=HEAD\n", encoding="utf-8")
            (root / "blueprint/contract.yaml").write_text("spec: {}\n", encoding="utf-8")

            exit_code = _call_main(root)

            self.assertEqual(exit_code, 0, "feature-gate-status must always exit 0")

    def test_gate_status_existing_open_entry_marked_done_on_adoption(self):
        """Open backlog entry from a prior run gets marked [x] when gate is later adopted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _make_consumer_repo(root)

            # First run: gate unadopted → open entry written
            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})
            content = (root / "AGENTS.backlog.md").read_text(encoding="utf-8")
            self.assertIn(f"- [ ] (blueprint-feature) seed: {_GATE_ID}", content)

            # Adopt: create gate files
            for gate_path in _GATE_PATHS:
                target = root / gate_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# seeded\n", encoding="utf-8")

            # Second run: gate now adopted → entry must be marked [x]
            _call_main(root, env_overrides={"CLAUDE_AI_ENABLED": None})
            content = (root / "AGENTS.backlog.md").read_text(encoding="utf-8")
            self.assertIn(f"- [x] (blueprint-feature) seed: {_GATE_ID}", content)
            self.assertNotIn(f"- [ ] (blueprint-feature) seed: {_GATE_ID}", content)


if __name__ == "__main__":
    unittest.main()
