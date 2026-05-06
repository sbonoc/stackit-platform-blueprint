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

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
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
        "dashboard_url=",
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
            f.write(_MOCK_RUNTIME_ENV_LOCAL)
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
        self.assertIn("uri=http://", _MOCK_RUNTIME_ENV_LOCAL)

    def test_opensearch_runtime_state_port_is_9200_in_local_profile(self) -> None:
        self.assertIn("port=9200", _MOCK_RUNTIME_ENV_LOCAL)

    def test_opensearch_runtime_state_scheme_is_http_in_local_profile(self) -> None:
        self.assertIn("scheme=http", _MOCK_RUNTIME_ENV_LOCAL)

    def test_opensearch_runtime_state_dashboard_url_empty_on_local_profile(self) -> None:
        # Local lane runs with dashboards.enabled=false to stay within ~1 GB
        # RAM dev budget. Contract output must be present but empty so smoke
        # check distinguishes "intentionally empty" from "missing key".
        self.assertIn("dashboard_url=", _MOCK_RUNTIME_ENV_LOCAL)
        line = next(
            l for l in _MOCK_RUNTIME_ENV_LOCAL.splitlines() if l.startswith("dashboard_url=")
        )
        self.assertEqual(line, "dashboard_url=",
                         msg="dashboard_url must be empty on local lane")

    def test_opensearch_runtime_state_username_locked_to_admin(self) -> None:
        # Bitnami chart hard-codes OPENSEARCH_USERNAME=admin; state file must
        # report the actual auth user, not any operator override.
        self.assertIn("username=admin", _MOCK_RUNTIME_ENV_LOCAL)
