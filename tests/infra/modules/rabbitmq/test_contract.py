from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "rabbitmq" / "module.contract.yaml"

_CONTRACT_OUTPUTS = (
    "host",
    "port",
    "username",
    "password",
    "uri",
    "vhost",
    "management_url",
)

_MOCK_RUNTIME_ENV_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=helm",
        "provision_path=/artifacts/infra/rendered/rabbitmq.values.yaml",
        "host=blueprint-rabbitmq.messaging.svc.cluster.local",
        "port=5672",
        "username=marketplace",
        "password=marketplace-password",
        "uri=amqp://marketplace:marketplace-password@blueprint-rabbitmq.messaging.svc.cluster.local:5672",
        "vhost=/",
        "management_url=http://blueprint-rabbitmq.messaging.svc.cluster.local:15672",
        "timestamp_utc=2026-05-07T00:00:00Z",
    ]
)


class RabbitmqContractYamlTests(unittest.TestCase):
    def test_contract_yaml_outputs_include_rabbitmq_vhost(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "RABBITMQ_VHOST",
            content,
            msg="module.contract.yaml outputs.produced must include RABBITMQ_VHOST",
        )

    def test_contract_yaml_outputs_include_rabbitmq_management_url(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "RABBITMQ_MANAGEMENT_URL",
            content,
            msg="module.contract.yaml outputs.produced must include RABBITMQ_MANAGEMENT_URL",
        )


class RabbitmqRuntimeContractTests(unittest.TestCase):
    def test_rabbitmq_runtime_state_has_all_contract_outputs(self) -> None:
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
                    msg=f"contract output missing in rabbitmq_runtime state: {key}",
                )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_rabbitmq_runtime_state_uri_has_amqp_scheme(self) -> None:
        self.assertIn("uri=amqp://", _MOCK_RUNTIME_ENV_LOCAL)
