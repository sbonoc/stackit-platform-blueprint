#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


DEFAULT_IGNORED_NAMESPACES = {
    "default",
    "kube-node-lease",
    "kube-public",
    "kube-system",
    "local-path-storage",
}

WAITING_FAILURE_REASONS = {
    "CrashLoopBackOff",
    "CreateContainerConfigError",
    "CreateContainerError",
    "ErrImagePull",
    "ImageInspectError",
    "ImagePullBackOff",
    "InvalidImageName",
    "RunContainerError",
    "StartError",
}


def _container_issues(pod: dict, field_name: str) -> list[dict[str, str | int | bool]]:
    issues: list[dict[str, str | int | bool]] = []
    for status in pod.get("status", {}).get(field_name, []) or []:
        container_name = status.get("name", "unknown")
        state = status.get("state", {}) or {}
        waiting = state.get("waiting")
        terminated = state.get("terminated")
        restart_count = int(status.get("restartCount", 0) or 0)
        ready = bool(status.get("ready", False))

        if waiting:
            reason = waiting.get("reason", "Waiting")
            message = waiting.get("message", "")
            if reason in WAITING_FAILURE_REASONS or pod.get("status", {}).get("phase") == "Pending":
                issues.append(
                    {
                        "type": field_name,
                        "container": container_name,
                        "reason": reason,
                        "message": message,
                        "restartCount": restart_count,
                        "ready": ready,
                    }
                )
            continue

        if terminated:
            reason = terminated.get("reason", "Terminated")
            exit_code = int(terminated.get("exitCode", 0) or 0)
            if reason != "Completed" or exit_code != 0:
                issues.append(
                    {
                        "type": field_name,
                        "container": container_name,
                        "reason": reason,
                        "message": terminated.get("message", ""),
                        "restartCount": restart_count,
                        "ready": ready,
                        "exitCode": exit_code,
                    }
                )
            continue

        if pod.get("status", {}).get("phase") == "Running" and not ready:
            issues.append(
                {
                    "type": field_name,
                    "container": container_name,
                    "reason": "NotReady",
                    "message": "container is running but not ready",
                    "restartCount": restart_count,
                    "ready": ready,
                }
            )

    return issues


def evaluate_pod_health(
    payload: dict,
    ignored_namespaces: set[str],
    monitored_namespaces: set[str] | None = None,
) -> dict:
    items = payload.get("items", []) or []
    unhealthy_pods: list[dict] = []
    checked_namespaces: set[str] = set()
    checked_pod_count = 0

    for pod in items:
        metadata = pod.get("metadata", {}) or {}
        namespace = metadata.get("namespace", "default")
        if namespace in ignored_namespaces or namespace.startswith("kube-"):
            continue
        if monitored_namespaces is not None and namespace not in monitored_namespaces:
            continue

        checked_namespaces.add(namespace)
        checked_pod_count += 1

        phase = pod.get("status", {}).get("phase", "Unknown")
        if phase == "Succeeded":
            continue

        issues: list[dict] = []
        if phase in {"Failed", "Unknown"}:
            issues.append(
                {
                    "type": "pod",
                    "container": "",
                    "reason": phase,
                    "message": pod.get("status", {}).get("message", ""),
                    "restartCount": 0,
                    "ready": False,
                }
            )
        elif phase == "Pending":
            issues.append(
                {
                    "type": "pod",
                    "container": "",
                    "reason": "Pending",
                    "message": pod.get("status", {}).get("message", ""),
                    "restartCount": 0,
                    "ready": False,
                }
            )

        issues.extend(_container_issues(pod, "initContainerStatuses"))
        issues.extend(_container_issues(pod, "containerStatuses"))

        if issues:
            unhealthy_pods.append(
                {
                    "namespace": namespace,
                    "name": metadata.get("name", "unknown"),
                    "phase": phase,
                    "issues": issues,
                }
            )

    status = "healthy" if not unhealthy_pods else "unhealthy"
    return {
        "status": status,
        "monitoredNamespaces": sorted(monitored_namespaces) if monitored_namespaces is not None else [],
        "checkedNamespaces": sorted(checked_namespaces),
        "checkedPodCount": checked_pod_count,
        "unhealthyPodCount": len(unhealthy_pods),
        "unhealthyPods": unhealthy_pods,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Kubernetes workload health from a pod-list JSON payload.")
    parser.add_argument("--input", required=True, help="Path to a kubectl get pods -A -o json payload.")
    parser.add_argument("--output", required=True, help="Path to write the workload health report JSON.")
    parser.add_argument(
        "--ignore-namespace",
        action="append",
        default=[],
        help="Additional namespace to ignore. May be repeated.",
    )
    parser.add_argument(
        "--namespace",
        action="append",
        default=[],
        help="Restrict checks to blueprint-managed namespaces. May be repeated.",
    )
    args = parser.parse_args()

    ignored_namespaces = set(DEFAULT_IGNORED_NAMESPACES)
    ignored_namespaces.update(args.ignore_namespace)
    monitored_namespaces = set(args.namespace) if args.namespace else None

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = evaluate_pod_health(payload, ignored_namespaces, monitored_namespaces)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        f"[workload-health] status={report['status']} checked_pods={report['checkedPodCount']} "
        f"unhealthy_pods={report['unhealthyPodCount']}"
    )

    if report["status"] != "healthy":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
