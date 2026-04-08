from __future__ import annotations

import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

from tests._shared.helpers import REPO_ROOT, run


class PythonHelperExtractionsTests(unittest.TestCase):
    def test_k8s_wait_helpers_server_url_and_host(self) -> None:
        script = REPO_ROOT / "scripts/lib/infra/k8s_wait_helpers.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            kubeconfig = Path(tmpdir) / "kubeconfig"
            kubeconfig.write_text(
                "apiVersion: v1\nclusters:\n- cluster:\n    server: https://example.cluster.local:6443\n",
                encoding="utf-8",
            )

            url = run([sys.executable, str(script), "server-url", str(kubeconfig)])
            self.assertEqual(url.returncode, 0, msg=url.stdout + url.stderr)
            self.assertEqual(url.stdout.strip(), "https://example.cluster.local:6443")

            host = run([sys.executable, str(script), "server-host", str(kubeconfig)])
            self.assertEqual(host.returncode, 0, msg=host.stdout + host.stderr)
            self.assertEqual(host.stdout.strip(), "example.cluster.local")

    def test_workflows_api_json_helpers(self) -> None:
        script = REPO_ROOT / "scripts/lib/infra/workflows_api_json.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "instances.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "items": [
                            {"displayName": "alpha", "id": "a1", "status": "RUNNING"},
                            {"displayName": "beta", "instanceId": "b2", "state": "running"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            pick = run(
                [
                    sys.executable,
                    str(script),
                    "pick",
                    str(payload_path),
                    "fallback",
                    "items.0.id",
                    "items.1.id",
                ]
            )
            self.assertEqual(pick.returncode, 0, msg=pick.stdout + pick.stderr)
            self.assertEqual(pick.stdout.strip(), "a1")

            count = run([sys.executable, str(script), "count-status", str(payload_path), "running"])
            self.assertEqual(count.returncode, 0, msg=count.stdout + count.stderr)
            self.assertEqual(count.stdout.strip(), "2")

            find = run([sys.executable, str(script), "find-instance-id", str(payload_path), "beta"])
            self.assertEqual(find.returncode, 0, msg=find.stdout + find.stderr)
            self.assertEqual(find.stdout.strip(), "b2")

    def test_status_json_payload_script(self) -> None:
        script = REPO_ROOT / "scripts/lib/infra/status_json_payload.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            smoke_result = Path(tmpdir) / "smoke_result.json"
            smoke_result.write_text(json.dumps({"status": "success"}), encoding="utf-8")
            smoke_diagnostics = Path(tmpdir) / "smoke_diagnostics.json"
            smoke_diagnostics.write_text(json.dumps({"workloadHealth": {"status": "healthy"}}), encoding="utf-8")
            result = run(
                [sys.executable, str(script)],
                {
                    "STATUS_PROFILE": "local-lite",
                    "STATUS_STACK": "local",
                    "STATUS_ENVIRONMENT": "local",
                    "STATUS_TOOLING_MODE": "dry-run",
                    "STATUS_OBSERVABILITY_ENABLED": "false",
                    "STATUS_ENABLED_MODULES": "postgres,neo4j",
                    "STATUS_SMOKE_RESULT_PATH": str(smoke_result),
                    "STATUS_SMOKE_DIAGNOSTICS_PATH": str(smoke_diagnostics),
                    "STATUS_PROVISION_PRESENT": "true",
                    "STATUS_DEPLOY_PRESENT": "true",
                    "STATUS_SMOKE_PRESENT": "true",
                    "STATUS_STACKIT_BOOTSTRAP_APPLY_PRESENT": "false",
                    "STATUS_STACKIT_FOUNDATION_APPLY_PRESENT": "false",
                    "STATUS_STACKIT_RUNTIME_DEPLOY_PRESENT": "false",
                    "STATUS_STACKIT_SMOKE_RUNTIME_PRESENT": "false",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["latestSmoke"]["status"], "success")
            self.assertEqual(payload["enabledModules"], ["postgres", "neo4j"])

    def test_stackit_foundation_outputs_helpers(self) -> None:
        script = REPO_ROOT / "scripts/lib/infra/stackit_foundation_outputs_json.py"
        outputs_payload = json.dumps(
            {
                "cluster_name": {"value": "demo-cluster"},
                "secrets": {"value": {"username": "demo", "enabled": True}},
            }
        )

        value = run(
            [sys.executable, str(script), "value", "cluster_name"],
            {"STACKIT_FOUNDATION_OUTPUTS_JSON": outputs_payload},
        )
        self.assertEqual(value.returncode, 0, msg=value.stdout + value.stderr)
        self.assertEqual(value.stdout.strip(), "demo-cluster")

        map_value = run(
            [sys.executable, str(script), "map-value", "secrets", "enabled"],
            {"STACKIT_FOUNDATION_OUTPUTS_JSON": outputs_payload},
        )
        self.assertEqual(map_value.returncode, 0, msg=map_value.stdout + map_value.stderr)
        self.assertEqual(map_value.stdout.strip(), "true")

    def test_argocd_repo_credentials_helpers(self) -> None:
        script = REPO_ROOT / "scripts/lib/platform/auth/argocd_repo_credentials_json.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            patch_file = Path(tmpdir) / "patch.json"
            render = run(
                [
                    sys.executable,
                    str(script),
                    "render-source-patch",
                    str(patch_file),
                    "git",
                    "https://github.com/acme/demo.git",
                    "x-access-token",
                    "github_pat_abc",
                ]
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            patch_payload = json.loads(patch_file.read_text(encoding="utf-8"))
            self.assertEqual(patch_payload["stringData"]["ARGOCD_REPO_TYPE"], "git")

            secret = {
                "metadata": {"labels": {"argocd.argoproj.io/secret-type": "repository"}},
                "data": {
                    "type": base64.b64encode(b"git").decode("utf-8"),
                    "url": base64.b64encode(b"https://github.com/acme/demo.git").decode("utf-8"),
                    "username": base64.b64encode(b"x-access-token").decode("utf-8"),
                    "password": base64.b64encode(b"github_pat_abc").decode("utf-8"),
                },
            }
            validate = run(
                [sys.executable, str(script), "validate-target-secret", "https://github.com/acme/demo.git"],
                cwd=REPO_ROOT,
            )
            self.assertEqual(validate.returncode, 1)

            import subprocess

            process = subprocess.run(
                [sys.executable, str(script), "validate-target-secret", "https://github.com/acme/demo.git"],
                input=json.dumps(secret),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(process.returncode, 0, msg=process.stdout + process.stderr)

    def test_prereqs_helpers_and_runtime_workload_helpers(self) -> None:
        prereqs_script = REPO_ROOT / "scripts/lib/infra/prereqs_helpers.py"
        workload_script = REPO_ROOT / "scripts/lib/platform/apps/runtime_workload_helpers.py"

        module_ok = run([sys.executable, str(prereqs_script), "python-module-available", "json"])
        self.assertEqual(module_ok.returncode, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "archive.zip"
            extracted = Path(tmpdir) / "extracted"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("sample.txt", "ok")
            unzip = run([sys.executable, str(prereqs_script), "extract-zip", str(archive), str(extracted)])
            self.assertEqual(unzip.returncode, 0, msg=unzip.stdout + unzip.stderr)
            self.assertTrue((extracted / "sample.txt").is_file())

        import subprocess

        count = subprocess.run(
            [sys.executable, str(workload_script)],
            input=json.dumps({"items": [{}, {}, {}]}),
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(count.returncode, 0, msg=count.stdout + count.stderr)
        self.assertEqual(count.stdout.strip(), "3")

    def test_catalog_renderer_and_readiness_reports(self) -> None:
        renderer = REPO_ROOT / "scripts/lib/platform/apps/catalog_scaffold_renderer.py"
        drift_report = REPO_ROOT / "scripts/lib/blueprint/runtime_contract_drift_report.py"
        upgrade_doctor = REPO_ROOT / "scripts/lib/blueprint/upgrade_readiness_doctor.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_out = Path(tmpdir) / "manifest.yaml"
            versions_out = Path(tmpdir) / "versions.lock"
            render = run(
                [
                    sys.executable,
                    str(renderer),
                    "render",
                    "--manifest-template",
                    str(REPO_ROOT / "scripts/templates/platform/apps/catalog/manifest.yaml.tmpl"),
                    "--versions-template",
                    str(REPO_ROOT / "scripts/templates/platform/apps/catalog/versions.lock.tmpl"),
                    "--manifest-output",
                    str(manifest_out),
                    "--versions-output",
                    str(versions_out),
                    "--python-runtime-base-image-version",
                    "3.12.11",
                    "--node-runtime-base-image-version",
                    "22.20.0",
                    "--nginx-runtime-base-image-version",
                    "1.29.2",
                    "--fastapi-version",
                    "0.119.1",
                    "--pydantic-version",
                    "2.11.10",
                    "--vue-version",
                    "3.5.22",
                    "--vue-router-version",
                    "4.5.1",
                    "--pinia-version",
                    "3.0.3",
                    "--app-runtime-gitops-enabled",
                    "true",
                    "--app-runtime-backend-image",
                    "python:3.12.11",
                    "--app-runtime-touchpoints-image",
                    "nginx:1.29.2",
                    "--observability-enabled",
                    "false",
                    "--otel-exporter-otlp-endpoint",
                    "",
                    "--otel-protocol",
                    "",
                    "--otel-traces-enabled",
                    "false",
                    "--otel-metrics-enabled",
                    "false",
                    "--otel-logs-enabled",
                    "false",
                    "--faro-enabled",
                    "false",
                    "--faro-collect-path",
                    "",
                ]
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            self.assertTrue(manifest_out.is_file())
            self.assertTrue(versions_out.is_file())

            validate = run(
                [
                    sys.executable,
                    str(renderer),
                    "validate",
                    "--manifest-path",
                    str(manifest_out),
                    "--app-runtime-gitops-enabled",
                    "true",
                    "--observability-enabled",
                    "false",
                ]
            )
            self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)

        with tempfile.TemporaryDirectory() as tmpdir:
            drift_out = Path(tmpdir) / "drift.json"
            drift = run([sys.executable, str(drift_report), "--repo-root", str(REPO_ROOT), "--output", str(drift_out)])
            self.assertEqual(drift.returncode, 0, msg=drift.stdout + drift.stderr)
            drift_payload = json.loads(drift_out.read_text(encoding="utf-8"))
            self.assertIn("status", drift_payload)
            self.assertIn("runtimeContracts", drift_payload)

            readiness_out = Path(tmpdir) / "readiness.json"
            readiness = run(
                [sys.executable, str(upgrade_doctor), "--repo-root", str(REPO_ROOT), "--output", str(readiness_out)]
            )
            self.assertEqual(readiness.returncode, 0, msg=readiness.stdout + readiness.stderr)
            readiness_payload = json.loads(readiness_out.read_text(encoding="utf-8"))
            self.assertIn("status", readiness_payload)
            self.assertIn("runtimeDependencyEdges", readiness_payload)


if __name__ == "__main__":
    unittest.main()
