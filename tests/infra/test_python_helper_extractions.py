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

            without_paths = run(
                [sys.executable, str(script)],
                {
                    "STATUS_PROFILE": "local-lite",
                    "STATUS_STACK": "local",
                    "STATUS_ENVIRONMENT": "local",
                    "STATUS_TOOLING_MODE": "dry-run",
                    "STATUS_OBSERVABILITY_ENABLED": "false",
                    "STATUS_ENABLED_MODULES": "",
                    "STATUS_SMOKE_RESULT_PATH": "",
                    "STATUS_SMOKE_DIAGNOSTICS_PATH": "",
                    "STATUS_PROVISION_PRESENT": "false",
                    "STATUS_DEPLOY_PRESENT": "false",
                    "STATUS_SMOKE_PRESENT": "false",
                    "STATUS_STACKIT_BOOTSTRAP_APPLY_PRESENT": "false",
                    "STATUS_STACKIT_FOUNDATION_APPLY_PRESENT": "false",
                    "STATUS_STACKIT_RUNTIME_DEPLOY_PRESENT": "false",
                    "STATUS_STACKIT_SMOKE_RUNTIME_PRESENT": "false",
                },
            )
            self.assertEqual(without_paths.returncode, 0, msg=without_paths.stdout + without_paths.stderr)
            without_paths_payload = json.loads(without_paths.stdout)
            self.assertEqual(without_paths_payload["latestSmoke"]["resultPath"], "")
            self.assertEqual(without_paths_payload["latestSmoke"]["diagnosticsPath"], "")

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
        script = REPO_ROOT / "scripts/lib/infra/argocd_repo_credentials_json.py"
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
                ],
                {"ARGOCD_REPO_TOKEN": "github_pat_abc"},
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            patch_payload = json.loads(patch_file.read_text(encoding="utf-8"))
            self.assertEqual(patch_payload["stringData"]["ARGOCD_REPO_TYPE"], "git")
            self.assertEqual(patch_payload["stringData"]["ARGOCD_REPO_TOKEN"], "github_pat_abc")

            missing_token = run(
                [
                    sys.executable,
                    str(script),
                    "render-source-patch",
                    str(patch_file),
                    "git",
                    "https://github.com/acme/demo.git",
                    "x-access-token",
                ],
                {"ARGOCD_REPO_TOKEN": ""},
            )
            self.assertEqual(missing_token.returncode, 1)
            self.assertIn("required repo token env var is empty or unset", missing_token.stderr)

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

            invalid_json = subprocess.run(
                [sys.executable, str(script), "validate-target-secret", "https://github.com/acme/demo.git"],
                input="{",
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(invalid_json.returncode, 1)
            self.assertIn("failed to parse target secret JSON from stdin", invalid_json.stderr)

            invalid_base64_secret = dict(secret)
            invalid_base64_secret["data"] = dict(secret["data"])
            invalid_base64_secret["data"]["url"] = "not-base64"
            invalid_base64 = subprocess.run(
                [sys.executable, str(script), "validate-target-secret", "https://github.com/acme/demo.git"],
                input=json.dumps(invalid_base64_secret),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(invalid_base64.returncode, 1)
            self.assertIn("contains invalid base64 content", invalid_base64.stderr)

    def test_runtime_secret_keys_helpers(self) -> None:
        script = REPO_ROOT / "scripts/lib/platform/auth/runtime_secret_keys_json.py"

        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            check_ready_path = Path(tmpdir) / "check-ready.json"
            check_missing_path = Path(tmpdir) / "check-missing.json"
            report_path = Path(tmpdir) / "report.json"

            valid_secret = {"apiVersion": "v1", "kind": "Secret", "data": {"client-id": "YQ==", "client-secret": "Yg=="}}
            valid = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id,client-secret"],
                input=json.dumps(valid_secret),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(valid.returncode, 0, msg=valid.stdout + valid.stderr)
            self.assertEqual(valid.stdout.strip(), "ok")

            missing = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id,client-secret"],
                input=json.dumps({"data": {"client-id": "YQ=="}}),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(missing.returncode, 1, msg=missing.stdout + missing.stderr)
            self.assertEqual(missing.stdout.strip(), "client-secret")

            noisy_input = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id,client-secret"],
                input=(
                    "INFO bootstrap complete\n"
                    + json.dumps({"data": {"client-id": "YQ==", "client-secret": "Yg=="}})
                    + "\nINFO done\n"
                ),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(noisy_input.returncode, 0, msg=noisy_input.stdout + noisy_input.stderr)
            self.assertEqual(noisy_input.stdout.strip(), "ok")

            missing_data_map = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id"],
                input=json.dumps({"kind": "Secret"}),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(missing_data_map.returncode, 2, msg=missing_data_map.stdout + missing_data_map.stderr)
            self.assertEqual(missing_data_map.stdout.strip(), "__verify_error__:missing-secret-data-map")

            invalid_json = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id"],
                input="{",
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(invalid_json.returncode, 2, msg=invalid_json.stdout + invalid_json.stderr)
            self.assertEqual(invalid_json.stdout.strip(), "__verify_error__:invalid-secret-json")

            empty_input = subprocess.run(
                [sys.executable, str(script), "verify-required-keys", "client-id"],
                input="",
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(empty_input.returncode, 2, msg=empty_input.stdout + empty_input.stderr)
            self.assertEqual(empty_input.stdout.strip(), "__verify_error__:empty-secret-json")

            check_ready = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "check-target-secret",
                    "--namespace",
                    "security",
                    "--secret-name",
                    "iap-runtime-credentials",
                    "--required-keys",
                    "client-id,client-secret",
                    "--summary",
                    "--output-json",
                    str(check_ready_path),
                ],
                input=json.dumps(valid_secret),
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(check_ready.returncode, 0, msg=check_ready.stdout + check_ready.stderr)
            self.assertEqual(check_ready.stdout.strip(), "ready\tnone\tok")
            check_ready_payload = json.loads(check_ready_path.read_text(encoding="utf-8"))
            self.assertEqual(check_ready_payload["kind"], "runtime-target-secret-contract-check")
            self.assertEqual(check_ready_payload["schemaVersion"], "v1")
            self.assertEqual(check_ready_payload["status"], "ready")

            check_missing = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "check-target-secret",
                    "--namespace",
                    "security",
                    "--secret-name",
                    "iap-runtime-credentials",
                    "--required-keys",
                    "client-id,client-secret",
                    "--secret-present",
                    "false",
                    "--summary",
                    "--output-json",
                    str(check_missing_path),
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(check_missing.returncode, 1, msg=check_missing.stdout + check_missing.stderr)
            self.assertEqual(check_missing.stdout.strip(), "missing-secret\tclient-id,client-secret\tmissing-target-secret")
            check_missing_payload = json.loads(check_missing_path.read_text(encoding="utf-8"))
            self.assertEqual(check_missing_payload["status"], "missing-secret")
            self.assertEqual(check_missing_payload["missingKeys"], ["client-id", "client-secret"])

            report = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "render-check-report",
                    "--output",
                    str(report_path),
                    str(check_ready_path),
                    str(check_missing_path),
                ],
                text=True,
                capture_output=True,
                cwd=REPO_ROOT,
            )
            self.assertEqual(report.returncode, 0, msg=report.stdout + report.stderr)
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report_payload["kind"], "runtime-target-secret-contract-check-report")
            self.assertEqual(report_payload["schemaVersion"], "v1")
            self.assertEqual(report_payload["counts"]["total"], 2)
            self.assertEqual(report_payload["counts"]["ready"], 1)
            self.assertEqual(report_payload["counts"]["missingSecret"], 1)
            self.assertEqual(len(report_payload["checks"]), 2)

    def test_runtime_identity_doctor_helpers(self) -> None:
        script = REPO_ROOT / "scripts/lib/platform/auth/runtime_identity_doctor_json.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            runtime_identity_state = tmp / "runtime_identity_reconcile.env"
            runtime_credentials_state = tmp / "runtime_credentials_eso_reconcile.env"
            argocd_state = tmp / "argocd_repo_credentials_reconcile.env"
            target_secret_report = tmp / "runtime_credentials_eso_target_secret_checks.json"
            report_path = tmp / "runtime_identity_doctor_report.json"

            runtime_identity_state.write_text(
                "\n".join(
                    [
                        "status=success",
                        "keycloak_realm_check_count=1",
                        "keycloak_expected_contract_count=1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            runtime_credentials_state.write_text(
                "\n".join(
                    [
                        "status=success-with-warnings",
                        "tooling_mode=execute",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            argocd_state.write_text("status=success\n", encoding="utf-8")
            target_secret_report.write_text(
                json.dumps(
                    {
                        "counts": {
                            "total": 2,
                            "ready": 1,
                            "missingSecret": 1,
                            "missingKeys": 0,
                            "verifyError": 0,
                        }
                    }
                ),
                encoding="utf-8",
            )

            render = run(
                [
                    sys.executable,
                    str(script),
                    "render-report",
                    "--output",
                    str(report_path),
                    "--profile",
                    "local-full",
                    "--stack",
                    "local",
                    "--tooling-mode",
                    "execute",
                    "--refresh-status",
                    "success",
                    "--runtime-identity-state",
                    str(runtime_identity_state),
                    "--runtime-credentials-state",
                    str(runtime_credentials_state),
                    "--argocd-state",
                    str(argocd_state),
                    "--target-secret-report",
                    str(target_secret_report),
                    "--contract-eso-expected",
                    "2",
                    "--contract-eso-enabled",
                    "2",
                    "--contract-keycloak-expected",
                    "1",
                    "--contract-keycloak-enabled",
                    "1",
                    "--contract-eso-enabled-contracts",
                    "runtime-credentials,argocd-gitops-repo",
                    "--contract-keycloak-enabled-realms",
                    "workflows",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            summary_fields = render.stdout.strip().split("\t")
            self.assertEqual(summary_fields[0], "success-with-warnings")
            self.assertEqual(summary_fields[4], "2")
            self.assertEqual(summary_fields[6], "1")

            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report_payload["kind"], "runtime-identity-doctor-report")
            self.assertEqual(report_payload["schemaVersion"], "v1")
            self.assertEqual(report_payload["summary"]["status"], "success-with-warnings")
            self.assertEqual(report_payload["contract"]["keycloak"]["enabledRealmCount"], 1)
            self.assertEqual(report_payload["artifacts"]["targetSecretCheckReport"]["counts"]["missingSecret"], 1)
            self.assertGreaterEqual(report_payload["summary"]["warningCount"], 1)

            runtime_identity_state.write_text(
                "\n".join(
                    [
                        "status=success",
                        "keycloak_realm_check_count=0",
                        "keycloak_expected_contract_count=0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            runtime_credentials_state.write_text(
                "\n".join(
                    [
                        "status=success",
                        "tooling_mode=dry-run",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            target_secret_report.write_text(
                json.dumps(
                    {
                        "counts": {
                            "total": 0,
                            "ready": 0,
                            "missingSecret": 0,
                            "missingKeys": 0,
                            "verifyError": 0,
                        }
                    }
                ),
                encoding="utf-8",
            )

            render_empty = run(
                [
                    sys.executable,
                    str(script),
                    "render-report",
                    "--output",
                    str(report_path),
                    "--profile",
                    "local-full",
                    "--stack",
                    "local",
                    "--tooling-mode",
                    "dry-run",
                    "--refresh-status",
                    "skipped",
                    "--runtime-identity-state",
                    str(runtime_identity_state),
                    "--runtime-credentials-state",
                    str(runtime_credentials_state),
                    "--argocd-state",
                    str(argocd_state),
                    "--target-secret-report",
                    str(target_secret_report),
                    "--contract-eso-expected",
                    "0",
                    "--contract-eso-enabled",
                    "0",
                    "--contract-keycloak-expected",
                    "0",
                    "--contract-keycloak-enabled",
                    "0",
                    "--contract-eso-enabled-contracts",
                    "none",
                    "--contract-keycloak-enabled-realms",
                    "N/A",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(render_empty.returncode, 0, msg=render_empty.stdout + render_empty.stderr)
            report_empty_payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report_empty_payload["summary"]["status"], "success")
            self.assertEqual(report_empty_payload["contract"]["eso"]["enabledContracts"], [])
            self.assertEqual(report_empty_payload["contract"]["keycloak"]["enabledRealms"], [])

    def test_prereqs_helpers_and_runtime_workload_helpers(self) -> None:
        prereqs_script = REPO_ROOT / "scripts/lib/infra/prereqs_helpers.py"
        workload_script = REPO_ROOT / "scripts/lib/infra/runtime_workload_helpers.py"

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

            malicious_archive = Path(tmpdir) / "malicious.zip"
            with zipfile.ZipFile(malicious_archive, "w") as handle:
                handle.writestr("../escape.txt", "escape")
            blocked = run(
                [sys.executable, str(prereqs_script), "extract-zip", str(malicious_archive), str(extracted)]
            )
            self.assertEqual(blocked.returncode, 1)
            self.assertIn("outside destination", blocked.stderr)

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
            manifest_text = manifest_out.read_text(encoding="utf-8")
            self.assertIn('endpoint: ""', manifest_text)
            self.assertIn('protocol: ""', manifest_text)
            self.assertIn('collectPath: ""', manifest_text)

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

    def test_smoke_artifacts_script_uses_empty_paths_when_env_is_empty(self) -> None:
        script = REPO_ROOT / "scripts/lib/infra/smoke_artifacts.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = Path(tmpdir) / "smoke_result.json"
            diagnostics_path = Path(tmpdir) / "smoke_diagnostics.json"
            run_result = run(
                [sys.executable, str(script)],
                {
                    "SMOKE_ENABLED_MODULES": "postgres",
                    "SMOKE_WORKLOAD_HEALTH_PATH": "",
                    "SMOKE_POD_SNAPSHOT_PATH": "",
                    "SMOKE_APP_RUNTIME_GITOPS_ENABLED": "true",
                    "SMOKE_APP_RUNTIME_MIN_WORKLOADS": "1",
                    "SMOKE_RESULT_STATUS": "success",
                    "SMOKE_PROFILE": "local-lite",
                    "SMOKE_STACK": "local",
                    "SMOKE_ENVIRONMENT": "local",
                    "SMOKE_TOOLING_MODE": "dry-run",
                    "SMOKE_OBSERVABILITY_ENABLED": "false",
                    "SMOKE_STARTED_AT": "1",
                    "SMOKE_FINISHED_AT": "2",
                    "SMOKE_KUBECTL_CONTEXT": "",
                    "SMOKE_PROVISION_PRESENT": "false",
                    "SMOKE_DEPLOY_PRESENT": "false",
                    "SMOKE_CORE_RUNTIME_PRESENT": "false",
                    "SMOKE_APPS_PRESENT": "false",
                    "SMOKE_WORKLOAD_NAMESPACES": "apps",
                    "SMOKE_RESULT_PATH": str(result_path),
                    "SMOKE_DIAGNOSTICS_PATH": str(diagnostics_path),
                },
            )
            self.assertEqual(run_result.returncode, 0, msg=run_result.stdout + run_result.stderr)
            diagnostics_payload = json.loads(diagnostics_path.read_text(encoding="utf-8"))
            workload_health = diagnostics_payload["workloadHealth"]
            self.assertEqual(workload_health["reportPath"], "")
            self.assertEqual(workload_health["podSnapshotPath"], "")


if __name__ == "__main__":
    unittest.main()
