"""Tests for v1.12.2 bugfixes (issues #383, #384, #385, #386, #366, #395).

AC-001: POSTGRES_INSTANCE_NAME is optional_env in module contract
AC-002: OBJECT_STORAGE_BUCKET_NAME is optional_env in module contract
AC-003: RABBITMQ_INSTANCE_NAME is optional_env; stackit_layers.sh emits -var= only when non-empty
AC-004: OPENSEARCH_INSTANCE_NAME is optional_env; OPENSEARCH_VERSION default is "2"; plan slug corrected
AC-005: POSTGRES_PASSWORD optional on STACKIT profiles (postgres_init_env does not require it)
AC-006: rabbitmq values files contain global.security.allowInsecureImages: true
AC-007: public_endpoints_deploy.sh does NOT call run_manifest_apply for gateway in argocd_application_chart mode
"""
from __future__ import annotations

import unittest
import yaml
from pathlib import Path
from tests._shared.helpers import REPO_ROOT

_POSTGRES_CONTRACT = REPO_ROOT / "blueprint" / "modules" / "postgres" / "module.contract.yaml"
_OBJECT_STORAGE_CONTRACT = REPO_ROOT / "blueprint" / "modules" / "object-storage" / "module.contract.yaml"
_RABBITMQ_CONTRACT = REPO_ROOT / "blueprint" / "modules" / "rabbitmq" / "module.contract.yaml"
_OPENSEARCH_CONTRACT = REPO_ROOT / "blueprint" / "modules" / "opensearch" / "module.contract.yaml"

_STACKIT_LAYERS = REPO_ROOT / "scripts" / "lib" / "infra" / "stackit_layers.sh"
_OBJECT_STORAGE_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "object_storage.sh"
_RABBITMQ_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "rabbitmq.sh"
_OPENSEARCH_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "opensearch.sh"
_POSTGRES_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "postgres.sh"

_RABBITMQ_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "rabbitmq" / "values.yaml"
_RABBITMQ_BOOTSTRAP_VALUES = (
    REPO_ROOT
    / "scripts"
    / "templates"
    / "infra"
    / "bootstrap"
    / "infra"
    / "local"
    / "helm"
    / "rabbitmq"
    / "values.yaml"
)
_PUBLIC_ENDPOINTS_DEPLOY = REPO_ROOT / "scripts" / "bin" / "infra" / "public_endpoints_deploy.sh"


def _load_contract(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _required_env(contract: dict) -> list:
    return contract.get("spec", {}).get("inputs", {}).get("required_env", [])


def _optional_env(contract: dict) -> list:
    return contract.get("spec", {}).get("inputs", {}).get("optional_env", [])


class AC001PostgresInstanceNameOptionalTests(unittest.TestCase):
    """AC-001: POSTGRES_INSTANCE_NAME must be in optional_env, NOT required_env."""

    def _contract(self) -> dict:
        return _load_contract(_POSTGRES_CONTRACT)

    def test_postgres_instance_name_not_in_required_env(self) -> None:
        self.assertNotIn(
            "POSTGRES_INSTANCE_NAME",
            _required_env(self._contract()),
            msg="AC-001: POSTGRES_INSTANCE_NAME must NOT be in required_env (fixes #383)",
        )

    def test_postgres_instance_name_in_optional_env(self) -> None:
        self.assertIn(
            "POSTGRES_INSTANCE_NAME",
            _optional_env(self._contract()),
            msg="AC-001: POSTGRES_INSTANCE_NAME MUST be in optional_env (fixes #383)",
        )

    def test_stackit_layers_emits_postgres_instance_name_only_when_set(self) -> None:
        content = _STACKIT_LAYERS.read_text(encoding="utf-8")
        # The conditional emit guard must exist: [[ -n "${POSTGRES_INSTANCE_NAME:-}" ]]
        self.assertIn(
            'POSTGRES_INSTANCE_NAME',
            content,
            msg="AC-001: stackit_layers.sh must reference POSTGRES_INSTANCE_NAME",
        )
        # The unconditional require_env_vars for POSTGRES_INSTANCE_NAME must be gone
        # (require_env_vars POSTGRES_INSTANCE_NAME is the pre-fix form in the postgres block)
        import re
        # Match the exact old pattern that required it unconditionally in the postgres block
        unconditional_require = re.search(
            r'require_env_vars[^\n]*POSTGRES_INSTANCE_NAME',
            content,
        )
        self.assertIsNone(
            unconditional_require,
            msg="AC-001: stackit_layers.sh must NOT unconditionally require POSTGRES_INSTANCE_NAME",
        )


class AC002ObjectStorageBucketNameOptionalTests(unittest.TestCase):
    """AC-002: OBJECT_STORAGE_BUCKET_NAME must be in optional_env, NOT required_env."""

    def _contract(self) -> dict:
        return _load_contract(_OBJECT_STORAGE_CONTRACT)

    def test_object_storage_bucket_name_not_in_required_env(self) -> None:
        self.assertNotIn(
            "OBJECT_STORAGE_BUCKET_NAME",
            _required_env(self._contract()),
            msg="AC-002: OBJECT_STORAGE_BUCKET_NAME must NOT be in required_env (fixes #384)",
        )

    def test_object_storage_bucket_name_in_optional_env(self) -> None:
        self.assertIn(
            "OBJECT_STORAGE_BUCKET_NAME",
            _optional_env(self._contract()),
            msg="AC-002: OBJECT_STORAGE_BUCKET_NAME MUST be in optional_env (fixes #384)",
        )

    def test_stackit_layers_emits_object_storage_bucket_name_only_when_set(self) -> None:
        content = _STACKIT_LAYERS.read_text(encoding="utf-8")
        import re
        unconditional_require = re.search(
            r'require_env_vars[^\n]*OBJECT_STORAGE_BUCKET_NAME',
            content,
        )
        self.assertIsNone(
            unconditional_require,
            msg="AC-002: stackit_layers.sh must NOT unconditionally require OBJECT_STORAGE_BUCKET_NAME",
        )

    def test_object_storage_sh_does_not_require_bucket_name(self) -> None:
        content = _OBJECT_STORAGE_SH.read_text(encoding="utf-8")
        import re
        # The inert require_env_vars that appears after set_default_env must be removed
        self.assertIsNone(
            re.search(r'require_env_vars[^\n]*OBJECT_STORAGE_BUCKET_NAME', content),
            msg="AC-002: object_storage.sh must NOT call require_env_vars OBJECT_STORAGE_BUCKET_NAME (inert after set_default_env, fixes #384)",
        )


class AC003RabbitmqInstanceNameOptionalTests(unittest.TestCase):
    """AC-003: RABBITMQ_INSTANCE_NAME must be in optional_env, NOT required_env."""

    def _contract(self) -> dict:
        return _load_contract(_RABBITMQ_CONTRACT)

    def test_rabbitmq_instance_name_not_in_required_env(self) -> None:
        self.assertNotIn(
            "RABBITMQ_INSTANCE_NAME",
            _required_env(self._contract()),
            msg="AC-003: RABBITMQ_INSTANCE_NAME must NOT be in required_env (fixes #385)",
        )

    def test_rabbitmq_instance_name_in_optional_env(self) -> None:
        self.assertIn(
            "RABBITMQ_INSTANCE_NAME",
            _optional_env(self._contract()),
            msg="AC-003: RABBITMQ_INSTANCE_NAME MUST be in optional_env (fixes #385)",
        )

    def test_rabbitmq_sh_does_not_unconditionally_require_instance_name(self) -> None:
        content = _RABBITMQ_SH.read_text(encoding="utf-8")
        import re
        self.assertIsNone(
            re.search(r'require_env_vars[^\n]*RABBITMQ_INSTANCE_NAME', content),
            msg="AC-003: rabbitmq.sh must NOT unconditionally require RABBITMQ_INSTANCE_NAME (fixes #385)",
        )

    def test_stackit_layers_does_not_unconditionally_require_rabbitmq_instance_name(self) -> None:
        content = _STACKIT_LAYERS.read_text(encoding="utf-8")
        import re
        self.assertIsNone(
            re.search(r'require_env_vars[^\n]*RABBITMQ_INSTANCE_NAME', content),
            msg="AC-003: stackit_layers.sh must NOT unconditionally require RABBITMQ_INSTANCE_NAME",
        )


class AC004OpensearchInstanceNameOptionalTests(unittest.TestCase):
    """AC-004: OPENSEARCH_INSTANCE_NAME optional; version default '2'; plan slug corrected."""

    def _contract(self) -> dict:
        return _load_contract(_OPENSEARCH_CONTRACT)

    def test_opensearch_instance_name_not_in_required_env(self) -> None:
        self.assertNotIn(
            "OPENSEARCH_INSTANCE_NAME",
            _required_env(self._contract()),
            msg="AC-004: OPENSEARCH_INSTANCE_NAME must NOT be in required_env (fixes #385)",
        )

    def test_opensearch_instance_name_in_optional_env(self) -> None:
        self.assertIn(
            "OPENSEARCH_INSTANCE_NAME",
            _optional_env(self._contract()),
            msg="AC-004: OPENSEARCH_INSTANCE_NAME MUST be in optional_env (fixes #385)",
        )

    def test_opensearch_version_default_is_major_only(self) -> None:
        content = _OPENSEARCH_SH.read_text(encoding="utf-8")
        self.assertIn(
            'set_default_env OPENSEARCH_VERSION "2"',
            content,
            msg='AC-004: OPENSEARCH_VERSION default must be "2" (major-only, fixes #385)',
        )

    def test_opensearch_sh_does_not_unconditionally_require_instance_name(self) -> None:
        content = _OPENSEARCH_SH.read_text(encoding="utf-8")
        import re
        self.assertIsNone(
            re.search(r'require_env_vars[^\n]*OPENSEARCH_INSTANCE_NAME', content),
            msg="AC-004: opensearch.sh must NOT unconditionally require OPENSEARCH_INSTANCE_NAME",
        )

    def test_stackit_layers_does_not_unconditionally_require_opensearch_instance_name(self) -> None:
        content = _STACKIT_LAYERS.read_text(encoding="utf-8")
        import re
        self.assertIsNone(
            re.search(r'require_env_vars[^\n]*OPENSEARCH_INSTANCE_NAME', content),
            msg="AC-004: stackit_layers.sh must NOT unconditionally require OPENSEARCH_INSTANCE_NAME",
        )

    def test_opensearch_plan_name_default_is_replica_plan(self) -> None:
        content = _OPENSEARCH_SH.read_text(encoding="utf-8")
        # The plan must be a replica plan slug, not the 'single' plan
        self.assertNotIn(
            'set_default_env OPENSEARCH_PLAN_NAME "stackit-opensearch-single"',
            content,
            msg="AC-004: OPENSEARCH_PLAN_NAME must not default to single-node plan (fixes #385)",
        )
        self.assertIn(
            "OPENSEARCH_PLAN_NAME",
            content,
            msg="AC-004: opensearch.sh must define OPENSEARCH_PLAN_NAME default",
        )


class AC005PostgresPasswordStackitOptionalTests(unittest.TestCase):
    """AC-005: postgres_init_env() must NOT require POSTGRES_PASSWORD on STACKIT profiles."""

    def test_postgres_password_not_in_required_env(self) -> None:
        contract = _load_contract(_POSTGRES_CONTRACT)
        self.assertNotIn(
            "POSTGRES_PASSWORD",
            _required_env(contract),
            msg="AC-005: POSTGRES_PASSWORD must NOT be in required_env (provider output, fixes #386)",
        )

    def test_postgres_password_in_optional_env(self) -> None:
        contract = _load_contract(_POSTGRES_CONTRACT)
        self.assertIn(
            "POSTGRES_PASSWORD",
            _optional_env(contract),
            msg="AC-005: POSTGRES_PASSWORD MUST be in optional_env (fixes #386)",
        )

    def test_postgres_sh_gates_password_require_on_non_stackit_profile(self) -> None:
        content = _POSTGRES_SH.read_text(encoding="utf-8")
        # The unconditional require must be replaced with a profile-gated require
        # The old pattern: require_env_vars POSTGRES_INSTANCE_NAME POSTGRES_DB_NAME POSTGRES_USER POSTGRES_PASSWORD
        self.assertNotIn(
            "require_env_vars POSTGRES_INSTANCE_NAME POSTGRES_DB_NAME POSTGRES_USER POSTGRES_PASSWORD",
            content,
            msg="AC-005: postgres.sh must NOT unconditionally require POSTGRES_PASSWORD (fixes #386)",
        )
        # Profile guard must be present
        self.assertIn(
            "is_stackit_profile",
            content,
            msg="AC-005: postgres.sh must use is_stackit_profile guard to gate POSTGRES_PASSWORD require",
        )


class AC006RabbitmqAllowInsecureImagesTests(unittest.TestCase):
    """AC-006: rabbitmq values files must have global.security.allowInsecureImages: true."""

    def _check_file(self, path: Path) -> None:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        global_section = parsed.get("global", {})
        security = global_section.get("security", {})
        self.assertTrue(
            security.get("allowInsecureImages", False),
            msg=f"AC-006: {path.name} must have global.security.allowInsecureImages: true (fixes #366)",
        )

    def test_seed_values_has_allow_insecure_images(self) -> None:
        self._check_file(_RABBITMQ_VALUES)

    def test_bootstrap_template_has_allow_insecure_images(self) -> None:
        self._check_file(_RABBITMQ_BOOTSTRAP_VALUES)


class AC007PublicEndpointsNoGatewayDriftTests(unittest.TestCase):
    """AC-007: public_endpoints_deploy.sh must NOT call run_manifest_apply for gateway in argocd_application_chart mode."""

    def test_argocd_application_chart_branch_does_not_apply_gateway_manifest(self) -> None:
        content = _PUBLIC_ENDPOINTS_DEPLOY.read_text(encoding="utf-8")
        import re
        # Find the argocd_application_chart case block
        # It starts at 'argocd_application_chart)' and ends at the next ';;' or 'esac'
        match = re.search(
            r'argocd_application_chart\)(.*?)(?:;;|\besac\b)',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(
            match,
            msg="AC-007: public_endpoints_deploy.sh must have an argocd_application_chart case branch",
        )
        branch_body = match.group(1)
        self.assertNotIn(
            "gateway_manifest_path",
            branch_body,
            msg="AC-007: argocd_application_chart branch must NOT apply gateway_manifest_path (GitOps owns it, fixes #395)",
        )
