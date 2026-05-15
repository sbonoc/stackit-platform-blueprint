"""Tests for check_workaround_manifest.py — issue-296-workaround-manifest-action-path-check.

AC-001: checker exits 0 for a manifest whose action_path files all exist.
AC-002: checker exits 1 with [quality-workaround-manifest-check]-prefixed stderr for a missing file.
NFR-REL-001: checker exits non-zero with clear message when manifest.yaml is absent.
AC-004(c): all real v1.10.0 entries in the live manifest resolve to existing files on disk.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = REPO_ROOT / "scripts/bin/quality/check_workaround_manifest.py"


def _load_checker():
    name = "check_workaround_manifest_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _SCRIPT_PATH)
    assert spec and spec.loader, f"checker script not found at {_SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ---------------------------------------------------------------------------
# AC-001 — valid manifest, all files present → exit 0
# ---------------------------------------------------------------------------


class TestValidManifest:
    """AC-001: exits 0 for a manifest whose action_path files all exist."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def test_all_files_present_exits_zero(
        self, checker, tmp_path: Path, monkeypatch
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)

        action_dir = workarounds_dir / "v1.0.0"
        action_dir.mkdir()
        (action_dir / "123_stub.yaml").write_text("---\n", encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.0.0": {
                    "workarounds": [
                        {
                            "id": "123",
                            "action_path": "workarounds/v1.0.0/123_stub.yaml",
                        }
                    ]
                }
            },
        }
        (workarounds_dir / "manifest.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 0

    def test_multiple_versions_all_present_exits_zero(
        self, checker, tmp_path: Path, monkeypatch
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        for version in ("v1.0.0", "v1.1.0"):
            d = workarounds_dir / version
            d.mkdir(parents=True)
            (d / "001_fix.patch").write_text("patch content\n", encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.0.0": {
                    "workarounds": [
                        {"id": "1", "action_path": "workarounds/v1.0.0/001_fix.patch"}
                    ]
                },
                "v1.1.0": {
                    "workarounds": [
                        {"id": "2", "action_path": "workarounds/v1.1.0/001_fix.patch"}
                    ]
                },
            },
        }
        (workarounds_dir / "manifest.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 0


# ---------------------------------------------------------------------------
# AC-002 — missing action_path file → exit 1 + prefixed stderr
# ---------------------------------------------------------------------------


class TestMissingActionPath:
    """AC-002: exits 1 with [quality-workaround-manifest-check]-prefixed stderr for a missing file."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def test_missing_file_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.0.0": {
                    "workarounds": [
                        {
                            "id": "999",
                            "action_path": "workarounds/v1.0.0/999_nonexistent.yaml",
                        }
                    ]
                }
            },
        }
        (workarounds_dir / "manifest.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        result = checker.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "[quality-workaround-manifest-check]" in captured.err
        assert "999_nonexistent.yaml" in captured.err

    def test_one_missing_among_valid_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        action_dir = workarounds_dir / "v1.0.0"
        action_dir.mkdir(parents=True)
        (action_dir / "001_present.yaml").write_text("---\n", encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "versions": {
                "v1.0.0": {
                    "workarounds": [
                        {"id": "1", "action_path": "workarounds/v1.0.0/001_present.yaml"},
                        {"id": "2", "action_path": "workarounds/v1.0.0/002_missing.yaml"},
                    ]
                }
            },
        }
        (workarounds_dir / "manifest.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        result = checker.main()
        assert result == 1
        assert "002_missing.yaml" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# NFR-REL-001 — manifest.yaml absent → exit non-zero with clear message
# ---------------------------------------------------------------------------


class TestAbsentManifest:
    """NFR-REL-001: exits non-zero with a clear message when manifest.yaml is absent."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def test_absent_manifest_exits_nonzero(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        skill_root.mkdir(parents=True)
        missing_manifest = skill_root / "workarounds" / "manifest.yaml"

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", missing_manifest)
        result = checker.main()
        assert result == 1
        assert "manifest" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# P1/P2 hardening — malformed action_path values → exit 1 + prefixed stderr
# ---------------------------------------------------------------------------


class TestMalformedActionPath:
    """Hardening: missing key, empty value, absolute path, traversal escape all exit 1."""

    @pytest.fixture
    def checker(self):
        return _load_checker()

    def _write_manifest(self, workarounds_dir: Path, workarounds: list) -> None:
        manifest = {
            "schema_version": 1,
            "versions": {"v1.0.0": {"workarounds": workarounds}},
        }
        (workarounds_dir / "manifest.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )

    def test_missing_action_path_key_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)
        self._write_manifest(workarounds_dir, [{"id": "1"}])  # no action_path key

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 1
        assert "[quality-workaround-manifest-check]" in capsys.readouterr().err

    def test_empty_action_path_value_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)
        self._write_manifest(workarounds_dir, [{"id": "2", "action_path": ""}])

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 1
        assert "[quality-workaround-manifest-check]" in capsys.readouterr().err

    def test_absolute_action_path_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)
        self._write_manifest(
            workarounds_dir, [{"id": "3", "action_path": "/etc/passwd"}]
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 1
        assert "[quality-workaround-manifest-check]" in capsys.readouterr().err

    def test_traversal_action_path_exits_one(
        self, checker, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        skill_root = tmp_path / ".agents" / "skills" / "blueprint-consumer-upgrade"
        workarounds_dir = skill_root / "workarounds"
        workarounds_dir.mkdir(parents=True)
        # Create a file that traversal would reach — should still fail because it escapes skill_root
        escape_target = tmp_path / "outside.yaml"
        escape_target.write_text("---\n", encoding="utf-8")
        self._write_manifest(
            workarounds_dir,
            [{"id": "4", "action_path": "../../../outside.yaml"}],
        )

        monkeypatch.setattr(checker, "SKILL_ROOT", skill_root)
        monkeypatch.setattr(checker, "MANIFEST_PATH", workarounds_dir / "manifest.yaml")
        assert checker.main() == 1
        assert "[quality-workaround-manifest-check]" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# AC-004(c) — live manifest: all real entries resolve to existing files
# ---------------------------------------------------------------------------


class TestLiveManifest:
    """AC-004(c): all real v1.10.0 entries in the live manifest resolve to existing files."""

    def test_live_manifest_all_action_paths_exist(self) -> None:
        skill_root = REPO_ROOT / ".agents" / "skills" / "blueprint-consumer-upgrade"
        manifest_path = skill_root / "workarounds" / "manifest.yaml"
        assert manifest_path.exists(), f"live manifest not found: {manifest_path}"

        content = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        missing = []
        for version, version_data in content.get("versions", {}).items():
            for entry in version_data.get("workarounds", []):
                action_path = entry.get("action_path", "")
                if not (skill_root / action_path).exists():
                    missing.append(f"{version}/{action_path}")

        assert not missing, f"live manifest has missing action_path files: {missing}"
