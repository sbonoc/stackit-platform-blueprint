from __future__ import annotations

import json
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

    def test_help_reference_includes_primary_workflows(self) -> None:
        result = run(["make", "infra-help-reference"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Primary Workflows", result.stdout)
        self.assertIn("make quality-hooks-fast", result.stdout)
        self.assertIn("make quality-hooks-strict", result.stdout)
        self.assertIn("make quality-hooks-run", result.stdout)
        self.assertIn("make blueprint-bootstrap", result.stdout)
        self.assertIn("make infra-bootstrap", result.stdout)
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

        self.assertRegex(function_body, r"\bkubectl\s+apply\b.*\s-k\b")
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
                "DNS_ENABLED": "true",
                "SECRETS_MANAGER_ENABLED": "true",
                "POSTGRES_INSTANCE_NAME": "bp-postgres-stackit",
                "POSTGRES_DB_NAME": "platform",
                "POSTGRES_USER": "platform",
                "POSTGRES_VERSION": "16",
                "POSTGRES_EXTRA_ALLOWED_CIDRS": "10.0.0.0/24, 10.0.1.0/24",
                "OBJECT_STORAGE_BUCKET_NAME": "bp-assets-stackit",
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
rabbitmq_init_env
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
        self.assertIn(
            "dsn=postgresql://managed-user:managed-password@managed-postgres.eu01.onstackit.cloud:15432/managed-db",
            result.stdout,
        )

    def test_optional_module_execution_resolves_local_fallback_modes(self) -> None:
        resolved = resolve_optional_module_execution("rabbitmq", "plan", profile="local-full")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=helm", resolved)
        self.assertIn(f"path={REPO_ROOT}/artifacts/infra/rendered/rabbitmq.values.yaml", resolved)

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

    def test_public_endpoints_destroy_clears_stuck_gatewayclass_finalizer(self) -> None:
        result = public_endpoints_delete_contract(require_finalizer_patch=True)
        self.assertIn("patch_state=patched", result)
        self.assertIn("public_endpoints_gatewayclass_finalizer_clear_total", result)

    def test_public_endpoints_destroy_skips_gatewayclass_patch_when_not_needed(self) -> None:
        result = public_endpoints_delete_contract(require_finalizer_patch=False)
        self.assertIn("patch_state=none", result)
        self.assertNotIn("public_endpoints_gatewayclass_finalizer_clear_total", result)

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


if __name__ == "__main__":
    unittest.main()
