from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


class WorkloadHealthCheckTests(unittest.TestCase):
    def _run_health_check(
        self,
        payload: dict,
        *namespaces: str,
        required_namespace_min_pods: dict[str, int] | None = None,
    ) -> tuple[int, dict, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "pods.json"
            output_path = Path(tmpdir) / "workload-health.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            cmd = [
                "python3",
                str(REPO_ROOT / "scripts/bin/infra/workload_health_check.py"),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]
            for namespace in namespaces:
                cmd.extend(["--namespace", namespace])
            for namespace, minimum_pods in sorted((required_namespace_min_pods or {}).items()):
                cmd.extend(["--required-namespace-min-pods", f"{namespace}={minimum_pods}"])

            result = run(cmd)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            return result.returncode, report, result.stdout + result.stderr

    def test_healthy_workloads_pass(self) -> None:
        payload = {
            "items": [
                {
                    "metadata": {"namespace": "apps", "name": "catalog-6d8f5"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "catalog",
                                "ready": True,
                                "restartCount": 0,
                                "state": {"running": {"startedAt": "2026-03-27T10:00:00Z"}},
                            }
                        ],
                    },
                }
            ]
        }

        code, report, output = self._run_health_check(payload, "apps")
        self.assertEqual(code, 0, msg=output)
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["checkedPodCount"], 1)
        self.assertEqual(report["unhealthyPodCount"], 0)
        self.assertEqual(report["monitoredNamespaces"], ["apps"])

    def test_unhealthy_workloads_fail(self) -> None:
        payload = {
            "items": [
                {
                    "metadata": {"namespace": "messaging", "name": "rabbitmq-0"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "rabbitmq",
                                "ready": False,
                                "restartCount": 7,
                                "state": {
                                    "waiting": {
                                        "reason": "ImagePullBackOff",
                                        "message": "Back-off pulling image",
                                    }
                                },
                            }
                        ],
                    },
                }
            ]
        }

        code, report, output = self._run_health_check(payload, "messaging")
        self.assertNotEqual(code, 0, msg=output)
        self.assertEqual(report["status"], "unhealthy")
        self.assertEqual(report["unhealthyPodCount"], 1)
        self.assertEqual(report["unhealthyPods"][0]["issues"][0]["reason"], "ImagePullBackOff")

    def test_monitored_namespaces_ignore_unrelated_workloads(self) -> None:
        payload = {
            "items": [
                {
                    "metadata": {"namespace": "apps", "name": "catalog-6d8f5"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "catalog",
                                "ready": True,
                                "restartCount": 0,
                                "state": {"running": {"startedAt": "2026-03-27T10:00:00Z"}},
                            }
                        ],
                    },
                },
                {
                    "metadata": {"namespace": "someone-else", "name": "broken-pod"},
                    "status": {
                        "phase": "Pending",
                        "containerStatuses": [
                            {
                                "name": "broken",
                                "ready": False,
                                "restartCount": 0,
                                "state": {"waiting": {"reason": "CrashLoopBackOff", "message": "boom"}},
                            }
                        ],
                    },
                },
            ]
        }

        code, report, output = self._run_health_check(payload, "apps")
        self.assertEqual(code, 0, msg=output)
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["checkedNamespaces"], ["apps"])

    def test_required_namespace_min_pods_fails_when_runtime_namespace_is_empty(self) -> None:
        payload = {
            "items": [
                {
                    "metadata": {"namespace": "security", "name": "keycloak-0"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "keycloak",
                                "ready": True,
                                "restartCount": 0,
                                "state": {"running": {"startedAt": "2026-04-08T18:30:00Z"}},
                            }
                        ],
                    },
                }
            ]
        }

        code, report, output = self._run_health_check(
            payload,
            "apps",
            required_namespace_min_pods={"apps": 1},
        )
        self.assertNotEqual(code, 0, msg=output)
        self.assertEqual(report["status"], "unhealthy")
        self.assertEqual(report["statusReason"], "empty-runtime-workloads")
        self.assertEqual(report["emptyRuntimeNamespaceCount"], 1)
        self.assertEqual(report["emptyRuntimeNamespaces"], ["apps"])
        self.assertEqual(report["requiredNamespaceMinimumPods"][0]["status"], "missing")

    def test_required_namespace_min_pods_passes_when_threshold_is_met(self) -> None:
        payload = {
            "items": [
                {
                    "metadata": {"namespace": "apps", "name": "backend-api-5b95b7fbd8-w2jv6"},
                    "status": {
                        "phase": "Running",
                        "containerStatuses": [
                            {
                                "name": "backend-api",
                                "ready": True,
                                "restartCount": 0,
                                "state": {"running": {"startedAt": "2026-04-08T18:30:00Z"}},
                            }
                        ],
                    },
                }
            ]
        }

        code, report, output = self._run_health_check(
            payload,
            "apps",
            required_namespace_min_pods={"apps": 1},
        )
        self.assertEqual(code, 0, msg=output)
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["statusReason"], "healthy")
        self.assertEqual(report["emptyRuntimeNamespaceCount"], 0)
        self.assertEqual(report["requiredNamespaceMinimumPods"][0]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
