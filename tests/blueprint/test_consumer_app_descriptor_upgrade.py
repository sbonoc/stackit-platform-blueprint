"""Slice 4 — upgrade diagnostics + advisory artifact.

Covers FR-009 (descriptor-driven ownership in upgrade diagnostics), FR-011
(suggested descriptor artifact for existing consumers), AC-006 (upgrade
classification reports `consumer-app-descriptor`), AC-008 (suggested
artifact is human-readable + agent-editable).
"""
from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

import yaml

from scripts.lib.blueprint import upgrade_consumer


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _write_apps_kustomization(repo_root: Path, resources: list[str]) -> Path:
    body = "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources:\n" + "".join(
        f"  - {r}\n" for r in resources
    )
    return _write(repo_root / "infra/gitops/platform/base/apps/kustomization.yaml", body)


_BASELINE_DESCRIPTOR_BODY = """\
schemaVersion: v1
apps:
  - id: backend-api
    owner:
      team: platform
    components:
      - id: backend-api
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/backend-api-deployment.yaml
          service: infra/gitops/platform/base/apps/backend-api-service.yaml
"""


class DescriptorOwnershipPruneGuardTests(unittest.TestCase):
    """T-106 / FR-009 / AC-006: descriptor-listed paths report `consumer-app-descriptor`."""

    def test_descriptor_referenced_paths_returns_resolved_manifest_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(repo_root / "apps/descriptor.yaml", _BASELINE_DESCRIPTOR_BODY)
            paths = upgrade_consumer._descriptor_referenced_paths(repo_root)

        self.assertEqual(
            paths,
            {
                "infra/gitops/platform/base/apps/backend-api-deployment.yaml",
                "infra/gitops/platform/base/apps/backend-api-service.yaml",
            },
        )

    def test_descriptor_referenced_paths_returns_empty_set_when_descriptor_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = upgrade_consumer._descriptor_referenced_paths(Path(tmpdir))
        self.assertEqual(paths, set())

    def test_classify_descriptor_listed_path_marks_consumer_app_descriptor(self) -> None:
        """Path absent in source but listed in apps/descriptor.yaml → ownership consumer-app-descriptor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            source_repo = repo_root / "src"
            source_repo.mkdir()
            _write(repo_root / "apps/descriptor.yaml", _BASELINE_DESCRIPTOR_BODY)
            _write_apps_kustomization(
                repo_root,
                [
                    "backend-api-deployment.yaml",
                    "backend-api-service.yaml",
                ],
            )
            # Manifest file is in the consumer tree; absent from upstream source repo.
            target_path = repo_root / "infra/gitops/platform/base/apps/backend-api-deployment.yaml"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("kind: Deployment\nmetadata:\n  name: backend-api\n", encoding="utf-8")

            contract = mock.Mock()
            contract.repository.consumer_seeded_paths = []
            contract.repository.source_only_paths = []
            contract.repository.init_managed_paths = []
            contract.repository.required_files = []

            entries = upgrade_consumer._classify_entries(
                repo_root=repo_root,
                source_repo=source_repo,
                candidate_paths=["infra/gitops/platform/base/apps/backend-api-deployment.yaml"],
                required_files=set(),
                init_managed=set(),
                conditional_entries=[],
                managed_dir_roots=set(),
                consumer_seeded=set(),
                source_only=set(),
                allow_delete=True,
                baseline_ref=None,
                baseline_cache={},
            )

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.ownership, "consumer-app-descriptor")
        self.assertEqual(entry.action, upgrade_consumer.ACTION_SKIP)
        self.assertIn("descriptor", entry.reason.lower())

    def test_descriptor_guard_takes_precedence_over_kustomization_ref(self) -> None:
        """When a path is in both descriptor and kustomization, descriptor wins (more specific)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            source_repo = repo_root / "src"
            source_repo.mkdir()
            _write(repo_root / "apps/descriptor.yaml", _BASELINE_DESCRIPTOR_BODY)
            _write_apps_kustomization(
                repo_root,
                [
                    "backend-api-deployment.yaml",
                    "backend-api-service.yaml",
                ],
            )
            target_path = repo_root / "infra/gitops/platform/base/apps/backend-api-service.yaml"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("kind: Service\nmetadata:\n  name: backend-api\n", encoding="utf-8")

            entries = upgrade_consumer._classify_entries(
                repo_root=repo_root,
                source_repo=source_repo,
                candidate_paths=["infra/gitops/platform/base/apps/backend-api-service.yaml"],
                required_files=set(),
                init_managed=set(),
                conditional_entries=[],
                managed_dir_roots=set(),
                consumer_seeded=set(),
                source_only=set(),
                allow_delete=True,
                baseline_ref=None,
                baseline_cache={},
            )

        self.assertEqual(entries[0].ownership, "consumer-app-descriptor")

    def test_apply_summary_counts_consumer_app_descriptor(self) -> None:
        entries = [
            upgrade_consumer.UpgradeEntry(
                path="x", ownership="consumer-app-descriptor",
                action=upgrade_consumer.ACTION_SKIP, operation=upgrade_consumer.OPERATION_NONE,
                reason="test", source_exists=False, target_exists=True,
                baseline_ref=None, baseline_content_available=False,
            ),
            upgrade_consumer.UpgradeEntry(
                path="y", ownership="consumer-kustomization-ref",
                action=upgrade_consumer.ACTION_SKIP, operation=upgrade_consumer.OPERATION_NONE,
                reason="test", source_exists=False, target_exists=True,
                baseline_ref=None, baseline_content_available=False,
            ),
            upgrade_consumer.UpgradeEntry(
                path="z", ownership="consumer-app-descriptor",
                action=upgrade_consumer.ACTION_SKIP, operation=upgrade_consumer.OPERATION_NONE,
                reason="test", source_exists=False, target_exists=True,
                baseline_ref=None, baseline_content_available=False,
            ),
        ]
        summary = upgrade_consumer._summarize_apply([], 0, [], entries=entries)
        self.assertEqual(summary["consumer_app_descriptor_count"], 2)
        self.assertEqual(summary["consumer_kustomization_ref_count"], 1)


class SuggestedDescriptorArtifactTests(unittest.TestCase):
    """T-107 / FR-011 / AC-008: suggested descriptor for consumers without apps/descriptor.yaml."""

    def test_suggested_descriptor_groups_kustomization_resources_by_component_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_apps_kustomization(
                repo_root,
                [
                    "backend-api-deployment.yaml",
                    "backend-api-service.yaml",
                    "marketplace-api-deployment.yaml",
                    "marketplace-api-service.yaml",
                ],
            )
            content = upgrade_consumer.generate_suggested_descriptor(repo_root)

        self.assertIsNotNone(content)
        parsed = yaml.safe_load(content)
        self.assertEqual(parsed["schemaVersion"], "v1")
        ids = sorted(app["id"] for app in parsed["apps"])
        self.assertEqual(ids, ["backend-api", "marketplace-api"])
        backend = next(app for app in parsed["apps"] if app["id"] == "backend-api")
        component = backend["components"][0]
        self.assertEqual(
            component["manifests"]["deployment"],
            "infra/gitops/platform/base/apps/backend-api-deployment.yaml",
        )
        self.assertEqual(
            component["manifests"]["service"],
            "infra/gitops/platform/base/apps/backend-api-service.yaml",
        )

    def test_suggested_descriptor_includes_review_guidance_comments(self) -> None:
        """AC-008: suggested artifact must guide human and agent review before adoption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_apps_kustomization(repo_root, ["backend-api-deployment.yaml"])
            content = upgrade_consumer.generate_suggested_descriptor(repo_root)

        self.assertIsNotNone(content)
        # Comment lines guide review (e.g., "review and edit", "TODO" markers)
        comment_lines = [line for line in content.splitlines() if line.lstrip().startswith("#")]
        self.assertGreaterEqual(len(comment_lines), 1, "suggested descriptor must include review guidance comments")
        comment_blob = "\n".join(comment_lines).lower()
        self.assertTrue(
            "review" in comment_blob or "edit" in comment_blob,
            f"comments must mention review/edit guidance; got:\n{comment_blob}",
        )
        # TODO marker on owner.team makes the editable spot obvious
        self.assertIn("TODO", content)

    def test_suggested_descriptor_returns_none_when_no_apps_kustomization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsNone(upgrade_consumer.generate_suggested_descriptor(Path(tmpdir)))

    def test_suggested_descriptor_returns_none_when_kustomization_has_no_workloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_apps_kustomization(repo_root, [])  # no resources
            self.assertIsNone(upgrade_consumer.generate_suggested_descriptor(repo_root))

    def test_suggested_descriptor_includes_only_component_with_deployment_manifest(self) -> None:
        """Stray resources that don't follow the {id}-deployment.yaml pattern are skipped silently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_apps_kustomization(
                repo_root,
                [
                    "backend-api-deployment.yaml",
                    "backend-api-service.yaml",
                    "shared-config.yaml",  # not a deployment/service — should be ignored
                ],
            )
            content = upgrade_consumer.generate_suggested_descriptor(repo_root)
        parsed = yaml.safe_load(content)
        ids = [app["id"] for app in parsed["apps"]]
        self.assertEqual(ids, ["backend-api"])

    def test_apply_writes_suggested_descriptor_when_descriptor_absent(self) -> None:
        """T-007 wiring: write_suggested_descriptor_artifact emits the file under artifacts/blueprint/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_apps_kustomization(repo_root, ["backend-api-deployment.yaml"])
            artifact_path = upgrade_consumer.write_suggested_descriptor_artifact(repo_root)

        self.assertIsNotNone(artifact_path)
        self.assertTrue(artifact_path.is_file())
        self.assertEqual(
            artifact_path.relative_to(repo_root).as_posix(),
            "artifacts/blueprint/app_descriptor.suggested.yaml",
        )
        # Critical: must NOT write to the consumer working tree
        self.assertFalse((repo_root / "apps/descriptor.yaml").exists())

    def test_apply_skips_suggested_descriptor_when_descriptor_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write(repo_root / "apps/descriptor.yaml", _BASELINE_DESCRIPTOR_BODY)
            _write_apps_kustomization(repo_root, ["backend-api-deployment.yaml"])
            artifact_path = upgrade_consumer.write_suggested_descriptor_artifact(repo_root)
        self.assertIsNone(artifact_path)


if __name__ == "__main__":
    unittest.main()
