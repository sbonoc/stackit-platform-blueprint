from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "managed-cache" / "module.contract.yaml"
_BLUEPRINT_CONTRACT = REPO_ROOT / "blueprint" / "contract.yaml"
_MANAGED_CACHE_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "managed_cache.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "managed_cache_apply.sh"
_PLAN_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "managed_cache_plan.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "managed_cache_smoke.sh"
_DESTROY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "managed_cache_destroy.sh"
_TF_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "managed-cache"
_TF_FOUNDATION_OUTPUTS = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation" / "outputs.tf"
_TF_FOUNDATION_MAIN = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation" / "main.tf"
_LOCAL_HELM_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "managed-cache" / "values.yaml"
_GENERATED_MK = REPO_ROOT / "make" / "blueprint.generated.mk"
_MK_TEMPLATE = REPO_ROOT / "scripts" / "templates" / "blueprint" / "bootstrap" / "make" / "blueprint.generated.mk.tmpl"
_RENDER_MAKEFILE = REPO_ROOT / "scripts" / "bin" / "blueprint" / "render_makefile.sh"

_CONTRACT_OUTPUTS = (
    "MANAGED_CACHE_HOST",
    "MANAGED_CACHE_PORT",
    "MANAGED_CACHE_USERNAME",
    "MANAGED_CACHE_PASSWORD",
    "MANAGED_CACHE_URI",
)

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "host=blueprint-managed-cache.managed-cache.svc.cluster.local",
        "port=6379",
        "uri=redis://:managed-cache-password@blueprint-managed-cache.managed-cache.svc.cluster.local:6379/0",
        "timestamp_utc=2026-05-27T00:00:00Z",
    ]
)


# ---------------------------------------------------------------------------
# Slice 1: Module contract + shell lib skeleton
# ---------------------------------------------------------------------------


class ManagedCacheContractTests(unittest.TestCase):
    def test_module_contract_file_exists(self) -> None:
        self.assertTrue(
            _CONTRACT_FILE.exists(),
            msg=f"module.contract.yaml must exist at {_CONTRACT_FILE}",
        )

    def test_managed_cache_enabled_flag_declared(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "MANAGED_CACHE_ENABLED",
            content,
            msg="module.contract.yaml must declare MANAGED_CACHE_ENABLED enable_flag",
        )

    def test_contract_outputs_declared(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        for output in _CONTRACT_OUTPUTS:
            self.assertIn(
                output,
                content,
                msg=f"module.contract.yaml outputs.produced must include {output}",
            )

    def test_blueprint_contract_registers_managed_cache(self) -> None:
        content = _BLUEPRINT_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "managed-cache",
            content,
            msg="blueprint/contract.yaml must register managed-cache under optional_modules",
        )


class ManagedCacheShellLibTests(unittest.TestCase):
    def test_managed_cache_host_function_exists(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_host()",
            content,
            msg="managed_cache.sh must define managed_cache_host()",
        )

    def test_managed_cache_port_function_exists(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_port()",
            content,
            msg="managed_cache.sh must define managed_cache_port()",
        )

    def test_managed_cache_username_function_exists(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_username()",
            content,
            msg="managed_cache.sh must define managed_cache_username()",
        )

    def test_managed_cache_password_function_exists(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_password()",
            content,
            msg="managed_cache.sh must define managed_cache_password()",
        )

    def test_managed_cache_uri_function_exists(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_uri()",
            content,
            msg="managed_cache.sh must define managed_cache_uri()",
        )


# ---------------------------------------------------------------------------
# Slice 2: Make targets
# ---------------------------------------------------------------------------


class ManagedCacheMakeTargetTests(unittest.TestCase):
    def test_make_target_plan_exists(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-managed-cache-plan",
            content,
            msg="render_makefile.sh must define infra-managed-cache-plan target",
        )

    def test_make_target_apply_exists(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-managed-cache-apply",
            content,
            msg="render_makefile.sh must define infra-managed-cache-apply target",
        )

    def test_make_target_smoke_exists(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-managed-cache-smoke",
            content,
            msg="render_makefile.sh must define infra-managed-cache-smoke target",
        )

    def test_make_target_destroy_exists(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-managed-cache-destroy",
            content,
            msg="render_makefile.sh must define infra-managed-cache-destroy target",
        )

    def test_apply_bin_script_exists(self) -> None:
        self.assertTrue(
            _APPLY_SH.exists(),
            msg=f"managed_cache_apply.sh must exist at {_APPLY_SH}",
        )


# ---------------------------------------------------------------------------
# Slice 3: TF module
# ---------------------------------------------------------------------------


class ManagedCacheTerraformModuleTests(unittest.TestCase):
    def test_tf_module_main_exists(self) -> None:
        self.assertTrue(
            (_TF_MODULE_DIR / "main.tf").exists(),
            msg=f"TF module main.tf must exist at {_TF_MODULE_DIR / 'main.tf'}",
        )

    def test_tf_module_declares_redis_instance(self) -> None:
        content = (_TF_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackit_redis_instance",
            content,
            msg="TF module main.tf must declare stackit_redis_instance resource",
        )

    def test_tf_module_declares_redis_credential(self) -> None:
        content = (_TF_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackit_redis_credential",
            content,
            msg="TF module main.tf must declare stackit_redis_credential resource",
        )

    def test_tf_foundation_wires_managed_cache_module(self) -> None:
        content = _TF_FOUNDATION_MAIN.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache",
            content,
            msg="foundation main.tf must wire the managed-cache module",
        )

    def test_tf_foundation_outputs_managed_cache_host(self) -> None:
        content = _TF_FOUNDATION_OUTPUTS.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_host",
            content,
            msg="foundation outputs.tf must expose managed_cache_host",
        )


# ---------------------------------------------------------------------------
# Slice 4: Local lane Helm values
# ---------------------------------------------------------------------------


class ManagedCacheLocalHelmTests(unittest.TestCase):
    def test_local_helm_values_exists(self) -> None:
        self.assertTrue(
            _LOCAL_HELM_VALUES.exists(),
            msg=f"local helm values.yaml must exist at {_LOCAL_HELM_VALUES}",
        )

    def test_local_helm_values_uses_bitnami_redis(self) -> None:
        content = _LOCAL_HELM_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "bitnami",
            content,
            msg="local helm values.yaml must reference bitnami chart for local lane",
        )


# ---------------------------------------------------------------------------
# Slice 5: Shell lib + apply script — full implementation
# ---------------------------------------------------------------------------


class ManagedCacheShellLibImplementationTests(unittest.TestCase):
    def test_managed_cache_uri_uses_redis_scheme(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "redis://",
            content,
            msg="managed_cache.sh must produce redis:// URIs",
        )

    def test_managed_cache_host_local_lane_uses_in_cluster_dns(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "svc.cluster.local",
            content,
            msg="managed_cache.sh must use in-cluster DNS for local lane host",
        )

    def test_managed_cache_host_stackit_reads_foundation_output(self) -> None:
        content = _MANAGED_CACHE_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "stackit_foundation_output_value_or_default",
            content,
            msg="managed_cache.sh must read foundation outputs on STACKIT lane",
        )

    def test_runtime_state_does_not_contain_password(self) -> None:
        apply_src = _APPLY_SH.read_text(encoding="utf-8")
        self.assertNotIn(
            "password=",
            apply_src,
            msg="managed_cache_apply.sh must not pass password= to write_state_file (NFR-SEC-001)",
        )

    def test_apply_script_calls_init_env(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "managed_cache_init_env",
            content,
            msg="managed_cache_apply.sh must call managed_cache_init_env",
        )
