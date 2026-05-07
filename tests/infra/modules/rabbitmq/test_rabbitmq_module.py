from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "rabbitmq"
_FOUNDATION_OUTPUTS = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation" / "outputs.tf"
_RABBITMQ_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "rabbitmq.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "rabbitmq_apply.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "rabbitmq_smoke.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"

_SMOKE_ENV = {
    "BLUEPRINT_PROFILE": "local-full",
    "RABBITMQ_ENABLED": "true",
    "RABBITMQ_INSTANCE_NAME": "marketplace-rabbitmq",
}


class RabbitmqTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_has_rabbitmq_resources(self) -> None:
        content = (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn("stackit_rabbitmq_instance", content)
        self.assertIn("stackit_rabbitmq_credential", content)
        self.assertIn("create_before_destroy", content)

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        content = (_MODULE_DIR / "variables.tf").read_text(encoding="utf-8")
        for var in (
            "stackit_project_id",
            "stackit_region",
            "rabbitmq_instance_name",
            "rabbitmq_version",
            "rabbitmq_plan_name",
        ):
            self.assertIn(var, content, msg=f"missing variable: {var}")

    def test_terraform_module_outputs_expose_contract_keys(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        for key in (
            "rabbitmq_host",
            "rabbitmq_port",
            "rabbitmq_username",
            "rabbitmq_password",
            "rabbitmq_uri",
            "rabbitmq_management_url",
        ):
            self.assertIn(key, content, msg=f"missing output: {key}")

    def test_terraform_module_versions_tf_exists_with_provider_constraint(self) -> None:
        content = (_MODULE_DIR / "versions.tf").read_text(encoding="utf-8")
        self.assertIn("stackitcloud/stackit", content)
        self.assertIn("required_providers", content)


class RabbitmqFoundationOutputsTests(unittest.TestCase):
    def test_foundation_outputs_expose_rabbitmq_management_url(self) -> None:
        content = _FOUNDATION_OUTPUTS.read_text(encoding="utf-8")
        self.assertIn(
            "rabbitmq_management_url",
            content,
            msg="foundation outputs.tf must expose rabbitmq_management_url so shell layer can read it",
        )

    def test_foundation_rabbitmq_management_url_reads_management_attribute(self) -> None:
        content = _FOUNDATION_OUTPUTS.read_text(encoding="utf-8")
        self.assertIn(
            ".management",
            content,
            msg="rabbitmq_management_url must read the .management attribute from stackit_rabbitmq_credential",
        )


class RabbitmqLibraryFunctionPresenceTests(unittest.TestCase):
    def test_lib_defines_vhost_function(self) -> None:
        content = _RABBITMQ_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "rabbitmq_vhost()",
            content,
            msg="rabbitmq.sh must define rabbitmq_vhost()",
        )

    def test_lib_defines_management_url_function(self) -> None:
        content = _RABBITMQ_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "rabbitmq_management_url()",
            content,
            msg="rabbitmq.sh must define rabbitmq_management_url()",
        )

    def test_vhost_returns_constant_slash(self) -> None:
        content = _RABBITMQ_LIB.read_text(encoding="utf-8")
        fn_start = content.find("rabbitmq_vhost()")
        fn_body = content[fn_start : fn_start + 200]
        self.assertIn(
            "/",
            fn_body,
            msg="rabbitmq_vhost() must return the constant '/' (RabbitMQ default vhost)",
        )

    def test_management_url_local_lane_uses_port_15672(self) -> None:
        content = _RABBITMQ_LIB.read_text(encoding="utf-8")
        fn_start = content.find("rabbitmq_management_url()")
        fn_body = content[fn_start : fn_start + 400]
        self.assertIn(
            "15672",
            fn_body,
            msg="rabbitmq_management_url() must use port 15672 for local lane (Bitnami management plugin default)",
        )

    def test_management_url_stackit_lane_reads_foundation_output(self) -> None:
        content = _RABBITMQ_LIB.read_text(encoding="utf-8")
        fn_start = content.find("rabbitmq_management_url()")
        fn_body = content[fn_start : fn_start + 400]
        self.assertIn(
            "rabbitmq_management_url",
            fn_body[len("rabbitmq_management_url()") :],
            msg="rabbitmq_management_url() must call stackit_foundation_output_value_or_default with rabbitmq_management_url key",
        )


class RabbitmqApplyScriptTests(unittest.TestCase):
    def test_apply_state_file_write_includes_vhost(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "vhost=",
            content,
            msg="rabbitmq_apply.sh must write vhost= to the runtime state file",
        )

    def test_apply_state_file_write_includes_management_url(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "management_url=",
            content,
            msg="rabbitmq_apply.sh must write management_url= to the runtime state file",
        )


class RabbitmqSmokeScriptTests(unittest.TestCase):
    def _run_smoke(self, state_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "rabbitmq_runtime.env"
        backup = runtime_env.read_bytes() if runtime_env.exists() else None
        runtime_env.write_text(state_content, encoding="utf-8")
        try:
            result = run(["bash", str(_SMOKE_SH)], _SMOKE_ENV)
            return result.returncode
        finally:
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def test_smoke_passes_with_valid_state(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-rabbitmq.messaging.svc.cluster.local\n"
            "port=5672\n"
            "username=marketplace\n"
            "password=marketplace-password\n"
            "uri=amqp://marketplace:marketplace-password@blueprint-rabbitmq.messaging.svc.cluster.local:5672\n"
            "vhost=/\n"
            "management_url=http://blueprint-rabbitmq.messaging.svc.cluster.local:15672\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with valid state containing all seven contract keys")

    def test_smoke_fails_when_uri_invalid(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-rabbitmq.messaging.svc.cluster.local\n"
            "port=5672\n"
            "username=marketplace\n"
            "password=marketplace-password\n"
            "uri=invalid://not-amqp\n"
            "vhost=/\n"
            "management_url=http://blueprint-rabbitmq.messaging.svc.cluster.local:15672\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when uri does not start with amqp:// or amqps://")

    def test_smoke_fails_when_host_empty(self) -> None:
        rc = self._run_smoke(
            "host=\n"
            "port=5672\n"
            "username=marketplace\n"
            "password=marketplace-password\n"
            "uri=amqp://marketplace:marketplace-password@:5672\n"
            "vhost=/\n"
            "management_url=http://blueprint-rabbitmq.messaging.svc.cluster.local:15672\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when host is empty")

    def test_smoke_fails_when_vhost_empty(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-rabbitmq.messaging.svc.cluster.local\n"
            "port=5672\n"
            "username=marketplace\n"
            "password=marketplace-password\n"
            "uri=amqp://marketplace:marketplace-password@blueprint-rabbitmq.messaging.svc.cluster.local:5672\n"
            "vhost=\n"
            "management_url=http://blueprint-rabbitmq.messaging.svc.cluster.local:15672\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when vhost is empty")

    def test_smoke_fails_when_management_url_empty(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-rabbitmq.messaging.svc.cluster.local\n"
            "port=5672\n"
            "username=marketplace\n"
            "password=marketplace-password\n"
            "uri=amqp://marketplace:marketplace-password@blueprint-rabbitmq.messaging.svc.cluster.local:5672\n"
            "vhost=/\n"
            "management_url=\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when management_url is empty")
