from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


def resolve_optional_module_execution(module: str, action: str, *, profile: str) -> str:
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stack_paths.sh"
source "{REPO_ROOT}/scripts/lib/infra/module_execution.sh"
resolve_optional_module_execution "{module}" "{action}"
printf 'class=%s\\ndriver=%s\\npath=%s\\nnote=%s\\n' \
  "$OPTIONAL_MODULE_EXECUTION_CLASS" \
  "$OPTIONAL_MODULE_EXECUTION_DRIVER" \
  "$OPTIONAL_MODULE_EXECUTION_PATH" \
  "$OPTIONAL_MODULE_EXECUTION_NOTE"
"""
    result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": profile})
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def resolve_local_kube_context_contract(
    contexts: list[str],
    current_context: str,
    *,
    ci: str = "false",
    local_kube_context: str | None = None,
) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        kubectl = Path(tmpdir) / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  cat <<'EOF'",
                    *contexts,
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    f"  printf '%s\\n' '{current_context}'",
                    "  exit 0",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        script = f"""
export PATH="{tmpdir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
printf 'context=%s\\n' "$(resolve_local_kube_context)"
printf 'source=%s\\n' "$(resolve_local_kube_context_source)"
"""
        env = {"BLUEPRINT_PROFILE": "local-full", "CI": ci}
        if local_kube_context is not None:
            env["LOCAL_KUBE_CONTEXT"] = local_kube_context
        result = run(["bash", "-lc", script], env)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout + result.stderr


def run_helm_upgrade_with_context_contract() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        values_file = tmp_path / "values.yaml"
        values_file.write_text("auth:\n  enablePostgresUser: true\n", encoding="utf-8")

        helm_log = tmp_path / "helm.log"
        kubectl = tmp_path / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        helm = tmp_path / "helm"
        helm.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'printf "%s\\n" "$*" >> "{helm_log}"',
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        helm.chmod(0o755)

        script = f"""
export PATH="{tmp_path}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="local-full"
export LOCAL_KUBE_CONTEXT="docker-desktop"
export DRY_RUN="false"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
run_helm_upgrade_install "contract-postgres" "data" "bitnami/postgresql" "16.7.13" "{values_file}"
cat "{helm_log}"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            helm_calls = helm_log.read_text(encoding="utf-8") if helm_log.exists() else "<missing helm log>"
            raise AssertionError(result.stdout + result.stderr + "\n[helm-calls]\n" + helm_calls)
        return result.stdout + result.stderr


def helm_repo_update_retry_contract(*, failures_before_success: int, max_attempts: int) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        attempts_file = tmp_path / "attempts.txt"
        attempts_file.write_text("0\n", encoding="utf-8")
        helm_log = tmp_path / "helm.log"
        helm = tmp_path / "helm"
        helm.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'ATTEMPTS_FILE="{attempts_file}"',
                    f'HELM_LOG="{helm_log}"',
                    f"FAILURES_BEFORE_SUCCESS={failures_before_success}",
                    'printf "%s\\n" "$*" >> "$HELM_LOG"',
                    'if [ "$1" = "repo" ] && [ "$2" = "add" ]; then',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "repo" ] && [ "$2" = "update" ]; then',
                    '  attempts="$(cat "$ATTEMPTS_FILE" 2>/dev/null || printf \'0\')"',
                    "  attempts=$((attempts + 1))",
                    '  printf "%s\\n" "$attempts" > "$ATTEMPTS_FILE"',
                    '  if [ "$attempts" -le "$FAILURES_BEFORE_SUCCESS" ]; then',
                    "    exit 17",
                    "  fi",
                    "  exit 0",
                    "fi",
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        helm.chmod(0o755)

        script = f"""
export PATH="{tmp_path}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export DRY_RUN="false"
export HELM_REPO_UPDATE_RETRY_MAX_ATTEMPTS="{max_attempts}"
export HELM_REPO_UPDATE_RETRY_BASE_DELAY_SECONDS="1"
export HELM_REPO_UPDATE_RETRY_MAX_DELAY_SECONDS="1"
export HELM_REPO_UPDATE_RETRY_BACKOFF_MULTIPLIER="2"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
prepare_helm_repo_for_chart "bitnami/postgresql"
printf 'attempts=%s\\n' "$(cat "{attempts_file}")"
        """
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            helm_calls = helm_log.read_text(encoding="utf-8") if helm_log.exists() else "<missing helm log>"
            raise AssertionError(result.stdout + result.stderr + "\n[helm-calls]\n" + helm_calls)
        return result.stdout + result.stderr


def port_forward_lifecycle_contract() -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ready_file = tmp_path / "port-ready"
        kubectl_log = tmp_path / "kubectl.log"
        pf_log = tmp_path / "port-forward.log"

        kubectl = tmp_path / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'READY_FILE="{ready_file}"',
                    f'KUBECTL_LOG="{kubectl_log}"',
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "--kubeconfig" ]; then',
                    '  printf "%s\\n" "$*" >> "$KUBECTL_LOG"',
                    '  printf "ready\\n" > "$READY_FILE"',
                    '  trap "rm -f \"$READY_FILE\"; exit 0" TERM INT EXIT',
                    "  while true; do sleep 1; done",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        nc = tmp_path / "nc"
        nc.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'READY_FILE="{ready_file}"',
                    'if [ "$1" = "-z" ] && [ "$2" = "127.0.0.1" ] && [ "$3" = "18080" ]; then',
                    '  if [ -f "$READY_FILE" ]; then',
                    "    exit 0",
                    "  fi",
                    "  exit 1",
                    "fi",
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        nc.chmod(0o755)

        script = f"""
export PATH="{tmp_path}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="local-full"
export LOCAL_KUBE_CONTEXT="docker-desktop"
export DRY_RUN="false"
export PORT_FORWARD_WAIT_TIMEOUT_SECONDS="5"
export PORT_FORWARD_WAIT_POLL_SECONDS="1"
export PORT_FORWARD_STOP_TIMEOUT_SECONDS="2"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
source "{REPO_ROOT}/scripts/lib/infra/port_forward.sh"
start_port_forward "contract-pf" "apps" "svc/demo" "18080" "8080" "{pf_log}"
wait_for_local_port "contract-pf" "18080" "5"
stop_port_forward "contract-pf"
cleanup_port_forwards
printf 'last_pid=%s\\n' "$PORT_FORWARD_LAST_PID"
printf 'remaining=%s\\n' "$(port_forward_registry_names | wc -l | tr -d '[:space:]')"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        calls = kubectl_log.read_text(encoding="utf-8") if kubectl_log.exists() else ""
        return result.stdout + result.stderr, calls


def port_forward_stop_timeout_contract() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ready_file = tmp_path / "port-ready"
        kubectl_log = tmp_path / "kubectl.log"
        pf_log = tmp_path / "port-forward.log"

        kubectl = tmp_path / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'READY_FILE="{ready_file}"',
                    f'KUBECTL_LOG="{kubectl_log}"',
                    'printf "%s\\n" "$*" >> "$KUBECTL_LOG"',
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "--kubeconfig" ]; then',
                    '  printf "ready\\n" > "$READY_FILE"',
                    '  trap "" TERM',
                    "  while true; do sleep 1; done",
                    "fi",
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        nc = tmp_path / "nc"
        nc.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'READY_FILE="{ready_file}"',
                    'if [ "$1" = "-z" ] && [ "$2" = "127.0.0.1" ] && [ "$3" = "18081" ]; then',
                    '  if [ -f "$READY_FILE" ]; then',
                    "    exit 0",
                    "  fi",
                    "  exit 1",
                    "fi",
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        nc.chmod(0o755)

        script = f"""
export PATH="{tmp_path}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="local-full"
export LOCAL_KUBE_CONTEXT="docker-desktop"
export DRY_RUN="false"
export PORT_FORWARD_WAIT_TIMEOUT_SECONDS="5"
export PORT_FORWARD_WAIT_POLL_SECONDS="1"
export PORT_FORWARD_STOP_TIMEOUT_SECONDS="1"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
source "{REPO_ROOT}/scripts/lib/infra/port_forward.sh"
start_port_forward "timeout-pf" "apps" "svc/demo" "18081" "8081" "{pf_log}"
wait_for_local_port "timeout-pf" "18081" "5"
set +e
stop_port_forward "timeout-pf" "false"
status="$?"
set -e
printf 'stop_status=%s\\n' "$status"
printf 'registry_after_stop=%s\\n' "$(port_forward_registry_names | wc -l | tr -d '[:space:]')"
cleanup_port_forwards "true"
printf 'registry_after_cleanup=%s\\n' "$(port_forward_registry_names | wc -l | tr -d '[:space:]')"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            kubectl_calls = kubectl_log.read_text(encoding="utf-8") if kubectl_log.exists() else "<missing kubectl log>"
            raise AssertionError(result.stdout + result.stderr + "\n[kubectl-calls]\n" + kubectl_calls)
        return result.stdout + result.stderr


def cluster_crd_exists_contract(crds: list[str], query: str) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        kubectl = Path(tmpdir) / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'while [ "$1" = "--kubeconfig" ] || [ "$1" = "--context" ]; do',
                    "  shift 2",
                    "done",
                    'if [ \"$1\" = \"get\" ] && [ \"$2\" = \"crd\" ]; then',
                    "  case \"$3\" in",
                    *[f"    {crd}) exit 0 ;;" for crd in crds],
                    "    *) exit 1 ;;",
                    "  esac",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        script = f"""
export PATH="{tmpdir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="local-full"
export DRY_RUN="false"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
if cluster_crd_exists "{query}"; then
  printf 'present\\n'
else
  printf 'missing\\n'
fi
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout.strip().splitlines()[-1] == "present"


def public_endpoints_delete_contract(*, require_finalizer_patch: bool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "gatewayclass_patch_state"
        kubectl = Path(tmpdir) / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'STATE_FILE="{state_file}"',
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    "  printf '%s\\n' docker-desktop",
                    "  exit 0",
                    "fi",
                    "while [ \"$#\" -gt 0 ]; do",
                    "  case \"$1\" in",
                    "    --kubeconfig|--context)",
                    "      shift 2",
                    "      continue",
                    "      ;;",
                    "    --kubeconfig=*|--context=*)",
                    "      shift",
                    "      continue",
                    "      ;;",
                    "  esac",
                    "  break",
                    "done",
                    'if [ "$1" = "delete" ] && [ "$2" = "gateway" ]; then',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "delete" ] && [ "$2" = "gatewayclass" ]; then',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "get" ] && [ "$2" = "gatewayclass" ] && [ "$3" = "public-endpoints" ] && [ "$4" = "-o" ]; then',
                    f"  if [ {1 if require_finalizer_patch else 0} -eq 1 ] && [ ! -f \"$STATE_FILE\" ]; then",
                    "    printf '%s\\n' 'gateway-exists-finalizer.gateway.networking.k8s.io'",
                    "  fi",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "patch" ] && [ "$2" = "gatewayclass" ] && [ "$3" = "public-endpoints" ]; then',
                    '  printf "%s\\n" patched > "$STATE_FILE"',
                    "  exit 0",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        script = f"""
export PATH="{tmpdir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="local-full"
export DRY_RUN="false"
export LOCAL_KUBE_CONTEXT="docker-desktop"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
source "{REPO_ROOT}/scripts/lib/infra/public_endpoints.sh"
public_endpoints_init_env
wait_call_count=0
public_endpoints_wait_for_resource_absence() {{
  wait_call_count=$((wait_call_count + 1))
  if [[ "$1" == "gatewayclass" && "{str(require_finalizer_patch).lower()}" == "true" && "$wait_call_count" -eq 2 ]]; then
    return 1
  fi
  return 0
}}
public_endpoints_delete_helm_gateway_baseline
printf 'wait_call_count=%s\\n' "$wait_call_count"
if [[ -f "{state_file}" ]]; then
  printf 'patch_state=%s\\n' "$(cat "{state_file}")"
else
  printf 'patch_state=none\\n'
fi
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout + result.stderr


def keycloak_exec_active_access_contract(*, profile: str, context_name: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        kubectl_log = tmp_path / "kubectl.log"
        stackit_kubeconfig = tmp_path / "stackit-kubeconfig.yaml"
        stackit_kubeconfig.write_text(
            "\n".join(
                [
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://stackit.example:6443",
                    f"  name: {context_name}",
                    "contexts:",
                    "- context:",
                    f"    cluster: {context_name}",
                    f"    user: {context_name}",
                    f"  name: {context_name}",
                    f"current-context: {context_name}",
                    "users:",
                    f"- name: {context_name}",
                    "  user:",
                    "    token: placeholder",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        kubectl = tmp_path / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'KUBECTL_LOG="{kubectl_log}"',
                    f'CONTEXT_NAME="{context_name}"',
                    'printf "%s\\n" "$*" >> "$KUBECTL_LOG"',
                    "set -- \"$@\"",
                    "while [ \"$#\" -gt 0 ]; do",
                    "  case \"$1\" in",
                    "    --kubeconfig|--context)",
                    "      shift 2",
                    "      continue",
                    "      ;;",
                    "    --kubeconfig=*|--context=*)",
                    "      shift",
                    "      continue",
                    "      ;;",
                    "  esac",
                    "  break",
                    "done",
                    'if [ "$1" = "config" ] && [ "$2" = "get-contexts" ] && [ "$3" = "-o" ] && [ "$4" = "name" ]; then',
                    '  printf "%s\\n" "$CONTEXT_NAME"',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "current-context" ]; then',
                    '  printf "%s\\n" "$CONTEXT_NAME"',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "config" ] && [ "$2" = "view" ] && [ "$3" = "--raw" ] && [ "$4" = "--minify" ] && [ "$5" = "--flatten" ]; then',
                    "  cat <<EOF",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "-n" ] && [ "$2" = "security" ] && [ "$3" = "get" ] && [ "$4" = "pod" ]; then',
                    "  printf '%s\\n' keycloak-0",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "-n" ] && [ "$2" = "security" ] && [ "$3" = "get" ] && [ "$4" = "secret" ]; then',
                    "  printf '%s\\n' 'W0400 key warning emitted on stderr' >&2",
                    "  printf '%s' 'cnVudGltZS1hZG1pbi1wYXNz'",
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "-n" ] && [ "$2" = "security" ] && [ "$3" = "exec" ] && [ "$4" = "keycloak-0" ]; then',
                    "  exit 0",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        profile_env = ""
        if profile.startswith("local-"):
            profile_env = f'export LOCAL_KUBE_CONTEXT="{context_name}"\n'
        else:
            profile_env = f'export STACKIT_FOUNDATION_KUBECONFIG_OUTPUT="{stackit_kubeconfig}"\n'

        script = f"""
export PATH="{tmp_path}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_PROFILE="{profile}"
export DRY_RUN="false"
{profile_env}source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/keycloak_identity_contract.sh"
keycloak_reconcile_oidc_identity_contract \
  "security" \
  "blueprint-keycloak" \
  "keycloak-runtime-credentials" \
  "iap" \
  "iap-client" \
  "iap-client-secret" \
  "https://iap.local/oauth2/callback" \
  "https://iap.local" \
  "Admin,Viewer" \
  "iap-admin" \
  "iap-admin-password" \
  "Admin" \
  "IAP Client"
cat "{kubectl_log}"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            kubectl_calls = kubectl_log.read_text(encoding="utf-8") if kubectl_log.exists() else "<missing kubectl log>"
            raise AssertionError(result.stdout + result.stderr + "\n[kubectl-calls]\n" + kubectl_calls)
        return result.stdout + result.stderr


def keycloak_optional_module_guard_contract(
    *,
    module_id: str,
    module_enabled_env_name: str,
    module_label: str,
    state_artifact_name: str,
    env_overrides: dict[str, str],
) -> str:
    state_env = REPO_ROOT / "artifacts" / "infra" / f"{state_artifact_name}.env"
    state_json = REPO_ROOT / "artifacts" / "infra" / f"{state_artifact_name}.json"
    for path in (state_env, state_json):
        if path.exists():
            path.unlink()

    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/state.sh"
source "{REPO_ROOT}/scripts/lib/infra/keycloak_identity_contract.sh"
if keycloak_optional_module_reconcile_should_run \
  "{module_id}" \
  "{module_enabled_env_name}" \
  "{state_artifact_name}" \
  "{module_label}"; then
  echo "proceed=true"
else
  echo "proceed=false"
fi
if [[ -f "{state_env}" ]]; then
  cat "{state_env}"
else
  echo "state_file=missing"
fi
"""
    result = run(["bash", "-lc", script], env_overrides)
    for path in (state_env, state_json):
        if path.exists():
            path.unlink()
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def keycloak_optional_module_helper_primitives_contract() -> str:
    state_artifact_name = "test_keycloak_helper_primitives"
    state_env = REPO_ROOT / "artifacts" / "infra" / f"{state_artifact_name}.env"
    state_json = REPO_ROOT / "artifacts" / "infra" / f"{state_artifact_name}.json"
    for path in (state_env, state_json):
        if path.exists():
            path.unlink()

    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/state.sh"
source "{REPO_ROOT}/scripts/lib/infra/keycloak_identity_contract.sh"
# Override contract loading to make fallback/override behavior deterministic.
keycloak_identity_contract_load_realm() {{
  KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME=""
  KEYCLOAK_IDENTITY_CONTRACT_ROLE_NAMES_CSV="Reader"
  KEYCLOAK_IDENTITY_CONTRACT_ADMIN_ROLE=""
  KEYCLOAK_IDENTITY_CONTRACT_CLIENT_DISPLAY_NAME=""
}}
keycloak_identity_contract_resolve_effective_realm_settings \
  "workflows" \
  "default-realm" \
  "Admin,User" \
  "Admin" \
  "Default Display"
printf 'effective_realm=%s\\n' "$KEYCLOAK_IDENTITY_EFFECTIVE_REALM_NAME"
printf 'effective_roles=%s\\n' "$KEYCLOAK_IDENTITY_EFFECTIVE_ROLE_NAMES_CSV"
printf 'effective_admin_role=%s\\n' "$KEYCLOAK_IDENTITY_EFFECTIVE_ADMIN_ROLE"
printf 'effective_display=%s\\n' "$KEYCLOAK_IDENTITY_EFFECTIVE_CLIENT_DISPLAY_NAME"
tokens="global-token-sentinel"
printf 'csv_append=%s\\n' "$(keycloak_csv_append_unique "Admin,User" "Viewer")"
printf 'csv_duplicate=%s\\n' "$(keycloak_csv_append_unique "Admin,User" "User")"
printf 'tokens_after=%s\\n' "$tokens"
printf 'origin=%s\\n' "$(keycloak_url_origin "https://example.com/path/to/callback")"
state_file="$(keycloak_optional_module_write_reconciled_state "{state_artifact_name}" "sample_key=sample_value")"
printf 'state_file=%s\\n' "$state_file"
cat "$state_file"
"""
    result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": "stackit-dev"})
    for path in (state_env, state_json):
        if path.exists():
            path.unlink()
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def run_local_post_deploy_hook_contract(
    *,
    profile: str,
    enabled: str,
    required: str,
    hook_cmd: str,
    state_namespace: str | None = None,
) -> tuple[int, str]:
    state_namespace_export = ""
    if state_namespace:
        state_namespace_export = f'export STATE_NAMESPACE="{state_namespace}"\n'
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/state.sh"
source "{REPO_ROOT}/scripts/lib/infra/local_post_deploy_hook.sh"
rm -f "$ROOT_DIR/artifacts/infra/local_post_deploy_hook.env" "$ROOT_DIR/artifacts/infra/local_post_deploy_hook.json"
rm -f "$ROOT_DIR/artifacts/apps/local_post_deploy_hook.env" "$ROOT_DIR/artifacts/apps/local_post_deploy_hook.json"
{state_namespace_export}
local_post_deploy_hook_run
state_file="$ROOT_DIR/artifacts/infra/local_post_deploy_hook.env"
if [[ -f "$state_file" ]]; then
  cat "$state_file"
fi
if [[ -f "$ROOT_DIR/artifacts/apps/local_post_deploy_hook.env" ]]; then
  echo "unexpected_apps_state_file=true"
fi
"""
    result = run(
        ["bash", "-lc", script],
        {
            "BLUEPRINT_PROFILE": profile,
            "LOCAL_POST_DEPLOY_HOOK_ENABLED": enabled,
            "LOCAL_POST_DEPLOY_HOOK_REQUIRED": required,
            "LOCAL_POST_DEPLOY_HOOK_CMD": hook_cmd,
        },
    )
    return result.returncode, result.stdout + result.stderr


def terraform_backend_init_contract(*, bucket: str, region: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        terraform_dir = Path(tmpdir) / "terraform"
        terraform_dir.mkdir()
        (terraform_dir / "main.tf").write_text("terraform {}\n", encoding="utf-8")
        backend_file = Path(tmpdir) / "backend.hcl"
        backend_file.write_text('bucket = "placeholder"\n', encoding="utf-8")
        captured_args = Path(tmpdir) / "terraform-args.txt"
        terraform = bin_dir / "terraform"
        terraform.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'printf "%s\\n" "$*" > "{captured_args}"',
                    'if printf "%s" "$*" | grep -q " init "; then',
                    "  exit 0",
                    "fi",
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        terraform.chmod(0o755)

        script = f"""
export PATH="{bin_dir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export DRY_RUN="false"
export STACKIT_TFSTATE_ACCESS_KEY_ID="access"
export STACKIT_TFSTATE_SECRET_ACCESS_KEY="secret"
export STACKIT_TFSTATE_BUCKET="{bucket}"
export STACKIT_REGION="{region}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
terraform_backend_init "{terraform_dir}" "{backend_file}"
cat "{captured_args}"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout


def profile_module_enablement_contract(module_defaults: dict[str, bool], env: dict[str, str] | None = None) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        profile_path = repo_root / "scripts/lib/infra/profile.sh"
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text((REPO_ROOT / "scripts/lib/infra/profile.sh").read_text(encoding="utf-8"), encoding="utf-8")

        contract_schema_path = repo_root / "scripts/lib/blueprint/contract_schema.py"
        contract_schema_path.parent.mkdir(parents=True, exist_ok=True)
        contract_schema_path.write_text(
            (REPO_ROOT / "scripts/lib/blueprint/contract_schema.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        contract_runtime_cli_path = repo_root / "scripts/lib/blueprint/contract_runtime_cli.py"
        contract_runtime_cli_path.parent.mkdir(parents=True, exist_ok=True)
        contract_runtime_cli_path.write_text(
            (REPO_ROOT / "scripts/lib/blueprint/contract_runtime_cli.py").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        contract = (REPO_ROOT / "blueprint/contract.yaml").read_text(encoding="utf-8")
        contract = re.sub(
            r"^(\s*repo_mode:\s*).+$",
            r"\1generated-consumer",
            contract,
            count=1,
            flags=re.MULTILINE,
        )
        for module, enabled in module_defaults.items():
            contract = re.sub(
                rf"(^\s{{6}}{re.escape(module)}:\n(?:\s{{8}}.*\n)*?\s{{8}}enabled_by_default:\s*)(true|false)",
                rf"\1{'true' if enabled else 'false'}",
                contract,
                count=1,
                flags=re.MULTILINE,
            )
        contract_path = repo_root / "blueprint/contract.yaml"
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(contract, encoding="utf-8")

        script = f"""
source "{profile_path}"
printf 'postgres=%s\\n' "$(is_module_enabled postgres && echo true || echo false)"
printf 'public_endpoints=%s\\n' "$(is_module_enabled public-endpoints && echo true || echo false)"
printf 'enabled_modules=%s\\n' "$(enabled_modules_csv)"
"""
        result = run(["bash", "-lc", script], env)
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout + result.stderr


def contract_test_fast_pytest_args_for_repo_mode(repo_mode: str) -> tuple[int, str]:
    contract_path = REPO_ROOT / "blueprint" / "contract.yaml"
    original_contract = contract_path.read_text(encoding="utf-8")
    patched_contract = re.sub(
        r"^(\s*repo_mode:\s*).+$",
        rf"\1{repo_mode}",
        original_contract,
        count=1,
        flags=re.MULTILINE,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        stub_pytest = Path(tmpdir) / "pytest"
        stub_pytest.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'printf "PYTEST_ARGS=%s\\n" "$*"',
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        stub_pytest.chmod(0o755)

        try:
            if patched_contract != original_contract:
                contract_path.write_text(patched_contract, encoding="utf-8")
            result = run(
                ["scripts/bin/infra/contract_test_fast.sh"],
                {"PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"},
            )
        finally:
            contract_path.write_text(original_contract, encoding="utf-8")

    return result.returncode, result.stdout + result.stderr


def terraform_backend_apply_failure_contract() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        bin_dir = Path(tmpdir) / "bin"
        bin_dir.mkdir()
        terraform_dir = Path(tmpdir) / "terraform"
        terraform_dir.mkdir()
        (terraform_dir / "main.tf").write_text("terraform {}\n", encoding="utf-8")
        backend_file = Path(tmpdir) / "backend.hcl"
        backend_file.write_text('bucket = "placeholder"\n', encoding="utf-8")
        var_file = Path(tmpdir) / "dev.tfvars"
        var_file.write_text('environment = "dev"\n', encoding="utf-8")
        terraform = bin_dir / "terraform"
        terraform.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'if printf "%s" "$*" | grep -q " init "; then',
                    "  exit 0",
                    "fi",
                    'if printf "%s" "$*" | grep -q " apply "; then',
                    "  exit 23",
                    "fi",
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        terraform.chmod(0o755)

        script = f"""
export PATH="{bin_dir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export DRY_RUN="false"
export STACKIT_TFSTATE_ACCESS_KEY_ID="access"
export STACKIT_TFSTATE_SECRET_ACCESS_KEY="secret"
export STACKIT_TFSTATE_BUCKET="runtime-state"
export STACKIT_REGION="eu01"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
set +e
run_terraform_action_with_backend apply "{terraform_dir}" "{backend_file}" "{var_file}"
status="$?"
set -e
printf 'status=%s\\n' "$status"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout


def blueprint_namespace_cleanup_contract() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir()
        kubectl = Path(tmpdir) / "kubectl"
        kubectl.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    f'STATE_DIR="{state_dir}"',
                    'if [ "$1" = "--context=docker-desktop" ] && [ "$2" = "config" ] && [ "$3" = "view" ] && [ "$4" = "--raw" ] && [ "$5" = "--minify" ] && [ "$6" = "--flatten" ]; then',
                    "  cat <<'EOF'",
                    "apiVersion: v1",
                    "kind: Config",
                    "clusters:",
                    "- cluster:",
                    "    server: https://docker-desktop.example:6443",
                    "  name: docker-desktop",
                    "contexts:",
                    "- context:",
                    "    cluster: docker-desktop",
                    "    user: docker-desktop",
                    "  name: docker-desktop",
                    "current-context: docker-desktop",
                    "users:",
                    "- name: docker-desktop",
                    "  user:",
                    "    token: placeholder",
                    "EOF",
                    "  exit 0",
                    "fi",
                    'while [ "$1" = "--kubeconfig" ] || [ "$1" = "--context" ]; do',
                    "  shift 2",
                    "done",
                    'if [ "$1" = "delete" ] && [ "$2" = "namespace" ]; then',
                    '  touch "$STATE_DIR/$3.deleted"',
                    "  exit 0",
                    "fi",
                    'if [ "$1" = "get" ] && [ "$2" = "namespace" ]; then',
                    '  if [ -f "$STATE_DIR/$3.deleted" ]; then',
                    "    exit 1",
                    "  fi",
                    '  printf "%s\\n" "$3"',
                    "  exit 0",
                    "fi",
                    'printf \'unexpected kubectl call: %s\\n\' \"$*\" >&2',
                    "exit 1",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        kubectl.chmod(0o755)

        script = f"""
export PATH="{tmpdir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export DRY_RUN="false"
export LOCAL_KUBE_CONTEXT="docker-desktop"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/tooling.sh"
delete_blueprint_managed_namespaces 5 "contract_namespace_cleanup"
"""
        result = run(["bash", "-lc", script])
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout + result.stderr


def env_file_defaults_contract() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / "repo.init.env"
        env_file.write_text(
            "\n".join(
                [
                    "BLUEPRINT_REPO_NAME=repo-from-file",
                    "BLUEPRINT_GITHUB_ORG=org-from-file",
                    "BLUEPRINT_GITHUB_REPO=repo-from-file",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
export BLUEPRINT_GITHUB_ORG="explicit-org"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
load_env_file_defaults "{env_file}"
printf 'repo=%s\\n' "$BLUEPRINT_REPO_NAME"
printf 'org=%s\\n' "$BLUEPRINT_GITHUB_ORG"
printf 'gh_repo=%s\\n' "$BLUEPRINT_GITHUB_REPO"
"""
        result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        return result.stdout + result.stderr


def init_placeholder_sanitization_contract() -> str:
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
export BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS="true"
source "{REPO_ROOT}/scripts/lib/blueprint/contract_runtime.sh"
unset BLUEPRINT_CONTRACT_RUNTIME_ALLOW_DEFAULTS
export BLUEPRINT_REPO_NAME="your-platform-blueprint"
export BLUEPRINT_GITHUB_ORG="your-github-org"
export BLUEPRINT_GITHUB_REPO="repo-from-user"
export BLUEPRINT_DOCS_TITLE="Your Platform Blueprint"
blueprint_sanitize_init_placeholder_defaults
printf 'repo=%s\\n' "${{BLUEPRINT_REPO_NAME-__unset__}}"
printf 'org=%s\\n' "${{BLUEPRINT_GITHUB_ORG-__unset__}}"
printf 'repo_name=%s\\n' "${{BLUEPRINT_GITHUB_REPO-__unset__}}"
printf 'docs_title=%s\\n' "${{BLUEPRINT_DOCS_TITLE-__unset__}}"
"""
    result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


def audit_helm_chart_repo_prefix_contract() -> tuple[set[str], set[str]]:
    audit_script = (REPO_ROOT / "scripts/bin/infra/audit_version.sh").read_text(encoding="utf-8")
    tooling_script = (REPO_ROOT / "scripts/lib/infra/tooling.sh").read_text(encoding="utf-8")

    chart_refs = re.findall(r'audit_helm_chart_pin\s+"[^"]+"\s+"([^"]+)"', audit_script)
    chart_repo_prefixes = {
        chart_ref.split("/", maxsplit=1)[0]
        for chart_ref in chart_refs
        if chart_ref and not chart_ref.startswith("oci://") and "/" in chart_ref
    }

    known_repo_prefixes = set(re.findall(r"^\s{2}([a-z0-9-]+)\)\s*$", tooling_script, flags=re.MULTILINE))
    return chart_repo_prefixes, known_repo_prefixes


class ToolingContractsTests(unittest.TestCase):
    def test_quality_infra_shell_source_graph_check_passes(self) -> None:
        result = run(["python3", "scripts/bin/quality/check_infra_shell_source_graph.py"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("quality-infra-shell-source-graph-check", result.stdout)

    def test_quality_sdd_check_passes(self) -> None:
        result = run(["python3", "scripts/bin/quality/check_sdd_assets.py"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("quality-sdd-check", result.stdout)

    def test_load_env_file_defaults_preserves_explicit_env(self) -> None:
        output = env_file_defaults_contract()
        self.assertIn("repo=repo-from-file", output)
        self.assertIn("org=explicit-org", output)
        self.assertIn("gh_repo=repo-from-file", output)

    def test_init_placeholder_sanitization_unsets_template_identity_values(self) -> None:
        output = init_placeholder_sanitization_contract()
        self.assertIn("repo=__unset__", output)
        self.assertIn("org=__unset__", output)
        self.assertIn("repo_name=repo-from-user", output)
        self.assertIn("docs_title=__unset__", output)

    def test_fallback_runtime_values_helper_keeps_stdout_machine_readable(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/fallback_runtime.sh"
export RABBITMQ_HELM_RELEASE=blueprint-rabbitmq
export RABBITMQ_PASSWORD_SECRET_NAME=blueprint-rabbitmq-auth
render_optional_module_values_file \
  "rabbitmq" \
  "infra/local/helm/rabbitmq/values.yaml" \
  "RABBITMQ_HELM_RELEASE=$RABBITMQ_HELM_RELEASE" \
  "RABBITMQ_PASSWORD_SECRET_NAME=$RABBITMQ_PASSWORD_SECRET_NAME"
"""
        result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f"{REPO_ROOT}/artifacts/infra/rendered/rabbitmq.values.yaml",
        )
        self.assertIn("optional_module_values_render_total", result.stderr)
        self.assertIn("rendered optional-module values artifact", result.stderr)

    def test_fallback_runtime_secret_helper_keeps_stdout_machine_readable(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/fallback_runtime.sh"
render_optional_module_secret_manifests "messaging" "blueprint-rabbitmq-auth" "rabbitmq-password=secret"
"""
        result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f"{REPO_ROOT}/artifacts/infra/rendered/secrets/secret-messaging-blueprint-rabbitmq-auth.yaml",
        )
        self.assertIn("optional_module_secret_render_total", result.stderr)

    def test_local_post_deploy_hook_skips_when_disabled(self) -> None:
        exit_code, output = run_local_post_deploy_hook_contract(
            profile="local-full",
            enabled="false",
            required="false",
            hook_cmd="echo should-not-run",
        )
        self.assertEqual(exit_code, 0, msg=output)
        self.assertIn("status=skipped", output)
        self.assertIn("reason=disabled", output)
        self.assertIn("mode=best-effort", output)
        self.assertIn("local_post_deploy_hook_duration_seconds", output)

    def test_local_post_deploy_hook_best_effort_failure_continues(self) -> None:
        exit_code, output = run_local_post_deploy_hook_contract(
            profile="local-full",
            enabled="true",
            required="false",
            hook_cmd="exit 12",
        )
        self.assertEqual(exit_code, 0, msg=output)
        self.assertIn("status=failure", output)
        self.assertIn("reason=command_failed", output)
        self.assertIn("mode=best-effort", output)
        self.assertIn("continuing chain", output)

    def test_local_post_deploy_hook_state_artifact_schema_contract_is_enforced(self) -> None:
        exit_code, output = run_local_post_deploy_hook_contract(
            profile="local-full",
            enabled="true",
            required="false",
            hook_cmd="echo post-deploy-ok",
        )
        self.assertEqual(exit_code, 0, msg=output)
        self.assertIn("local_post_deploy_hook_state_contract_validation_total", output)

        state_json = REPO_ROOT / "artifacts" / "infra" / "local_post_deploy_hook.json"
        self.assertTrue(state_json.exists(), msg=f"missing post-deploy hook state json: {state_json}")
        payload = json.loads(state_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["artifact"]["name"], "local_post_deploy_hook")
        self.assertEqual(payload["artifact"]["namespace"], "infra")
        self.assertEqual(payload["artifact"]["envPath"], "artifacts/infra/local_post_deploy_hook.env")
        self.assertEqual(payload["artifact"]["jsonPath"], "artifacts/infra/local_post_deploy_hook.json")
        self.assertIn(payload["entries"]["status"], {"success", "failure", "skipped"})
        self.assertIn(payload["entries"]["reason"], {"executed", "command_failed", "disabled", "non_local_profile"})

    def test_local_post_deploy_hook_forces_infra_namespace_even_when_state_namespace_is_overridden(self) -> None:
        exit_code, output = run_local_post_deploy_hook_contract(
            profile="local-full",
            enabled="false",
            required="false",
            hook_cmd="echo should-not-run",
            state_namespace="apps",
        )
        self.assertEqual(exit_code, 0, msg=output)
        self.assertNotIn("unexpected_apps_state_file=true", output)
        self.assertTrue((REPO_ROOT / "artifacts" / "infra" / "local_post_deploy_hook.env").exists())
        self.assertFalse((REPO_ROOT / "artifacts" / "apps" / "local_post_deploy_hook.env").exists())

    def test_local_post_deploy_hook_strict_failure_is_fail_fast(self) -> None:
        exit_code, output = run_local_post_deploy_hook_contract(
            profile="local-full",
            enabled="true",
            required="true",
            hook_cmd="exit 9",
        )
        self.assertNotEqual(exit_code, 0, msg=output)
        self.assertIn("status=failure", output)
        self.assertIn("reason=command_failed", output)
        self.assertIn("LOCAL_POST_DEPLOY_HOOK_REQUIRED=true", output)

    def test_help_reference_includes_primary_workflows(self) -> None:
        result = run(["make", "infra-help-reference"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Primary Workflows", result.stdout)
        self.assertIn("make quality-hooks-fast", result.stdout)
        self.assertIn("make quality-hooks-strict", result.stdout)
        self.assertIn("make quality-hooks-run", result.stdout)
        self.assertIn("make quality-sdd-check", result.stdout)
        self.assertIn("make quality-sdd-check-all", result.stdout)
        self.assertIn("make quality-docs-check-changed", result.stdout)
        self.assertIn("make blueprint-install-codex-skills", result.stdout)
        self.assertIn("make spec-scaffold SPEC_SLUG=<slug>", result.stdout)
        self.assertIn("make spec-impact", result.stdout)
        self.assertIn("make spec-evidence-manifest", result.stdout)
        self.assertIn("make spec-context-pack", result.stdout)
        self.assertIn("make spec-pr-context", result.stdout)
        self.assertIn("make quality-hardening-review", result.stdout)
        self.assertIn("make blueprint-bootstrap", result.stdout)
        self.assertIn("make infra-bootstrap", result.stdout)
        self.assertIn("make infra-port-forward-start", result.stdout)
        self.assertIn("make infra-port-forward-stop", result.stdout)
        self.assertIn("make infra-port-forward-cleanup", result.stdout)
        self.assertIn("quality-docs-sync-core-targets", result.stdout)

    def test_prereqs_help_mentions_extended_optional_tooling(self) -> None:
        result = run(["scripts/bin/infra/prereqs.sh", "--help"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("terraform kubectl helm docker kind uv gh jq pnpm kustomize nc", result.stdout)
        self.assertIn("Canonical required Python modules:", result.stdout)
        self.assertIn("pytest", result.stdout)

    def test_prereqs_script_enforces_required_pytest_python_module(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/prereqs.sh").read_text(encoding="utf-8")
        self.assertIn('check_or_install_python_module "pytest" "required"', script)
        self.assertIn("python_module_available()", script)

    def test_prereqs_optional_stackit_gate_is_controlled_only_by_install_optional(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/prereqs.sh").read_text(encoding="utf-8")
        self.assertIn('elif [[ "$PREREQS_INSTALL_OPTIONAL" == "true" ]]; then', script)
        self.assertNotIn(
            'elif [[ "$PREREQS_INSTALL_OPTIONAL" == "true" || "$PREREQS_AUTO_INSTALL" == "true" ]]; then',
            script,
        )

    def test_prereqs_selected_bucket_still_honors_auto_install_for_missing_tools(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/prereqs.sh").read_text(encoding="utf-8")
        match = re.search(
            r"^check_or_install\(\)\s*\{(?P<body>.*?)(?=^\})",
            script,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, msg="check_or_install() definition not found in prereqs.sh")
        function_body = match.group("body")
        self.assertIn('if [[ "$PREREQS_AUTO_INSTALL" == "true" ]]; then', function_body)

    def test_audit_version_chart_refs_have_known_helm_repo_prefixes(self) -> None:
        chart_repo_prefixes, known_repo_prefixes = audit_helm_chart_repo_prefix_contract()
        missing = sorted(chart_repo_prefixes - known_repo_prefixes)
        self.assertFalse(
            missing,
            msg=(
                "audit_version.sh chart refs use unknown repo prefixes without tooling mapping: "
                + ", ".join(missing)
            ),
        )
        self.assertIn("codecentric", known_repo_prefixes)

    def test_e2e_aggregate_script_supports_scope_and_budget_contract(self) -> None:
        script = (REPO_ROOT / "scripts/bin/platform/test/e2e_all_local.sh").read_text(encoding="utf-8")
        self.assertIn("--scope fast|full", script)
        self.assertIn("E2E_FAST_BUDGET_SECONDS", script)
        self.assertIn("E2E_FULL_BUDGET_SECONDS", script)
        self.assertIn("aggregate_e2e_budget_total", script)
        self.assertIn("touchpoints-test-e2e", script)
        self.assertIn(
            'run_cmd make -C "$ROOT_DIR" DRY_RUN=true BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" infra-provision-deploy',
            script,
        )
        self.assertIn(
            'run_cmd make -C "$ROOT_DIR" DRY_RUN=false BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" infra-provision-deploy',
            script,
        )

    def test_apps_bootstrap_versions_lock_keeps_trailing_newline(self) -> None:
        versions_lock = REPO_ROOT / "apps" / "catalog" / "versions.lock"
        original = versions_lock.read_bytes() if versions_lock.exists() else None
        try:
            result = run(
                ["make", "apps-bootstrap"],
                {
                    "BLUEPRINT_PROFILE": "local-lite",
                    "OBSERVABILITY_ENABLED": "false",
                },
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(versions_lock.exists(), msg="apps/catalog/versions.lock should be created by apps-bootstrap")
            content = versions_lock.read_bytes()
            self.assertTrue(
                content.endswith(b"\n") and not content.endswith(b"\n\n"),
                msg="apps/catalog/versions.lock must end with exactly one trailing newline",
            )
        finally:
            if original is not None:
                versions_lock.write_bytes(original)

    def test_argocd_local_overlay_resolves_with_default_kustomize_load_restrictions(self) -> None:
        kubectl_check = run(["bash", "-lc", "command -v kubectl >/dev/null 2>&1"])
        if kubectl_check.returncode != 0:
            self.skipTest("kubectl is required for local overlay kustomize regression check")
        kustomize_help_check = run(["bash", "-lc", "kubectl kustomize --help >/dev/null 2>&1"])
        if kustomize_help_check.returncode != 0:
            self.skipTest("kubectl kustomize is required for local overlay kustomize regression check")

        result = run(["kubectl", "kustomize", str(REPO_ROOT / "infra/gitops/argocd/overlays/local")])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("name: platform-keycloak-local", result.stdout)

    def test_argocd_topology_validate_uses_explicit_load_restrictor_none(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/argocd_topology_validate.sh").read_text(encoding="utf-8")
        self.assertIn("kustomize build --load-restrictor=LoadRestrictionsNone \"$base_dir\"", script)
        self.assertIn("kustomize build --load-restrictor=LoadRestrictionsNone \"$overlay_dir\"", script)

    def test_kustomize_apply_contract_avoids_load_restrictions_none_fallback(self) -> None:
        tooling = (REPO_ROOT / "scripts/lib/infra/tooling.sh").read_text(encoding="utf-8")
        match = re.search(
            r"^run_kustomize_apply\(\)\s*\{\n(?P<body>.*?)(?=^\})",
            tooling,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, msg="run_kustomize_apply() definition not found in tooling.sh")
        function_body = match.group("body")

        self.assertIn("run_kubectl_with_active_access apply -k", function_body)
        self.assertNotIn("LoadRestrictionsNone", function_body)
        self.assertNotIn("--load-restrictor", function_body)

    def test_quality_test_pyramid_target_passes(self) -> None:
        result = run(["make", "quality-test-pyramid"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[test-pyramid] OK", result.stdout)

    def test_profile_uses_generated_repo_contract_when_module_env_is_unset(self) -> None:
        resolved = profile_module_enablement_contract({"postgres": True, "public-endpoints": False})
        self.assertIn("postgres=true", resolved)
        self.assertIn("public_endpoints=false", resolved)
        self.assertIn("enabled_modules=postgres", resolved)

    def test_profile_env_flags_override_generated_repo_contract_defaults(self) -> None:
        resolved = profile_module_enablement_contract(
            {"postgres": True, "public-endpoints": False},
            {"POSTGRES_ENABLED": "false", "PUBLIC_ENDPOINTS_ENABLED": "true"},
        )
        self.assertIn("postgres=false", resolved)
        self.assertIn("public_endpoints=true", resolved)
        self.assertIn("enabled_modules=public-endpoints", resolved)

    def test_contract_test_fast_includes_template_source_only_tests_in_template_source_mode(self) -> None:
        exit_code, output = contract_test_fast_pytest_args_for_repo_mode("template-source")
        self.assertEqual(exit_code, 0, msg=output)
        self.assertIn("tests/blueprint/test_upgrade_fixture_matrix.py", output)
        self.assertIn("tests/infra/test_optional_module_required_env_contract.py", output)

    def test_contract_test_fast_skips_only_template_source_only_tests_in_generated_consumer_mode(self) -> None:
        exit_code, output = contract_test_fast_pytest_args_for_repo_mode("generated-consumer")
        self.assertEqual(exit_code, 0, msg=output)
        self.assertNotIn("tests/blueprint/test_upgrade_fixture_matrix.py", output)
        self.assertIn("tests/infra/test_optional_module_required_env_contract.py", output)
        self.assertIn("tests/infra/test_runtime_identity_contract_cli.py", output)
        self.assertIn("tests/infra/test_argocd_repo_contract_cli.py", output)
        self.assertIn("tests/infra/test_state_artifact_contract.py", output)
        self.assertIn("tests/infra/test_root_dir_resolution.py", output)

    def test_contract_test_fast_fails_fast_when_template_source_required_test_is_missing(self) -> None:
        fixture_matrix_test = REPO_ROOT / "tests" / "blueprint" / "test_upgrade_fixture_matrix.py"
        backup_path = fixture_matrix_test.with_name("test_upgrade_fixture_matrix.py.backup")
        fixture_matrix_test.rename(backup_path)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                stub_pytest = Path(tmpdir) / "pytest"
                stub_pytest.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                stub_pytest.chmod(0o755)
                result = run(
                    ["scripts/bin/infra/contract_test_fast.sh"],
                    {"PATH": f"{tmpdir}:{os.environ.get('PATH', '')}"},
                )
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            combined_output = result.stdout + result.stderr
            self.assertIn("missing required fast contract test path(s)", combined_output)
            self.assertIn("tests/blueprint/test_upgrade_fixture_matrix.py", combined_output)
        finally:
            backup_path.rename(fixture_matrix_test)

    def test_infra_validate_renders_makefile_from_contract_defaults(self) -> None:
        contract_path = REPO_ROOT / "blueprint" / "contract.yaml"
        contract_template_path = (
            REPO_ROOT / "scripts" / "templates" / "blueprint" / "bootstrap" / "blueprint" / "contract.yaml"
        )
        makefile_path = REPO_ROOT / "make" / "blueprint.generated.mk"
        original_contract = contract_path.read_text(encoding="utf-8")
        original_contract_template = contract_template_path.read_text(encoding="utf-8")
        original_makefile = makefile_path.read_text(encoding="utf-8")

        try:
            patched_contract = original_contract.replace(
                "      postgres:\n        enabled_by_default: false\n        enable_flag: POSTGRES_ENABLED",
                "      postgres:\n        enabled_by_default: true\n        enable_flag: POSTGRES_ENABLED",
                1,
            ).replace(
                "      public-endpoints:\n        enabled_by_default: false\n        enable_flag: PUBLIC_ENDPOINTS_ENABLED",
                "      public-endpoints:\n        enabled_by_default: true\n        enable_flag: PUBLIC_ENDPOINTS_ENABLED",
                1,
            )
            self.assertNotEqual(
                patched_contract,
                original_contract,
                msg="contract patch failed; expected enabled_by_default=true for regression scenario",
            )
            contract_path.write_text(patched_contract, encoding="utf-8")
            contract_template_path.write_text(patched_contract, encoding="utf-8")

            render = run(
                [
                    "env",
                    "-u",
                    "OBSERVABILITY_ENABLED",
                    "-u",
                    "WORKFLOWS_ENABLED",
                    "-u",
                    "LANGFUSE_ENABLED",
                    "-u",
                    "POSTGRES_ENABLED",
                    "-u",
                    "NEO4J_ENABLED",
                    "-u",
                    "OBJECT_STORAGE_ENABLED",
                    "-u",
                    "RABBITMQ_ENABLED",
                    "-u",
                    "OPENSEARCH_ENABLED",
                    "-u",
                    "DNS_ENABLED",
                    "-u",
                    "PUBLIC_ENDPOINTS_ENABLED",
                    "-u",
                    "SECRETS_MANAGER_ENABLED",
                    "-u",
                    "KMS_ENABLED",
                    "-u",
                    "IDENTITY_AWARE_PROXY_ENABLED",
                    "make",
                    "blueprint-render-makefile",
                ]
            )
            self.assertEqual(render.returncode, 0, msg=render.stdout + render.stderr)
            expected_makefile = makefile_path.read_text(encoding="utf-8")
            self.assertIn("infra-postgres-plan", expected_makefile)
            self.assertIn("infra-public-endpoints-plan", expected_makefile)

            validate = run(
                ["make", "infra-validate"],
                {
                    "GITHUB_REF_NAME": "fix/infra-validate-regression",
                    "BLUEPRINT_PROFILE": "local-lite",
                    "OBSERVABILITY_ENABLED": "false",
                    "POSTGRES_ENABLED": "false",
                    "PUBLIC_ENDPOINTS_ENABLED": "false",
                },
            )
            self.assertEqual(validate.returncode, 0, msg=validate.stdout + validate.stderr)
            self.assertIn(
                "infra validate ignored transient module toggle overrides while rendering makefile",
                validate.stdout + validate.stderr,
            )
            actual_makefile = makefile_path.read_text(encoding="utf-8")
            self.assertEqual(
                actual_makefile,
                expected_makefile,
                msg=(
                    "infra-validate should render from contract defaults and must not rewrite "
                    "make/blueprint.generated.mk from transient runtime module flags"
                ),
            )
        finally:
            contract_path.write_text(original_contract, encoding="utf-8")
            contract_template_path.write_text(original_contract_template, encoding="utf-8")
            makefile_path.write_text(original_makefile, encoding="utf-8")

    def test_touchpoints_pnpm_lane_unsets_no_color_for_child_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            touchpoints_root = Path(tmpdir) / "apps" / "touchpoints"
            package_dir = touchpoints_root / "service-a"
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "package.json").write_text(
                json.dumps(
                    {
                        "name": "service-a",
                        "version": "1.0.0",
                        "scripts": {
                            "test:e2e": "echo should-not-run",
                        },
                    }
                ),
                encoding="utf-8",
            )

            bin_dir = Path(tmpdir) / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            pnpm = bin_dir / "pnpm"
            pnpm.write_text(
                "\n".join(
                    [
                        "#!/bin/sh",
                        'printf "pnpm_no_color=%s\\n" "${NO_COLOR-unset}"',
                        'printf "pnpm_force_color=%s\\n" "${FORCE_COLOR-unset}"',
                        'printf "pnpm_args=%s\\n" "$*"',
                        "exit 0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            pnpm.chmod(0o755)

            script = f"""
export PATH="{bin_dir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
export NO_COLOR="1"
export FORCE_COLOR="1"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/platform/testing.sh"
run_touchpoints_pnpm_lane "touchpoints e2e" "playwright" "{touchpoints_root}" "test:e2e"
"""
            result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            output = result.stdout + result.stderr
            self.assertIn("touchpoints touchpoints_e2e lane unsetting NO_COLOR", output)
            self.assertIn("pnpm_no_color=unset", output)
            self.assertIn("pnpm_force_color=1", output)
            self.assertIn("+ env -u NO_COLOR pnpm --dir", output)
            self.assertIn("no_color_sanitized=true", output)

    def test_touchpoints_pnpm_lane_no_color_sanitized_false_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            touchpoints_root = Path(tmpdir) / "apps" / "touchpoints"
            package_dir = touchpoints_root / "service-a"
            package_dir.mkdir(parents=True, exist_ok=True)
            (package_dir / "package.json").write_text(
                json.dumps(
                    {
                        "name": "service-a",
                        "version": "1.0.0",
                        "scripts": {
                            "test:e2e": "echo should-not-run",
                        },
                    }
                ),
                encoding="utf-8",
            )

            bin_dir = Path(tmpdir) / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            pnpm = bin_dir / "pnpm"
            pnpm.write_text(
                "\n".join(
                    [
                        "#!/bin/sh",
                        'printf "pnpm_no_color=%s\\n" "${NO_COLOR-unset}"',
                        "exit 0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            pnpm.chmod(0o755)

            script = f"""
export PATH="{bin_dir}:$PATH"
export ROOT_DIR="{REPO_ROOT}"
unset NO_COLOR
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/platform/testing.sh"
run_touchpoints_pnpm_lane "touchpoints e2e" "playwright" "{touchpoints_root}" "test:e2e"
"""
            result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            output = result.stdout + result.stderr
            self.assertNotIn("unsetting NO_COLOR", output)
            self.assertIn("pnpm_no_color=unset", output)
            self.assertIn("no_color_sanitized=false", output)

    def test_optional_module_execution_resolves_provider_backed_stackit_modes(self) -> None:
        resolved = resolve_optional_module_execution("postgres", "plan", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_stackit_layer_var_args_normalize_provider_backed_module_inputs(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stack_paths.sh"
source "{REPO_ROOT}/scripts/lib/infra/stackit_layers.sh"
stackit_layer_var_args foundation
"""
        result = run(
            ["bash", "-lc", script],
            {
                "BLUEPRINT_PROFILE": "stackit-dev",
                "POSTGRES_ENABLED": "true",
                "OBJECT_STORAGE_ENABLED": "true",
                "OPENSEARCH_ENABLED": "true",
                "DNS_ENABLED": "true",
                "SECRETS_MANAGER_ENABLED": "true",
                "POSTGRES_INSTANCE_NAME": "bp-postgres-stackit",
                "POSTGRES_DB_NAME": "platform",
                "POSTGRES_USER": "platform",
                "POSTGRES_VERSION": "16",
                "POSTGRES_EXTRA_ALLOWED_CIDRS": "10.0.0.0/24, 10.0.1.0/24",
                "OBJECT_STORAGE_BUCKET_NAME": "bp-assets-stackit",
                "OPENSEARCH_INSTANCE_NAME": "bp-opensearch-stackit",
                "OPENSEARCH_VERSION": "2.17",
                "OPENSEARCH_PLAN_NAME": "stackit-opensearch-single",
                "DNS_ZONE_NAME": "marketplace-stackit",
                "DNS_ZONE_FQDN": "marketplace-stackit.example.",
                "SECRETS_MANAGER_INSTANCE_NAME": "bp-secrets-stackit",
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("-var=postgres_instance_name=bp-postgres-stackit", result.stdout)
        self.assertIn("-var=postgres_db_name=platform", result.stdout)
        self.assertIn("-var=postgres_username=platform", result.stdout)
        self.assertIn("-var=postgres_version=16", result.stdout)
        self.assertIn('-var=postgres_acl=["10.0.0.0/24", "10.0.1.0/24"]', result.stdout)
        self.assertIn("-var=object_storage_bucket_name=bp-assets-stackit", result.stdout)
        self.assertIn("-var=opensearch_instance_name=bp-opensearch-stackit", result.stdout)
        self.assertIn("-var=opensearch_version=2.17", result.stdout)
        self.assertIn("-var=opensearch_plan_name=stackit-opensearch-single", result.stdout)
        self.assertIn('-var=dns_zone_fqdns=["marketplace-stackit.example."]', result.stdout)
        self.assertIn("-var=secrets_manager_instance_name=bp-secrets-stackit", result.stdout)

    def test_stackit_layers_resolve_paths_without_caller_sourcing_stack_paths(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stackit_layers.sh"
printf 'dir=%s\\n' "$(stackit_layer_dir foundation)"
printf 'backend=%s\\n' "$(stackit_layer_backend_file foundation)"
printf 'vars=%s\\n' "$(stackit_layer_var_file foundation)"
"""
        result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": "stackit-dev"})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"dir={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", result.stdout)
        self.assertIn(f"backend={REPO_ROOT}/infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl", result.stdout)
        self.assertIn(f"vars={REPO_ROOT}/infra/cloud/stackit/terraform/foundation/env/dev.tfvars", result.stdout)

    def test_stackit_provider_backed_helpers_prefer_foundation_outputs(self) -> None:
        payload = json.dumps(
            {
                "postgres_host": {"value": "managed-postgres.eu01.onstackit.cloud"},
                "postgres_port": {"value": 15432},
                "postgres_username": {"value": "managed-user"},
                "postgres_password": {"value": "managed-password"},
                "postgres_database": {"value": "managed-db"},
                "object_storage_bucket_name": {"value": "managed-assets"},
                "object_storage_access_key": {"value": "managed-access"},
                "object_storage_secret_access_key": {"value": "managed-secret"},
                "dns_zone_ids": {"value": {"marketplace-stackit.example.": "zone-12345"}},
                "rabbitmq_uri": {
                    "value": "amqps://managed-user:managed-password@managed-rabbitmq.eu01.onstackit.cloud:5671"
                },
                "rabbitmq_host": {"value": "managed-rabbitmq.eu01.onstackit.cloud"},
                "rabbitmq_port": {"value": 5671},
                "rabbitmq_username": {"value": "managed-user"},
                "rabbitmq_password": {"value": "managed-password"},
                "opensearch_host": {"value": "managed-opensearch.eu01.onstackit.cloud"},
                "opensearch_hosts": {"value": "managed-opensearch-1.eu01.onstackit.cloud,managed-opensearch-2.eu01.onstackit.cloud"},
                "opensearch_port": {"value": 443},
                "opensearch_scheme": {"value": "https"},
                "opensearch_uri": {"value": "https://managed-opensearch.eu01.onstackit.cloud:443"},
                "opensearch_dashboard_url": {"value": "https://managed-opensearch.eu01.onstackit.cloud"},
                "opensearch_username": {"value": "managed-opensearch-user"},
                "opensearch_password": {"value": "managed-opensearch-password"},
            }
        )
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/postgres.sh"
source "{REPO_ROOT}/scripts/lib/infra/object_storage.sh"
source "{REPO_ROOT}/scripts/lib/infra/dns.sh"
source "{REPO_ROOT}/scripts/lib/infra/rabbitmq.sh"
source "{REPO_ROOT}/scripts/lib/infra/opensearch.sh"
rabbitmq_init_env
opensearch_init_env
printf 'postgres_host=%s\\n' "$(postgres_host)"
printf 'postgres_port=%s\\n' "$(postgres_port)"
printf 'postgres_user=%s\\n' "$(postgres_username)"
printf 'postgres_password=%s\\n' "$(postgres_password)"
printf 'postgres_db=%s\\n' "$(postgres_database)"
printf 'object_storage_bucket=%s\\n' "$(object_storage_bucket_name)"
printf 'object_storage_access=%s\\n' "$(object_storage_access_key)"
printf 'object_storage_secret=%s\\n' "$(object_storage_secret_key)"
printf 'dns_zone_id=%s\\n' "$(dns_zone_id)"
printf 'rabbitmq_uri=%s\\n' "$(rabbitmq_uri)"
printf 'rabbitmq_host=%s\\n' "$(rabbitmq_host)"
printf 'rabbitmq_port=%s\\n' "$(rabbitmq_port)"
printf 'rabbitmq_user=%s\\n' "$(rabbitmq_username)"
printf 'rabbitmq_password=%s\\n' "$(rabbitmq_password)"
printf 'opensearch_host=%s\\n' "$(opensearch_host)"
printf 'opensearch_hosts=%s\\n' "$(opensearch_hosts)"
printf 'opensearch_port=%s\\n' "$(opensearch_port)"
printf 'opensearch_scheme=%s\\n' "$(opensearch_scheme)"
printf 'opensearch_uri=%s\\n' "$(opensearch_uri)"
printf 'opensearch_dashboard=%s\\n' "$(opensearch_dashboard_url)"
printf 'opensearch_user=%s\\n' "$(opensearch_username)"
printf 'opensearch_password=%s\\n' "$(opensearch_password)"
printf 'dsn=%s\\n' "$(postgres_dsn)"
"""
        result = run(
            ["bash", "-lc", script],
            {
                "BLUEPRINT_PROFILE": "stackit-dev",
                "STACKIT_REGION": "eu01",
                "POSTGRES_INSTANCE_NAME": "placeholder-postgres",
                "POSTGRES_DB_NAME": "placeholder-db",
                "POSTGRES_USER": "placeholder-user",
                "POSTGRES_PASSWORD": "placeholder-password",
                "POSTGRES_PORT": "5432",
                "OBJECT_STORAGE_BUCKET_NAME": "placeholder-assets",
                "OBJECT_STORAGE_ACCESS_KEY": "placeholder-access",
                "OBJECT_STORAGE_SECRET_KEY": "placeholder-secret",
                "DNS_ZONE_NAME": "placeholder-zone",
                "DNS_ZONE_FQDN": "marketplace-stackit.example.",
                "OPENSEARCH_INSTANCE_NAME": "placeholder-opensearch",
                "OPENSEARCH_VERSION": "2.17",
                "OPENSEARCH_PLAN_NAME": "stackit-opensearch-single",
                "STACKIT_FOUNDATION_OUTPUTS_LOADED": "true",
                "STACKIT_FOUNDATION_OUTPUTS_JSON": payload,
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("postgres_host=managed-postgres.eu01.onstackit.cloud", result.stdout)
        self.assertIn("postgres_port=15432", result.stdout)
        self.assertIn("postgres_user=managed-user", result.stdout)
        self.assertIn("postgres_password=managed-password", result.stdout)
        self.assertIn("postgres_db=managed-db", result.stdout)
        self.assertIn("object_storage_bucket=managed-assets", result.stdout)
        self.assertIn("object_storage_access=managed-access", result.stdout)
        self.assertIn("object_storage_secret=managed-secret", result.stdout)
        self.assertIn("dns_zone_id=zone-12345", result.stdout)
        self.assertIn(
            "rabbitmq_uri=amqps://managed-user:managed-password@managed-rabbitmq.eu01.onstackit.cloud:5671",
            result.stdout,
        )
        self.assertIn("rabbitmq_host=managed-rabbitmq.eu01.onstackit.cloud", result.stdout)
        self.assertIn("rabbitmq_port=5671", result.stdout)
        self.assertIn("rabbitmq_user=managed-user", result.stdout)
        self.assertIn("rabbitmq_password=managed-password", result.stdout)
        self.assertIn("opensearch_host=managed-opensearch.eu01.onstackit.cloud", result.stdout)
        self.assertIn(
            "opensearch_hosts=managed-opensearch-1.eu01.onstackit.cloud,managed-opensearch-2.eu01.onstackit.cloud",
            result.stdout,
        )
        self.assertIn("opensearch_port=443", result.stdout)
        self.assertIn("opensearch_scheme=https", result.stdout)
        self.assertIn("opensearch_uri=https://managed-opensearch.eu01.onstackit.cloud:443", result.stdout)
        self.assertIn("opensearch_dashboard=https://managed-opensearch.eu01.onstackit.cloud", result.stdout)
        self.assertIn("opensearch_user=managed-opensearch-user", result.stdout)
        self.assertIn("opensearch_password=managed-opensearch-password", result.stdout)
        self.assertIn(
            "dsn=postgresql://managed-user:managed-password@managed-postgres.eu01.onstackit.cloud:15432/managed-db",
            result.stdout,
        )

    def test_optional_module_execution_resolves_local_fallback_modes(self) -> None:
        resolved = resolve_optional_module_execution("rabbitmq", "plan", profile="local-full")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=helm", resolved)
        self.assertIn(f"path={REPO_ROOT}/artifacts/infra/rendered/rabbitmq.values.yaml", resolved)

    def test_optional_module_execution_resolves_local_provider_noop_mode_for_opensearch(self) -> None:
        resolved = resolve_optional_module_execution("opensearch", "plan", profile="local-full")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=noop", resolved)
        self.assertIn("path=none", resolved)

    def test_local_context_prefers_docker_desktop_on_workstations(self) -> None:
        resolved = resolve_local_kube_context_contract(
            ["kind-blueprint-e2e", "docker-desktop", "kind-ppwr-local"],
            "kind-ppwr-local",
        )
        self.assertIn("context=docker-desktop", resolved)
        self.assertIn("source=docker-desktop-preferred", resolved)

    def test_local_context_prefers_kind_in_ci(self) -> None:
        resolved = resolve_local_kube_context_contract(
            ["docker-desktop", "kind-blueprint-e2e", "kind-ppwr-local"],
            "docker-desktop",
            ci="true",
        )
        self.assertIn("context=kind-blueprint-e2e", resolved)
        self.assertIn("source=ci-kind-blueprint-e2e", resolved)

    def test_local_context_override_env_wins(self) -> None:
        resolved = resolve_local_kube_context_contract(
            ["docker-desktop", "kind-blueprint-e2e"],
            "docker-desktop",
            local_kube_context="kind-blueprint-e2e",
        )
        self.assertIn("context=kind-blueprint-e2e", resolved)
        self.assertIn("source=env", resolved)

    def test_helm_upgrade_uses_explicit_active_kube_access_args(self) -> None:
        output = run_helm_upgrade_with_context_contract()
        self.assertIn("--kubeconfig", output)
        self.assertIn("--kube-context docker-desktop", output)
        self.assertIn("upgrade --install contract-postgres bitnami/postgresql", output)

    def test_helm_repo_update_retries_until_success(self) -> None:
        output = helm_repo_update_retry_contract(failures_before_success=2, max_attempts=4)
        self.assertIn("attempts=3", output)
        self.assertIn("helm_repo_update_retry_total", output)

    def test_port_forward_helpers_are_context_safe_and_cleanup_registry(self) -> None:
        output, calls = port_forward_lifecycle_contract()
        self.assertIn("remaining=0", output)
        self.assertIn("--kubeconfig", calls)
        self.assertIn("--context docker-desktop -n apps port-forward svc/demo 18080:8080", calls)

    def test_port_forward_stop_timeout_keeps_registry_until_forced_cleanup(self) -> None:
        output = port_forward_stop_timeout_contract()
        self.assertIn("stop_status=1", output)
        self.assertIn("registry_after_stop=1", output)
        self.assertIn("registry_after_cleanup=0", output)

    def test_public_endpoints_destroy_clears_stuck_gatewayclass_finalizer(self) -> None:
        result = public_endpoints_delete_contract(require_finalizer_patch=True)
        self.assertIn("patch_state=patched", result)
        self.assertIn("public_endpoints_gatewayclass_finalizer_clear_total", result)

    def test_public_endpoints_destroy_skips_gatewayclass_patch_when_not_needed(self) -> None:
        result = public_endpoints_delete_contract(require_finalizer_patch=False)
        self.assertIn("patch_state=none", result)
        self.assertNotIn("public_endpoints_gatewayclass_finalizer_clear_total", result)

    def test_keycloak_identity_reconcile_exec_uses_active_access_args_local_profile(self) -> None:
        result = keycloak_exec_active_access_contract(profile="local-full", context_name="docker-desktop")
        self.assertIn("--kubeconfig", result)
        self.assertIn("--context docker-desktop -n security get pod", result)
        self.assertIn("--context docker-desktop -n security get secret keycloak-runtime-credentials", result)
        self.assertIn("--context docker-desktop -n security exec keycloak-0 -- env", result)

    def test_keycloak_identity_reconcile_exec_uses_active_access_args_stackit_profile(self) -> None:
        result = keycloak_exec_active_access_contract(profile="stackit-dev", context_name="stackit-dev-cluster")
        self.assertIn("--kubeconfig", result)
        self.assertIn("--context stackit-dev-cluster -n security get pod", result)
        self.assertIn("--context stackit-dev-cluster -n security get secret keycloak-runtime-credentials", result)
        self.assertIn("--context stackit-dev-cluster -n security exec keycloak-0 -- env", result)

    def test_keycloak_optional_module_guard_writes_disabled_state_when_toggle_off(self) -> None:
        result = keycloak_optional_module_guard_contract(
            module_id="workflows",
            module_enabled_env_name="WORKFLOWS_ENABLED",
            module_label="workflows",
            state_artifact_name="test_keycloak_guard",
            env_overrides={
                "BLUEPRINT_PROFILE": "stackit-dev",
                "WORKFLOWS_ENABLED": "true",
                "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED": "false",
            },
        )
        self.assertIn("proceed=false", result)
        self.assertIn("status=disabled", result)
        self.assertIn("reason=keycloak_optional_module_reconciliation_toggle_off", result)

    def test_keycloak_optional_module_guard_skips_without_state_when_module_disabled(self) -> None:
        result = keycloak_optional_module_guard_contract(
            module_id="langfuse",
            module_enabled_env_name="LANGFUSE_ENABLED",
            module_label="langfuse",
            state_artifact_name="test_keycloak_guard_module_disabled",
            env_overrides={
                "BLUEPRINT_PROFILE": "stackit-dev",
                "LANGFUSE_ENABLED": "false",
                "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED": "true",
            },
        )
        self.assertIn("proceed=false", result)
        self.assertIn("state_file=missing", result)

    def test_keycloak_optional_module_guard_proceeds_when_enabled(self) -> None:
        result = keycloak_optional_module_guard_contract(
            module_id="workflows",
            module_enabled_env_name="WORKFLOWS_ENABLED",
            module_label="workflows",
            state_artifact_name="test_keycloak_guard_enabled",
            env_overrides={
                "BLUEPRINT_PROFILE": "stackit-dev",
                "WORKFLOWS_ENABLED": "true",
                "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED": "true",
            },
        )
        self.assertIn("proceed=true", result)
        self.assertIn("state_file=missing", result)

    def test_keycloak_optional_module_helper_primitives_contract(self) -> None:
        result = keycloak_optional_module_helper_primitives_contract()
        self.assertIn("effective_realm=default-realm", result)
        self.assertIn("effective_roles=Reader", result)
        self.assertIn("effective_admin_role=Admin", result)
        self.assertIn("effective_display=Default Display", result)
        self.assertIn("csv_append=Admin,User,Viewer", result)
        self.assertIn("csv_duplicate=Admin,User", result)
        self.assertIn("tokens_after=global-token-sentinel", result)
        self.assertIn("origin=https://example.com", result)
        self.assertIn("status=reconciled", result)
        self.assertIn("sample_key=sample_value", result)

    def test_cluster_crd_exists_detects_present_crd(self) -> None:
        self.assertTrue(cluster_crd_exists_contract(["applications.argoproj.io"], "applications.argoproj.io"))

    def test_cluster_crd_exists_detects_missing_crd(self) -> None:
        self.assertFalse(cluster_crd_exists_contract(["applications.argoproj.io"], "appprojects.argoproj.io"))

    def test_optional_module_execution_resolves_stackit_provider_backed_rabbitmq_modes(self) -> None:
        resolved = resolve_optional_module_execution("rabbitmq", "apply", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_optional_module_execution_resolves_stackit_chart_applications(self) -> None:
        resolved = resolve_optional_module_execution("public-endpoints", "apply", profile="stackit-dev")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=argocd_application_chart", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/gitops/argocd/optional/dev/public-endpoints.yaml", resolved)

    def test_optional_module_execution_resolves_stackit_provider_backed_kms_modes(self) -> None:
        resolved = resolve_optional_module_execution("kms", "apply", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_optional_module_execution_resolves_local_noop_modes(self) -> None:
        resolved = resolve_optional_module_execution("dns", "destroy", profile="local-full")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=noop", resolved)
        self.assertIn("destroy is a contract no-op", resolved)

    def test_optional_module_execution_resolves_manifest_fallback_across_profiles(self) -> None:
        resolved = resolve_optional_module_execution("langfuse", "destroy", profile="local-full")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=argocd_optional_manifest", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/gitops/argocd/optional/local/langfuse.yaml", resolved)

    def test_core_runtime_bootstrap_polls_crd_conditions_directly(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/core_runtime_bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn(".status.conditions", script)
        self.assertIn("runtime_crd_wait_total", script)
        self.assertNotIn("kubectl wait --for=condition=Established", script)

    def test_stackit_foundation_apply_materializes_kubeconfig_artifact(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/stackit_foundation_apply.sh").read_text(encoding="utf-8")
        self.assertIn("stackit_foundation_fetch_kubeconfig.sh", script)
        self.assertIn("kubeconfig_state=", script)
        self.assertIn("run_stackit_foundation_apply_with_retry", script)
        self.assertIn("stackit_foundation_apply_retry_total", script)
        self.assertIn('terraform -chdir="$terraform_dir" untaint "stackit_postgresflex_instance.foundation[0]"', script)
        self.assertIn("stackit_foundation_apply_untaint_total", script)
        self.assertIn("Requested instance with ID:", script)

    def test_terraform_backend_init_honors_runtime_bucket_and_region_overrides(self) -> None:
        output = terraform_backend_init_contract(bucket="runtime-state", region="eu01")
        self.assertIn("-backend-config=bucket=runtime-state", output)
        self.assertIn("-backend-config=region=eu01", output)

    def test_run_terraform_action_with_backend_propagates_apply_failure_outside_errexit(self) -> None:
        output = terraform_backend_apply_failure_contract()
        self.assertIn("status=23", output)

    def test_delete_blueprint_managed_namespaces_requests_delete_and_waits(self) -> None:
        output = blueprint_namespace_cleanup_contract()
        self.assertIn("contract_namespace_cleanup_delete_total", output)
        self.assertIn("namespace=apps status=requested", output)
        self.assertIn("namespace=network status=requested", output)
        self.assertIn("contract_namespace_cleanup_wait_total", output)
        self.assertIn("namespace=argocd status=deleted", output)

    def test_local_destroy_all_waits_for_namespace_deletion(self) -> None:
        script = (REPO_ROOT / "scripts/bin/infra/local_destroy_all.sh").read_text(encoding="utf-8")
        self.assertIn("wait_for_namespace_deletion()", script)
        self.assertIn("local_destroy_all_namespace_wait_total", script)
        self.assertIn("still in `Terminating`", script)

    def test_k8s_wait_extracts_server_url_from_kubeconfig(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            kubeconfig = Path(tmpdir) / "stackit.yaml"
            kubeconfig.write_text(
                "\n".join(
                    [
                        "apiVersion: v1",
                        "kind: Config",
                        "clusters:",
                        "- cluster:",
                        "    server: https://api.example.internal:6443",
                        "  name: stackit-dev",
                        "contexts:",
                        "- context:",
                        "    cluster: stackit-dev",
                        "    user: stackit-dev",
                        "  name: stackit-dev",
                        "current-context: stackit-dev",
                        "users:",
                        "- name: stackit-dev",
                        "  user:",
                        "    token: placeholder",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/k8s_wait.sh"
printf 'server=%s\\n' "$(k8s_kubeconfig_server_url "{kubeconfig}")"
printf 'host=%s\\n' "$(k8s_kubeconfig_server_host "{kubeconfig}")"
"""
            result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("server=https://api.example.internal:6443", result.stdout)
            self.assertIn("host=api.example.internal", result.stdout)


class PlatformPythonHelperGuardTests(unittest.TestCase):
    """Guard tests for FR-009 / AC-006: platform shell scripts MUST reference existing Python helpers.

    These tests ensure that python3 "$ROOT_DIR/scripts/lib/..." invocations in
    scripts/bin/platform/** resolve to files that actually exist in the repository.
    They fail if helper files are moved without updating the caller references.
    """

    # Matches "$ROOT_DIR/scripts/lib/...py" in both direct python3 invocations
    # and variable assignments that are later passed to python3.
    _PYTHON_REF_RE = re.compile(r'"\$ROOT_DIR/(scripts/lib/[^"]+\.py)"')

    def _extract_python_helper_refs(self, script_path: Path) -> list[str]:
        text = script_path.read_text(encoding="utf-8")
        return self._PYTHON_REF_RE.findall(text)

    def test_smoke_sh_python_helper_refs_exist(self) -> None:
        """T-105: scripts/bin/platform/apps/smoke.sh python3 helper references must exist."""
        script = REPO_ROOT / "scripts/bin/platform/apps/smoke.sh"
        refs = self._extract_python_helper_refs(script)
        self.assertTrue(refs, msg="expected at least one python3 helper ref in smoke.sh")
        for ref in refs:
            self.assertTrue(
                (REPO_ROOT / ref).is_file(),
                msg=f"smoke.sh references missing helper: {ref}",
            )

    def test_reconcile_argocd_repo_credentials_sh_python_helper_refs_exist(self) -> None:
        """T-106: scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh python3 refs must exist."""
        script = REPO_ROOT / "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh"
        refs = self._extract_python_helper_refs(script)
        self.assertTrue(refs, msg="expected at least one python3 helper ref in reconcile_argocd_repo_credentials.sh")
        for ref in refs:
            self.assertTrue(
                (REPO_ROOT / ref).is_file(),
                msg=f"reconcile_argocd_repo_credentials.sh references missing helper: {ref}",
            )

    def test_quality_infra_shell_source_graph_check_passes_with_current_platform_refs(self) -> None:
        """Guard passes when all scripts/bin/platform/** python3 helper references resolve to existing files.

        The negative path (AC-006: guard fails on a missing helper) is covered transitively:
        test_smoke_sh_python_helper_refs_exist and test_reconcile_argocd_repo_credentials_sh_python_helper_refs_exist
        would fail first if a caller were updated without also updating the helper path, causing
        this end-to-end pass assertion to become unreachable in practice.
        """
        result = run(["python3", "scripts/bin/quality/check_infra_shell_source_graph.py"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("quality-infra-shell-source-graph-check", result.stdout)


if __name__ == "__main__":
    unittest.main()
