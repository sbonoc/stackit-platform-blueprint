from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_CONTRACT_OUTPUTS = (
    "host",
    "port",
    "db_name",
    "user",
    "password",
    "dsn",
)

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=helm",
        "provision_path=/artifacts/infra/rendered/postgres.values.yaml",
        "host=blueprint-postgres.data.svc.cluster.local",
        "port=5432",
        "db_name=platform",
        "user=platform",
        "password=platform-password",
        "dsn=postgresql://platform:platform-password@blueprint-postgres.data.svc.cluster.local:5432/platform",
        "timestamp_utc=2026-05-07T00:00:00Z",
    ]
)


class PostgresRuntimeContractTests(unittest.TestCase):
    def test_postgres_runtime_state_has_all_contract_outputs(self) -> None:
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
                    msg=f"contract output missing in postgres_runtime state: {key}",
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_postgres_runtime_state_dsn_has_postgresql_scheme(self) -> None:
        self.assertIn("dsn=postgresql://", _MOCK_RUNTIME_ENV_LOCAL)
