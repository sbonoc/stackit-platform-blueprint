from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from tests._shared.exec import run_command
from tests._shared.helpers import REPO_ROOT


INSTALL_SCRIPT_REL = Path("scripts/bin/blueprint/install_codex_skill.sh")
SHELL_LIB_DIR_REL = Path("scripts/lib/shell")
MAKEFILE_REL = Path("Makefile")
UPGRADE_SKILL_NAME = "blueprint-consumer-upgrade"
OPS_SKILL_NAME = "blueprint-consumer-ops"


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
        skill_name: str,
        include_repo_local_skill: bool,
        include_template_skill: bool,
    ) -> None:
        _copy_file(MAKEFILE_REL, tmp_root)
        _copy_file(INSTALL_SCRIPT_REL, tmp_root)
        for shell_lib_path in sorted((REPO_ROOT / SHELL_LIB_DIR_REL).glob("*.sh")):
            relative_path = shell_lib_path.relative_to(REPO_ROOT)
            _copy_file(relative_path, tmp_root)

        if include_repo_local_skill:
            shutil.copytree(
                REPO_ROOT / f".agents/skills/{skill_name}",
                tmp_root / f".agents/skills/{skill_name}",
                dirs_exist_ok=True,
            )

        if include_template_skill:
            template_skill_dir = Path(f"scripts/templates/consumer/init/.agents/skills/{skill_name}")
            shutil.copytree(
                REPO_ROOT / template_skill_dir,
                tmp_root / template_skill_dir,
                dirs_exist_ok=True,
            )

    def _run_install(self, tmp_root: Path, *, skill_name: str):
        return run_command(
            ["bash", str(tmp_root / INSTALL_SCRIPT_REL)],
            cwd=tmp_root,
            env={
                "BLUEPRINT_CODEX_SKILL_NAME": skill_name,
                "BLUEPRINT_CODEX_SKILLS_DIR": str(tmp_root / "codex-skills"),
            },
        )

    def test_template_fallback_installs_supported_skills_when_repo_local_source_missing(self) -> None:
        for skill_name in (UPGRADE_SKILL_NAME, OPS_SKILL_NAME):
            with self.subTest(skill_name=skill_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_root = Path(tmpdir)
                    self._prepare_minimal_repo(
                        tmp_root,
                        skill_name=skill_name,
                        include_repo_local_skill=False,
                        include_template_skill=True,
                    )

                    result = self._run_install(tmp_root, skill_name=skill_name)

                    combined = f"{result.stdout}\n{result.stderr}"
                    self.assertEqual(result.returncode, 0, msg=combined)
                    self.assertIn("consumer template fallback", combined)
                    installed_root = tmp_root / "codex-skills" / skill_name
                    self.assertTrue((installed_root / "SKILL.md").is_file())
                    self.assertTrue((installed_root / "agents/openai.yaml").is_file())
                    if skill_name == UPGRADE_SKILL_NAME:
                        self.assertTrue((installed_root / "references/manual_merge_checklist.md").is_file())
                        script_path = installed_root / "scripts/resolve_latest_stable_ref.sh"
                        self.assertTrue(script_path.is_file())
                        self.assertTrue(script_path.stat().st_mode & 0o111)
                    else:
                        self.assertTrue((installed_root / "references/consumer_ops_checklist.md").is_file())

    def test_missing_sources_fail_with_remediation_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            self._prepare_minimal_repo(
                tmp_root,
                skill_name=OPS_SKILL_NAME,
                include_repo_local_skill=False,
                include_template_skill=False,
            )

            result = self._run_install(tmp_root, skill_name=OPS_SKILL_NAME)

            combined = f"{result.stdout}\n{result.stderr}"
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skill source not found", combined)
            self.assertIn("BLUEPRINT_RESYNC_APPLY_SAFE=true make blueprint-resync-consumer-seeds", combined)


if __name__ == "__main__":
    unittest.main()
