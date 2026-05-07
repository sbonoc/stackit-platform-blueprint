from __future__ import annotations

import re
import unittest

from tests._shared.helpers import REPO_ROOT

_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "kms" / "module.contract.yaml"

_CONTRACT_STATE_KEYS = (
    "key_ring_id",
    "key_id",
    "key_ring_name",
    "key_name",
    "endpoint",
)

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=helm",
        "provision_path=/artifacts/infra/rendered/kms.values.yaml",
        "key_ring_id=kms://marketplace-ring",
        "key_id=kms://marketplace-ring/marketplace-key",
        "key_ring_name=marketplace-ring",
        "key_name=marketplace-key",
        "endpoint=http://blueprint-vault.kms.svc.cluster.local:8200/v1/transit",
        "timestamp_utc=2026-05-07T00:00:00Z",
    ]
)


class KmsContractYamlTests(unittest.TestCase):
    def test_contract_yaml_outputs_include_kms_endpoint(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "KMS_ENDPOINT",
            content,
            msg="module.contract.yaml outputs.produced must include KMS_ENDPOINT (AC-004, FR-002)",
        )


class KmsRuntimeContractTests(unittest.TestCase):
    def test_runtime_state_has_all_five_contract_output_keys(self) -> None:
        for key in _CONTRACT_STATE_KEYS:
            self.assertTrue(
                re.search(rf"^{key}=", _MOCK_RUNTIME_ENV_LOCAL, re.MULTILINE) is not None,
                msg=f"contract output key missing from kms_runtime state fixture: {key} (AC-011)",
            )
