from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


INSTALL_SCRIPT_REL = Path("scripts/bin/blueprint/install_codex_skill.sh")
SHELL_LIB_DIR_REL = Path("scripts/lib/shell")
SKILL_NAME = "blueprint-consumer-upgrade"
TEMPLATE_SKILL_DIR_REL = Path(f"scripts/templates/consumer/init/.agents/skills/{SKILL_NAME}")


def _copy_file(relative_path: Path, destination_root: Path) -> None:
    source_path = REPO_ROOT / relative_path
    target_path = destination_root / relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)


class InstallCodexSkillTests(unittest.TestCase):
    def _prepare_minimal_repo(
        self,
        tmp_root: Path,
        *,
        include_repo_local_skill: bool,
        include_template_skill: bool,
    ) -> None:
        _copy_file(INSTALL_SCRIPT_REL, tmp_root)
        for shell_lib_path in sorted((REPO_ROOT / SHELL_LIB_DIR_REL).glob("*.sh")):
            relative_path = shell_lib_path.relative_to(REPO_ROOT)
            _copy_file(relative_path, tmp_root)

        if include_repo_local_skill:
            shutil.copytree(
                REPO_ROOT / f".agents/skills/{SKILL_NAME}",
                tmp_root / f".agents/skills/{SKILL_NAME}",
                dirs_exist_ok=True,
            )

        if include_template_skill:
            shutil.copytree(
                REPO_ROOT / TEMPLATE_SKILL_DIR_REL,
                tmp_root / TEMPLATE_SKILL_DIR_REL,
                dirs_exist_ok=True,
            )

    def _run_install(self, tmp_root: Path):
        return run_command(
            ["bash", str(tmp_root / INSTALL_SCRIPT_REL)],
            cwd=tmp_root,
            env={
                "BLUEPRINT_CODEX_SKILLS_DIR": str(tmp_root / "codex-skills"),
            },
        )

    def test_template_fallback_installs_skill_when_repo_local_source_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_minimal_repo(
                tmp_root,
                include_repo_local_skill=False,
                include_template_skill=True,
            )

            result = self._run_install(tmp_root)

            combined = f"{result.stdout}\n{result.stderr}"
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertIn("consumer template fallback", combined)
            installed_root = tmp_root / "codex-skills" / SKILL_NAME
            self.assertTrue((installed_root / "SKILL.md").is_file())
            self.assertTrue((installed_root / "agents/openai.yaml").is_file())
            self.assertTrue((installed_root / "references/manual_merge_checklist.md").is_file())
            script_path = installed_root / "scripts/resolve_latest_stable_ref.sh"
            self.assertTrue(script_path.is_file())
            self.assertTrue(script_path.stat().st_mode & 0o111)

    def test_missing_sources_fail_with_remediation_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_minimal_repo(
                tmp_root,
                include_repo_local_skill=False,
                include_template_skill=False,
            )

            result = self._run_install(tmp_root)

            combined = f"{result.stdout}\n{result.stderr}"
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skill source not found", combined)
            self.assertIn("BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds", combined)


if __name__ == "__main__":
    unittest.main()
