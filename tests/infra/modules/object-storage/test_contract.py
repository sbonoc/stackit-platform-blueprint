from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT, run

_CONTRACT_OUTPUTS = (
    "endpoint",
    "bucket",
    "access_key",
    "secret_key",
    "region",
)

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=helm",
        "provision_path=/artifacts/infra/rendered/object-storage.values.yaml",
        "endpoint=http://blueprint-object-storage.data.svc.cluster.local:9000",
        "bucket=marketplace-assets",
        "access_key=minioadmin",
        "secret_key=minioadmin123",
        "region=eu01",
        "timestamp_utc=2026-05-06T00:00:00Z",
    ]
)


class ObjectStorageRuntimeContractTests(unittest.TestCase):
    def test_object_storage_runtime_state_has_all_contract_outputs(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False, encoding="utf-8"
        ) as f:
            f.write(_MOCK_RUNTIME_ENV_LOCAL)
            tmp_path = Path(f.name)

        try:
            content = tmp_path.read_text(encoding="utf-8")
            for key in _CONTRACT_OUTPUTS:
                self.assertTrue(
                    re.search(rf"^{key}=", content, re.MULTILINE) is not None,
                    msg=f"contract output missing in object_storage_runtime state: {key}",
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_object_storage_runtime_state_endpoint_is_http_in_local_profile(self) -> None:
        self.assertIn("endpoint=http://", _MOCK_RUNTIME_ENV_LOCAL)

    def test_object_storage_runtime_state_bucket_is_non_empty(self) -> None:
        line = next(
            l for l in _MOCK_RUNTIME_ENV_LOCAL.splitlines() if l.startswith("bucket=")
        )
        self.assertNotEqual(line, "bucket=", msg="bucket must be non-empty in local profile")

    def test_object_storage_runtime_state_region_is_non_empty(self) -> None:
        self.assertIn("region=", _MOCK_RUNTIME_ENV_LOCAL)
        line = next(
            l for l in _MOCK_RUNTIME_ENV_LOCAL.splitlines() if l.startswith("region=")
        )
        self.assertNotEqual(line, "region=", msg="region must be non-empty")
