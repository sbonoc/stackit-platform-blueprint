from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT, run

_CONTRACT_OUTPUTS = (
    "host",
    "hosts",
    "port",
    "scheme",
    "uri",
    "dashboard_url",
    "username",
    "password",
)

_MOCK_RUNTIME_ENV = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=helm",
        "provision_path=/artifacts/infra/rendered/opensearch.values.yaml",
        "host=blueprint-opensearch.search.svc.cluster.local",
        "hosts=blueprint-opensearch.search.svc.cluster.local",
        "port=9200",
        "scheme=http",
        "uri=http://blueprint-opensearch.search.svc.cluster.local:9200",
        "dashboard_url=http://blueprint-opensearch.search.svc.cluster.local:5601",
        "username=admin",
        "password=admin",
        "timestamp_utc=2026-05-06T00:00:00Z",
    ]
)


class OpenSearchRuntimeContractTests(unittest.TestCase):
    def test_opensearch_runtime_state_has_all_contract_outputs(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False, encoding="utf-8"
        ) as f:
            f.write(_MOCK_RUNTIME_ENV)
            tmp_path = Path(f.name)

        try:
            content = tmp_path.read_text(encoding="utf-8")
            for key in _CONTRACT_OUTPUTS:
                self.assertTrue(
                    re.search(rf"^{key}=", content, re.MULTILINE) is not None,
                    msg=f"contract output missing in opensearch_runtime state: {key}",
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_opensearch_runtime_state_uri_is_http_in_local_profile(self) -> None:
        self.assertIn("uri=http://", _MOCK_RUNTIME_ENV)

    def test_opensearch_runtime_state_port_is_9200_in_local_profile(self) -> None:
        self.assertIn("port=9200", _MOCK_RUNTIME_ENV)

    def test_opensearch_runtime_state_scheme_is_http_in_local_profile(self) -> None:
        self.assertIn("scheme=http", _MOCK_RUNTIME_ENV)
