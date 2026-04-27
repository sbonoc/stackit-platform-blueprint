"""Slice 3 — descriptor-driven app catalog manifest rendering.

Covers FR-005 (multi-component), FR-007 (descriptor-driven `deliveryTopology.workloads`
and `runtimeDeliveryContract.gitopsWorkloads`), FR-008 (catalog stays as compatibility
artifact — actual deprecation diagnostics live in S5), AC-005 (no hardcoded baseline
ID dependency in renderer logic), AC-007 (baseline smoke scenarios still pass).
"""
from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from scripts.lib.platform.apps import catalog_scaffold_renderer


def _write_descriptor(repo_root: Path, body: str) -> Path:
    descriptor_path = repo_root / "apps" / "descriptor.yaml"
    descriptor_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor_path.write_text(textwrap.dedent(body), encoding="utf-8")
    return descriptor_path


_BASELINE_DESCRIPTOR = """\
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
        service:
          port: 8080
        health:
          readiness: /
  - id: touchpoints-web
    owner:
      team: platform
    components:
      - id: touchpoints-web
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml
          service: infra/gitops/platform/base/apps/touchpoints-web-service.yaml
        service:
          port: 80
        health:
          readiness: /
"""

_NON_BASELINE_DESCRIPTOR = """\
schemaVersion: v1
apps:
  - id: marketplace
    owner:
      team: marketplace
    components:
      - id: marketplace-api
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/marketplace-api-deployment.yaml
          service: infra/gitops/platform/base/apps/marketplace-api-service.yaml
        service:
          port: 9090
      - id: marketplace-worker
        kind: Deployment
        manifests:
          deployment: infra/gitops/platform/base/apps/marketplace-worker-deployment.yaml
          service: infra/gitops/platform/base/apps/marketplace-worker-service.yaml
        service:
          port: 7070
"""


class DescriptorWorkloadBlockRenderingTests(unittest.TestCase):
    """Block-rendering helpers iterate descriptor components — no hardcoded baseline IDs."""

    def test_render_delivery_workloads_block_emits_one_entry_per_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(Path(tmpdir), _NON_BASELINE_DESCRIPTOR)
            descriptor, errors = catalog_scaffold_renderer._load_descriptor(descriptor_path)

        self.assertEqual(errors, [])
        component_image_map = {
            "marketplace-api": "marketplace/api:1.0",
            "marketplace-worker": "marketplace/worker:1.0",
        }
        component_image_env_var_map = {
            "marketplace-api": "MARKETPLACE_API_IMAGE",
            "marketplace-worker": "MARKETPLACE_WORKER_IMAGE",
        }
        block = catalog_scaffold_renderer.render_delivery_workloads_block(
            descriptor.components, component_image_map
        )
        parsed = yaml.safe_load("workloads:\n" + block)["workloads"]
        ids = [w["workloadId"] for w in parsed]
        self.assertEqual(ids, ["marketplace-api", "marketplace-worker"])
        for entry in parsed:
            self.assertIn(entry["workloadId"], component_image_map)
            self.assertEqual(entry["image"], component_image_map[entry["workloadId"]])
            self.assertEqual(entry["kind"], "Deployment")
            self.assertEqual(entry["namespace"], "apps")
        self.assertEqual(parsed[0]["servicePort"], 9090)
        self.assertEqual(parsed[1]["servicePort"], 7070)

    def test_render_gitops_workloads_block_uses_descriptor_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            descriptor_path = _write_descriptor(Path(tmpdir), _NON_BASELINE_DESCRIPTOR)
            descriptor, _ = catalog_scaffold_renderer._load_descriptor(descriptor_path)

        component_image_map = {
            "marketplace-api": "marketplace/api:1.0",
            "marketplace-worker": "marketplace/worker:1.0",
        }
        component_image_env_var_map = {
            "marketplace-api": "MARKETPLACE_API_IMAGE",
            "marketplace-worker": "MARKETPLACE_WORKER_IMAGE",
        }
        block = catalog_scaffold_renderer.render_gitops_workloads_block(
            descriptor.components, component_image_map, component_image_env_var_map
        )
        parsed = yaml.safe_load("gitopsWorkloads:\n" + block)["gitopsWorkloads"]
        ids = [w["id"] for w in parsed]
        self.assertEqual(ids, ["marketplace-api", "marketplace-worker"])
        self.assertEqual(
            parsed[0]["deploymentManifest"],
            "infra/gitops/platform/base/apps/marketplace-api-deployment.yaml",
        )
        self.assertEqual(
            parsed[0]["serviceManifest"],
            "infra/gitops/platform/base/apps/marketplace-api-service.yaml",
        )
        self.assertEqual(parsed[0]["imageEnvVar"], "MARKETPLACE_API_IMAGE")
        self.assertEqual(parsed[0]["defaultImage"], "marketplace/api:1.0")

    def test_renderer_module_has_no_hardcoded_baseline_ids(self) -> None:
        """AC-005: renderer logic must not name `backend-api` or `touchpoints-web`."""
        source = Path(catalog_scaffold_renderer.__file__).read_text(encoding="utf-8")
        for hardcoded in ("backend-api-deployment.yaml", "touchpoints-web-deployment.yaml"):
            self.assertNotIn(
                hardcoded,
                source,
                f"renderer must not hardcode baseline manifest filename {hardcoded!r}",
            )
        for hardcoded_id in ('"backend-api"', "'backend-api'", '"touchpoints-web"', "'touchpoints-web'"):
            self.assertNotIn(
                hardcoded_id,
                source,
                f"renderer must not hardcode baseline component ID literal {hardcoded_id}",
            )


class CatalogManifestEndToEndRenderingTests(unittest.TestCase):
    """End-to-end render via `cmd_render` with descriptor + per-component image map."""

    @staticmethod
    def _baseline_render_args(
        repo_root: Path,
        descriptor_path: Path,
        manifest_template_path: Path,
        versions_template_path: Path,
        manifest_output: Path,
        versions_output: Path,
        component_images: list[str],
        component_image_env_vars: list[str],
    ):
        import argparse

        return argparse.Namespace(
            command="render",
            manifest_template=str(manifest_template_path),
            versions_template=str(versions_template_path),
            manifest_output=str(manifest_output),
            versions_output=str(versions_output),
            python_runtime_base_image_version="3.14-slim",
            node_runtime_base_image_version="22-slim",
            nginx_runtime_base_image_version="1.27-alpine",
            fastapi_version="0.115.4",
            pydantic_version="2.9.2",
            vue_version="3.5.0",
            vue_router_version="4.4.0",
            pinia_version="2.2.0",
            app_runtime_gitops_enabled=True,
            observability_enabled=False,
            otel_exporter_otlp_endpoint="",
            otel_protocol="",
            otel_traces_enabled=False,
            otel_metrics_enabled=False,
            otel_logs_enabled=False,
            faro_enabled=False,
            faro_collect_path="",
            app_descriptor_path=str(descriptor_path),
            component_image=component_images,
            component_image_env_var=component_image_env_vars,
            func=catalog_scaffold_renderer.cmd_render,
        )

    def _baseline_template_paths(self) -> tuple[Path, Path]:
        from tests._shared.helpers import REPO_ROOT

        return (
            REPO_ROOT / "scripts/templates/platform/apps/catalog/manifest.yaml.tmpl",
            REPO_ROOT / "scripts/templates/platform/apps/catalog/versions.lock.tmpl",
        )

    def test_baseline_descriptor_renders_two_workloads_with_baseline_ids(self) -> None:
        """AC-007: the baseline descriptor still renders the two baseline workloads end-to-end."""
        manifest_tmpl, versions_tmpl = self._baseline_template_paths()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            descriptor_path = _write_descriptor(tmp_root, _BASELINE_DESCRIPTOR)
            manifest_output = tmp_root / "apps/catalog/manifest.yaml"
            versions_output = tmp_root / "apps/catalog/versions.lock"
            args = self._baseline_render_args(
                tmp_root,
                descriptor_path,
                manifest_tmpl,
                versions_tmpl,
                manifest_output,
                versions_output,
                component_images=[
                    "backend-api=python:3.14-slim",
                    "touchpoints-web=nginx:1.27-alpine",
                ],
                component_image_env_vars=[
                    "backend-api=APP_RUNTIME_BACKEND_IMAGE",
                    "touchpoints-web=APP_RUNTIME_TOUCHPOINTS_IMAGE",
                ],
            )
            rc = catalog_scaffold_renderer.cmd_render(args)
            self.assertEqual(rc, 0)
            manifest = yaml.safe_load(manifest_output.read_text(encoding="utf-8"))
        workload_ids = [w["workloadId"] for w in manifest["deliveryTopology"]["workloads"]]
        self.assertEqual(workload_ids, ["backend-api", "touchpoints-web"])
        gitops_ids = [w["id"] for w in manifest["runtimeDeliveryContract"]["gitopsWorkloads"]]
        self.assertEqual(gitops_ids, ["backend-api", "touchpoints-web"])

    def test_non_baseline_descriptor_renders_descriptor_components(self) -> None:
        """FR-007 + AC-005: a marketplace descriptor renders marketplace workloads end-to-end."""
        manifest_tmpl, versions_tmpl = self._baseline_template_paths()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            descriptor_path = _write_descriptor(tmp_root, _NON_BASELINE_DESCRIPTOR)
            manifest_output = tmp_root / "apps/catalog/manifest.yaml"
            versions_output = tmp_root / "apps/catalog/versions.lock"
            args = self._baseline_render_args(
                tmp_root,
                descriptor_path,
                manifest_tmpl,
                versions_tmpl,
                manifest_output,
                versions_output,
                component_images=[
                    "marketplace-api=marketplace/api:1.0",
                    "marketplace-worker=marketplace/worker:1.0",
                ],
                component_image_env_vars=[
                    "marketplace-api=MARKETPLACE_API_IMAGE",
                    "marketplace-worker=MARKETPLACE_WORKER_IMAGE",
                ],
            )
            rc = catalog_scaffold_renderer.cmd_render(args)
            self.assertEqual(rc, 0)
            manifest_text = manifest_output.read_text(encoding="utf-8")
        self.assertIn("marketplace-api-deployment.yaml", manifest_text)
        self.assertIn("marketplace-worker-deployment.yaml", manifest_text)
        self.assertNotIn("backend-api-deployment.yaml", manifest_text)
        self.assertNotIn("touchpoints-web-deployment.yaml", manifest_text)
        manifest = yaml.safe_load(manifest_text)
        gitops_workloads = manifest["runtimeDeliveryContract"]["gitopsWorkloads"]
        self.assertEqual(len(gitops_workloads), 2)
        self.assertEqual(gitops_workloads[0]["imageEnvVar"], "MARKETPLACE_API_IMAGE")

    def test_missing_descriptor_raises_deterministic_error(self) -> None:
        manifest_tmpl, versions_tmpl = self._baseline_template_paths()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            descriptor_path = tmp_root / "apps/descriptor.yaml"  # not created
            args = self._baseline_render_args(
                tmp_root,
                descriptor_path,
                manifest_tmpl,
                versions_tmpl,
                tmp_root / "apps/catalog/manifest.yaml",
                tmp_root / "apps/catalog/versions.lock",
                component_images=["backend-api=x", "touchpoints-web=y"],
                component_image_env_vars=[
                    "backend-api=APP_RUNTIME_BACKEND_IMAGE",
                    "touchpoints-web=APP_RUNTIME_TOUCHPOINTS_IMAGE",
                ],
            )
            with self.assertRaises(ValueError) as cm:
                catalog_scaffold_renderer.cmd_render(args)
        self.assertIn("descriptor", str(cm.exception).lower())

    def test_descriptor_component_without_image_mapping_falls_back_with_warning(self) -> None:
        """Codex P1 fix: missing per-component mapping renders with empty image + derived
        env-var name and emits a stderr warning naming the affected components, instead of
        hard-failing the render. This unblocks `make apps-bootstrap` for new components added
        to apps/descriptor.yaml without requiring concurrent bootstrap.sh edits."""
        import io
        from contextlib import redirect_stderr

        manifest_tmpl, versions_tmpl = self._baseline_template_paths()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            descriptor_path = _write_descriptor(tmp_root, _NON_BASELINE_DESCRIPTOR)
            manifest_output = tmp_root / "apps/catalog/manifest.yaml"
            args = self._baseline_render_args(
                tmp_root,
                descriptor_path,
                manifest_tmpl,
                versions_tmpl,
                manifest_output,
                tmp_root / "apps/catalog/versions.lock",
                component_images=["marketplace-api=marketplace/api:1.0"],  # missing marketplace-worker
                component_image_env_vars=[],  # all derived
            )
            stderr_buf = io.StringIO()
            with redirect_stderr(stderr_buf):
                rc = catalog_scaffold_renderer.cmd_render(args)
            self.assertEqual(rc, 0)
            manifest_text = manifest_output.read_text(encoding="utf-8")
            stderr_text = stderr_buf.getvalue()

        # Mapped component renders normally
        self.assertIn("defaultImage: marketplace/api:1.0", manifest_text)
        # Unmapped component falls back: env var derived from component_id
        self.assertIn("imageEnvVar: APP_RUNTIME_MARKETPLACE_WORKER_IMAGE", manifest_text)
        # Stderr warning names the affected component(s)
        self.assertIn("warning", stderr_text.lower())
        self.assertIn("marketplace-worker", stderr_text)

    def test_descriptor_component_with_explicit_env_var_override_wins(self) -> None:
        """Explicit --component-image-env-var must override the derived default."""
        manifest_tmpl, versions_tmpl = self._baseline_template_paths()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            descriptor_path = _write_descriptor(tmp_root, _BASELINE_DESCRIPTOR)
            manifest_output = tmp_root / "apps/catalog/manifest.yaml"
            args = self._baseline_render_args(
                tmp_root,
                descriptor_path,
                manifest_tmpl,
                versions_tmpl,
                manifest_output,
                tmp_root / "apps/catalog/versions.lock",
                component_images=[
                    "backend-api=python:3.14-slim",
                    "touchpoints-web=nginx:1.27-alpine",
                ],
                component_image_env_vars=[
                    "backend-api=APP_RUNTIME_BACKEND_IMAGE",  # legacy short name override
                ],
            )
            rc = catalog_scaffold_renderer.cmd_render(args)
            self.assertEqual(rc, 0)
            manifest_text = manifest_output.read_text(encoding="utf-8")
        # Explicit override wins for backend-api; touchpoints-web falls back to derived name
        self.assertIn("imageEnvVar: APP_RUNTIME_BACKEND_IMAGE", manifest_text)
        self.assertIn("imageEnvVar: APP_RUNTIME_TOUCHPOINTS_WEB_IMAGE", manifest_text)


class CatalogManifestValidatorTests(unittest.TestCase):
    """The validator must not require hardcoded baseline names (AC-005)."""

    def test_validator_accepts_non_baseline_descriptor_workloads(self) -> None:
        manifest_text = textwrap.dedent(
            """\
            schemaVersion: v1
            appVersionContract: {}
            runtimePinnedVersions: {}
            frameworkPinnedVersions: {}
            deliveryTopology:
              workloads:
                - workloadId: marketplace-api
                  image: marketplace/api:1.0
            runtimeDeliveryContract:
              gitopsEnabled: true
              mode: k8s-manifests
              manifestsRoot: infra/gitops/platform/base/apps
              gitopsWorkloads:
                - id: marketplace-api
                  deploymentManifest: infra/gitops/platform/base/apps/marketplace-api-deployment.yaml
                  serviceManifest: infra/gitops/platform/base/apps/marketplace-api-service.yaml
                  imageEnvVar: MARKETPLACE_API_IMAGE
                  defaultImage: marketplace/api:1.0
            observabilityRuntimeContract:
              enabled: false
            """
        )
        errors = catalog_scaffold_renderer.validate_manifest_text(
            manifest_text,
            app_runtime_gitops_enabled=True,
            observability_enabled=False,
        )
        self.assertEqual(errors, [], f"validator must accept descriptor-derived workloads; got: {errors}")

    def test_validator_rejects_when_gitops_enabled_but_no_gitopsworkloads_entry(self) -> None:
        manifest_text = textwrap.dedent(
            """\
            schemaVersion: v1
            appVersionContract: {}
            runtimePinnedVersions: {}
            frameworkPinnedVersions: {}
            deliveryTopology:
              workloads: []
            runtimeDeliveryContract:
              gitopsEnabled: true
              mode: k8s-manifests
              manifestsRoot: infra/gitops/platform/base/apps
              gitopsWorkloads: []
            observabilityRuntimeContract:
              enabled: false
            """
        )
        errors = catalog_scaffold_renderer.validate_manifest_text(
            manifest_text,
            app_runtime_gitops_enabled=True,
            observability_enabled=False,
        )
        self.assertTrue(
            any("gitopsWorkloads" in e for e in errors),
            f"validator must reject empty gitopsWorkloads when gitopsEnabled=true; got: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
