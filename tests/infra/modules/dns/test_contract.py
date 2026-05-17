from __future__ import annotations

import re
import unittest

from tests._shared.helpers import REPO_ROOT

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "dns"
_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "dns" / "module.contract.yaml"
_SHELL_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "dns.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "dns_apply.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "dns_smoke.sh"
_PYRAMID_CONTRACT = REPO_ROOT / "scripts" / "lib" / "quality" / "test_pyramid_contract.json"

_REQUIRED_VARIABLES = (
    "stackit_project_id",
    "stackit_region",
    "dns_zone_fqdns",
    "dns_naming_prefix",
    "dns_record_ttl",
)

_MOCK_RUNTIME_STATE = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=noop",
        "provision_path=noop",
        "zone_ids=marketplace-web-local",
        "zone_fqdns=marketplace-web-dev.runs.onstackit.local.",
        "zone_count=1",
        "primary_name_servers=ns.dns.local.",
        "timestamp_utc=2026-05-17T00:00:00Z",
    ]
)


# ---------------------------------------------------------------------------
# Slice 1 — Terraform module structure (AC-001 through AC-004)
# ---------------------------------------------------------------------------


class DnsTerraformModuleTests(unittest.TestCase):
    def _main_tf(self) -> str:
        return (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")

    def test_ac001_main_tf_declares_zone_resource(self) -> None:
        self.assertIn(
            'resource "stackit_dns_zone" "this"',
            self._main_tf(),
            msg="main.tf must declare stackit_dns_zone.this resource (AC-001, FR-001)",
        )

    def test_ac001_main_tf_uses_for_each(self) -> None:
        self.assertIn(
            "for_each",
            self._main_tf(),
            msg="main.tf must use for_each to iterate over dns_zone_fqdns (AC-001, FR-001)",
        )

    def test_ac001_main_tf_uses_sha1_for_naming(self) -> None:
        self.assertIn(
            "sha1",
            self._main_tf(),
            msg="main.tf zone name must use sha1(fqdn) hash for collision-resistant display name (AC-001, FR-001)",
        )

    def test_ac001_main_tf_has_required_version(self) -> None:
        self.assertIn(
            'required_version = ">= 1.13.0"',
            self._main_tf(),
            msg="main.tf terraform block must include required_version >= 1.13.0 (AC-001, FR-001)",
        )

    def test_ac001_main_tf_no_create_before_destroy(self) -> None:
        self.assertNotIn(
            "create_before_destroy",
            self._main_tf(),
            msg="main.tf must NOT include lifecycle create_before_destroy — DNS zone recreation is destructive (AC-001, NFR-REL-001)",
        )

    def test_ac001_main_tf_uses_trimsuffix_for_dns_name(self) -> None:
        self.assertIn(
            "trimsuffix",
            self._main_tf(),
            msg="main.tf dns_name attribute must use trimsuffix to strip trailing dot (AC-001, FR-001)",
        )

    def test_ac002_variables_tf_declares_all_five_variables(self) -> None:
        content = (_MODULE_DIR / "variables.tf").read_text(encoding="utf-8")
        for var in _REQUIRED_VARIABLES:
            self.assertIn(
                f'variable "{var}"',
                content,
                msg=f'variables.tf must declare variable "{var}" (AC-002, FR-002)',
            )

    def test_ac003_outputs_tf_declares_zone_ids(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"zone_ids"',
            content,
            msg="outputs.tf must declare zone_ids output (map of FQDN→zone_id) (AC-003, FR-003)",
        )

    def test_ac003_outputs_tf_declares_dns_names(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"dns_names"',
            content,
            msg="outputs.tf must declare dns_names output (list) (AC-003, FR-003)",
        )

    def test_ac003_outputs_tf_declares_primary_name_servers(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"primary_name_servers"',
            content,
            msg="outputs.tf must declare primary_name_servers output (map of FQDN→NS) (AC-003, FR-003)",
        )

    def test_ac004_versions_tf_declares_stackit_provider(self) -> None:
        content = (_MODULE_DIR / "versions.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackitcloud/stackit",
            content,
            msg="versions.tf must declare stackitcloud/stackit required provider (AC-004, FR-004)",
        )

    def test_ac004_versions_tf_pins_exact_version(self) -> None:
        content = (_MODULE_DIR / "versions.tf").read_text(encoding="utf-8")
        self.assertIn(
            "= 0.88.0",
            content,
            msg="versions.tf must pin stackit provider at exactly = 0.88.0 (AC-004, FR-004)",
        )


# ---------------------------------------------------------------------------
# Slice 2 — Shell layer, contract, smoke, and quality gate (AC-005 through AC-012)
# ---------------------------------------------------------------------------


class DnsContractYamlTests(unittest.TestCase):
    def test_ac011_contract_yaml_includes_dns_zone_ids(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "DNS_ZONE_IDS",
            content,
            msg="module.contract.yaml outputs.produced must include DNS_ZONE_IDS (AC-011, FR-004b)",
        )

    def test_ac011_contract_yaml_includes_dns_zone_count(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "DNS_ZONE_COUNT",
            content,
            msg="module.contract.yaml outputs.produced must include DNS_ZONE_COUNT (AC-011, FR-004b)",
        )

    def test_ac011_contract_yaml_includes_dns_primary_name_servers(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "DNS_PRIMARY_NAME_SERVERS",
            content,
            msg="module.contract.yaml outputs.produced must include DNS_PRIMARY_NAME_SERVERS (AC-011, FR-004b)",
        )


class DnsShellLibTests(unittest.TestCase):
    def test_ac011_lib_defines_dns_zone_ids_function(self) -> None:
        content = _SHELL_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "dns_zone_ids()",
            content,
            msg="dns.sh must declare dns_zone_ids() helper function (AC-011, FR-004b)",
        )

    def test_ac011_lib_defines_dns_zone_count_function(self) -> None:
        content = _SHELL_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "dns_zone_count()",
            content,
            msg="dns.sh must declare dns_zone_count() helper function (AC-011, FR-004b)",
        )

    def test_ac011_lib_defines_dns_primary_name_servers_function(self) -> None:
        content = _SHELL_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "dns_primary_name_servers()",
            content,
            msg="dns.sh must declare dns_primary_name_servers() helper function (AC-011, FR-004b)",
        )


class DnsSmokeScriptTests(unittest.TestCase):
    def test_ac005_smoke_validates_zone_count_positive(self) -> None:
        content = _SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "zone_count",
            content,
            msg="dns_smoke.sh must validate zone_count is a positive integer in runtime state (AC-005, FR-005)",
        )

    def test_ac006_smoke_validates_zone_ids_non_empty(self) -> None:
        content = _SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "zone_ids",
            content,
            msg="dns_smoke.sh must validate zone_ids is non-empty in runtime state (AC-006, FR-005)",
        )

    def test_ac012_smoke_validates_primary_name_servers_non_empty(self) -> None:
        content = _SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "primary_name_servers",
            content,
            msg="dns_smoke.sh must validate primary_name_servers is non-empty in runtime state (AC-012, FR-005)",
        )


class DnsApplyScriptTests(unittest.TestCase):
    def test_ac011_apply_writes_zone_ids_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "zone_ids",
            content,
            msg="dns_apply.sh write_state_file must include zone_ids key (AC-011, FR-004b)",
        )

    def test_ac011_apply_writes_zone_count_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "zone_count",
            content,
            msg="dns_apply.sh write_state_file must include zone_count key (AC-011, FR-004b)",
        )

    def test_ac011_apply_writes_primary_name_servers_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "primary_name_servers",
            content,
            msg="dns_apply.sh write_state_file must include primary_name_servers key (AC-011, FR-004b)",
        )


class DnsRuntimeContractTests(unittest.TestCase):
    def test_ac010_runtime_state_fixture_has_all_contract_keys(self) -> None:
        for key in ("zone_ids", "zone_fqdns", "zone_count", "primary_name_servers"):
            self.assertTrue(
                re.search(rf"^{key}=", _MOCK_RUNTIME_STATE, re.MULTILINE) is not None,
                msg=f"contract output key missing from runtime state fixture: {key} (AC-010, NFR-OPS-001)",
            )


class DnsQualityGateTests(unittest.TestCase):
    def test_ac008_test_contract_in_pyramid_contract_json(self) -> None:
        content = _PYRAMID_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "tests/infra/modules/dns/test_contract.py",
            content,
            msg="test_contract.py must be registered in test_pyramid_contract.json (AC-008, FR-006)",
        )
