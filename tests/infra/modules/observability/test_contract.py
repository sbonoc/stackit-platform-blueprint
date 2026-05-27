from __future__ import annotations

import re
import unittest

from tests._shared.helpers import REPO_ROOT

_FOUNDATION_OUTPUTS = (
    REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "foundation" / "outputs.tf"
)
_BOOTSTRAP_OUTPUTS = (
    REPO_ROOT
    / "scripts"
    / "templates"
    / "infra"
    / "bootstrap"
    / "infra"
    / "cloud"
    / "stackit"
    / "terraform"
    / "foundation"
    / "outputs.tf"
)
_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "observability" / "module.contract.yaml"
_SHELL_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "observability.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "observability_apply.sh"
_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "observability_destroy.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "observability_smoke.sh"
_ARGOCD_DEV = REPO_ROOT / "infra" / "gitops" / "argocd" / "optional" / "dev" / "observability.yaml"
_ARGOCD_STAGE = (
    REPO_ROOT / "infra" / "gitops" / "argocd" / "optional" / "stage" / "observability.yaml"
)
_ARGOCD_PROD = (
    REPO_ROOT / "infra" / "gitops" / "argocd" / "optional" / "prod" / "observability.yaml"
)
_OTC_VALUES = (
    REPO_ROOT / "infra" / "cloud" / "stackit" / "helm" / "observability" / "otel-collector.values.yaml"
)
_PYRAMID_CONTRACT = REPO_ROOT / "scripts" / "lib" / "quality" / "test_pyramid_contract.json"
_LOCAL_OTC_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "observability" / "otel-collector.values.yaml"
_DASHBOARDS_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "observability_dashboards_apply.sh"
_DASHBOARDS_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "observability_dashboards_destroy.sh"
_SEED_DASHBOARD = REPO_ROOT / "infra" / "observability" / "dashboards" / "golden-signals.json"
_BOOTSTRAP_SEED_DASHBOARD = REPO_ROOT / "scripts" / "templates" / "blueprint" / "bootstrap" / "infra" / "observability" / "dashboards" / "golden-signals.json"
_MAKEFILE_TEMPLATE = REPO_ROOT / "scripts" / "templates" / "blueprint" / "bootstrap" / "make" / "blueprint.generated.mk.tmpl"

_MOCK_RUNTIME_STATE_STACKIT = "\n".join(
    [
        "profile=stackit-dev",
        "stack=stackit",
        "tooling_mode=live",
        "provision_driver=foundation_contract",
        "otel_endpoint=http://otel-collector.observability.svc.cluster.local:4317",
        "otel_protocol=grpc",
        "otel_traces_enabled=true",
        "otel_metrics_enabled=true",
        "otel_logs_enabled=true",
        "faro_enabled=true",
        "faro_collect_path=/collect",
        "faro_endpoint=http://otel-collector.observability.svc.cluster.local:12347/collect",
        "logs_endpoint=https://logs.eu01.logs.onstackit.cloud/loki/api/v1/push",
        "metrics_endpoint=https://metrics.eu01.metrics.onstackit.cloud/api/v1/push",
        "traces_endpoint=https://traces.eu01.traces.onstackit.cloud",
        "api_key=",
        "stackit_observability_instance_id=obs-12345",
        "stackit_observability_grafana_url=https://grafana.eu01.stackit.cloud",
        "health_status=Provisioned",
        "timestamp_utc=2026-05-19T00:00:00Z",
    ]
)

_MOCK_RUNTIME_STATE_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "provision_driver=crossplane_plus_helm",
        "otel_endpoint=http://otel-collector.observability.svc.cluster.local:4317",
        "otel_protocol=grpc",
        "otel_traces_enabled=true",
        "otel_metrics_enabled=true",
        "otel_logs_enabled=true",
        "faro_enabled=true",
        "faro_collect_path=/collect",
        "faro_endpoint=http://otel-collector.observability.svc.cluster.local:12347/collect",
        "logs_endpoint=",
        "metrics_endpoint=",
        "traces_endpoint=",
        "api_key=",
        "stackit_observability_instance_id=stackit-observability-local",
        "stackit_observability_grafana_url=https://grafana.local.stackit.example.invalid",
        "health_status=Provisioned",
        "timestamp_utc=2026-05-19T00:00:00Z",
    ]
)


class FoundationOutputsTests(unittest.TestCase):
    """FR-001, T-104 — foundation outputs.tf exposes the three push URL attributes."""

    def _outputs(self) -> str:
        return _FOUNDATION_OUTPUTS.read_text(encoding="utf-8")

    def test_foundation_outputs_metrics_push_url(self) -> None:
        self.assertIn(
            '"observability_metrics_push_url"',
            self._outputs(),
            msg="foundation outputs.tf must declare observability_metrics_push_url (FR-001, T-104)",
        )

    def test_foundation_outputs_logs_push_url(self) -> None:
        self.assertIn(
            '"observability_logs_push_url"',
            self._outputs(),
            msg="foundation outputs.tf must declare observability_logs_push_url (FR-001, T-104)",
        )

    def test_foundation_outputs_traces_push_url(self) -> None:
        self.assertIn(
            '"observability_traces_push_url"',
            self._outputs(),
            msg="foundation outputs.tf must declare observability_traces_push_url (FR-001, T-104)",
        )

    def test_foundation_outputs_metrics_push_url_not_sensitive(self) -> None:
        content = self._outputs()
        block_start = content.find('"observability_metrics_push_url"')
        block_end = content.find("\n}", block_start)
        block = content[block_start:block_end]
        self.assertNotIn(
            "sensitive",
            block,
            msg="observability_metrics_push_url must NOT be marked sensitive — push URLs contain no credential material (FR-001, NFR-OPS-001)",
        )

    def test_bootstrap_template_outputs_metrics_push_url(self) -> None:
        self.assertIn(
            '"observability_metrics_push_url"',
            _BOOTSTRAP_OUTPUTS.read_text(encoding="utf-8"),
            msg="bootstrap template outputs.tf must also declare observability_metrics_push_url (FR-001)",
        )


class ObservabilityShellLibTests(unittest.TestCase):
    """FR-002, FR-003, FR-004 — helper functions exist in observability.sh."""

    def _lib(self) -> str:
        return _SHELL_LIB.read_text(encoding="utf-8")

    def test_metrics_push_url_function_exists(self) -> None:
        self.assertIn(
            "observability_metrics_push_url()",
            self._lib(),
            msg="observability.sh must declare observability_metrics_push_url() (FR-002)",
        )

    def test_logs_push_url_function_exists(self) -> None:
        self.assertIn(
            "observability_logs_push_url()",
            self._lib(),
            msg="observability.sh must declare observability_logs_push_url() (FR-002)",
        )

    def test_traces_push_url_function_exists(self) -> None:
        self.assertIn(
            "observability_traces_push_url()",
            self._lib(),
            msg="observability.sh must declare observability_traces_push_url() (FR-002)",
        )

    def test_api_key_function_exists(self) -> None:
        self.assertIn(
            "observability_api_key()",
            self._lib(),
            msg="observability.sh must declare observability_api_key() (FR-003)",
        )

    def test_reconcile_runtime_secret_function_exists(self) -> None:
        self.assertIn(
            "observability_reconcile_runtime_secret()",
            self._lib(),
            msg="observability.sh must declare observability_reconcile_runtime_secret() (FR-004)",
        )

    def test_delete_runtime_secret_function_exists(self) -> None:
        self.assertIn(
            "observability_delete_runtime_secret()",
            self._lib(),
            msg="observability.sh must declare observability_delete_runtime_secret() (FR-004)",
        )

    def test_reconcile_targets_blueprint_observability_auth(self) -> None:
        self.assertIn(
            "blueprint-observability-auth",
            self._lib(),
            msg="observability_reconcile_runtime_secret() must operate on blueprint-observability-auth secret (FR-004, NFR-SEC-001)",
        )

    def test_reconcile_username_sourced_from_tf_output(self) -> None:
        self.assertIn(
            "observability_credential_username",
            self._lib(),
            msg="observability_reconcile_runtime_secret() must source username from TF foundation output observability_credential_username, not bare OBSERVABILITY_USERNAME env var (FR-004, Claude review finding)",
        )


class ApplyScriptTests(unittest.TestCase):
    """FR-005, AC-001 — apply script writes new state keys and reconciles secret."""

    def _apply(self) -> str:
        return _APPLY_SCRIPT.read_text(encoding="utf-8")

    def test_apply_calls_reconcile_runtime_secret(self) -> None:
        self.assertIn(
            "observability_reconcile_runtime_secret",
            self._apply(),
            msg="observability_apply.sh must call observability_reconcile_runtime_secret() in foundation_contract case (FR-005)",
        )

    def test_apply_writes_logs_endpoint_to_state(self) -> None:
        self.assertIn(
            "logs_endpoint",
            self._apply(),
            msg="observability_apply.sh must write logs_endpoint key to state file (FR-005, AC-001)",
        )

    def test_apply_writes_metrics_endpoint_to_state(self) -> None:
        self.assertIn(
            "metrics_endpoint",
            self._apply(),
            msg="observability_apply.sh must write metrics_endpoint key to state file (FR-005, AC-001)",
        )

    def test_apply_writes_traces_endpoint_to_state(self) -> None:
        self.assertIn(
            "traces_endpoint",
            self._apply(),
            msg="observability_apply.sh must write traces_endpoint key to state file (FR-005, AC-001)",
        )

    def test_apply_writes_api_key_to_state(self) -> None:
        self.assertIn(
            "api_key",
            self._apply(),
            msg="observability_apply.sh must write api_key key to state file (FR-005, AC-001)",
        )

    def test_apply_writes_faro_endpoint_to_state(self) -> None:
        self.assertIn(
            "faro_endpoint",
            self._apply(),
            msg="observability_apply.sh must write faro_endpoint key to state file (FR-007)",
        )


class DestroyScriptTests(unittest.TestCase):
    """FR-006, AC-008 — destroy script deletes runtime secret and ArgoCD Application."""

    def test_destroy_calls_delete_runtime_secret(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "observability_delete_runtime_secret",
            content,
            msg="observability_destroy.sh must call observability_delete_runtime_secret() in foundation_reconcile_apply case (FR-006, AC-008)",
        )

    def test_destroy_deletes_argocd_manifest(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "run_manifest_delete",
            content,
            msg="observability_destroy.sh must call run_manifest_delete to remove the ArgoCD Application before Secret deletion (FR-006, Codex P1 finding)",
        )


class SmokeScriptTests(unittest.TestCase):
    """FR-009, AC-003 — smoke script validates new state keys on STACKIT lane."""

    def _smoke(self) -> str:
        return _SMOKE_SCRIPT.read_text(encoding="utf-8")

    def test_smoke_validates_logs_endpoint(self) -> None:
        self.assertIn(
            "logs_endpoint",
            self._smoke(),
            msg="observability_smoke.sh must check logs_endpoint on STACKIT lane (FR-009, AC-003)",
        )

    def test_smoke_validates_metrics_endpoint(self) -> None:
        self.assertIn(
            "metrics_endpoint",
            self._smoke(),
            msg="observability_smoke.sh must check metrics_endpoint on STACKIT lane (FR-009, AC-003)",
        )

    def test_smoke_validates_traces_endpoint(self) -> None:
        self.assertIn(
            "traces_endpoint",
            self._smoke(),
            msg="observability_smoke.sh must check traces_endpoint on STACKIT lane (FR-009, AC-003)",
        )

    def test_smoke_validates_api_key_presence(self) -> None:
        self.assertIn(
            "api_key=",
            self._smoke(),
            msg="observability_smoke.sh must check api_key key presence on STACKIT lane (FR-009, Claude review finding)",
        )

    def test_smoke_validates_faro_endpoint(self) -> None:
        self.assertIn(
            "faro_endpoint",
            self._smoke(),
            msg="observability_smoke.sh must check faro_endpoint is non-empty and starts with http (FR-008)",
        )


class ArgoCDManifestTests(unittest.TestCase):
    """FR-008, AC-005, NFR-REL-001 — ArgoCD Application resource present in all environments."""

    def test_argocd_dev_has_application_kind(self) -> None:
        self.assertIn(
            "kind: Application",
            _ARGOCD_DEV.read_text(encoding="utf-8"),
            msg="dev/observability.yaml must contain an ArgoCD Application resource (FR-008, AC-005)",
        )

    def test_argocd_stage_has_application_kind(self) -> None:
        self.assertIn(
            "kind: Application",
            _ARGOCD_STAGE.read_text(encoding="utf-8"),
            msg="stage/observability.yaml must contain an ArgoCD Application resource (FR-008, AC-005)",
        )

    def test_argocd_prod_has_application_kind(self) -> None:
        self.assertIn(
            "kind: Application",
            _ARGOCD_PROD.read_text(encoding="utf-8"),
            msg="prod/observability.yaml must contain an ArgoCD Application resource (FR-008, AC-005)",
        )

    def test_argocd_dev_self_heal_enabled(self) -> None:
        self.assertIn(
            "selfHeal: true",
            _ARGOCD_DEV.read_text(encoding="utf-8"),
            msg="dev/observability.yaml Application must set selfHeal: true (NFR-REL-001)",
        )


class OtelCollectorValuesTests(unittest.TestCase):
    """FR-007, AC-006 — otel-collector.values.yaml declares all three exporter types."""

    def _values(self) -> str:
        return _OTC_VALUES.read_text(encoding="utf-8")

    def test_values_has_prometheusremotewrite_exporter(self) -> None:
        self.assertIn(
            "prometheusremotewrite",
            self._values(),
            msg="otel-collector.values.yaml must declare prometheusremotewrite exporter (FR-007, AC-006)",
        )

    def test_values_has_loki_exporter(self) -> None:
        self.assertIn(
            "loki",
            self._values(),
            msg="otel-collector.values.yaml must declare loki exporter (FR-007, AC-006)",
        )

    def test_values_has_otlp_stackit_exporter(self) -> None:
        self.assertIn(
            "otlp/stackit",
            self._values(),
            msg="otel-collector.values.yaml must declare otlp/stackit exporter (FR-007, AC-006)",
        )

    def test_values_uses_projected_volume_mount(self) -> None:
        values = self._values()
        self.assertNotIn(
            "extraEnvFrom",
            values,
            msg="otel-collector.values.yaml must NOT use extraEnvFrom — credentials injected via projected volume mount (NFR-SEC-001)",
        )
        self.assertIn(
            "extraVolumes",
            values,
            msg="otel-collector.values.yaml must declare extraVolumes for blueprint-observability-auth Secret mount (FR-007, NFR-SEC-001)",
        )
        self.assertIn(
            "/etc/otel/secrets",
            values,
            msg="otel-collector.values.yaml must mount Secret at /etc/otel/secrets (FR-007, NFR-SEC-001)",
        )

    def test_values_uses_file_provider_for_credentials(self) -> None:
        self.assertIn(
            "${file:/etc/otel/secrets/",
            self._values(),
            msg="otel-collector.values.yaml must reference credentials via OTC file config provider, not env vars (NFR-SEC-001)",
        )

    def test_values_has_spanmetrics_connector(self) -> None:
        self.assertIn(
            "spanmetrics",
            self._values(),
            msg="otel-collector.values.yaml must declare spanmetrics connector for auto-derived span metrics from traces",
        )


class ContractYamlTests(unittest.TestCase):
    """FR-010, AC-010 — module.contract.yaml outputs.produced includes new output keys."""

    def _contract(self) -> str:
        return _CONTRACT_FILE.read_text(encoding="utf-8")

    def test_contract_includes_logs_endpoint_output(self) -> None:
        self.assertIn(
            "OBSERVABILITY_LOGS_ENDPOINT",
            self._contract(),
            msg="module.contract.yaml outputs.produced must include OBSERVABILITY_LOGS_ENDPOINT (FR-010, AC-010)",
        )

    def test_contract_includes_metrics_endpoint_output(self) -> None:
        self.assertIn(
            "OBSERVABILITY_METRICS_ENDPOINT",
            self._contract(),
            msg="module.contract.yaml outputs.produced must include OBSERVABILITY_METRICS_ENDPOINT (FR-010, AC-010)",
        )

    def test_contract_includes_traces_endpoint_output(self) -> None:
        self.assertIn(
            "OBSERVABILITY_TRACES_ENDPOINT",
            self._contract(),
            msg="module.contract.yaml outputs.produced must include OBSERVABILITY_TRACES_ENDPOINT (FR-010, AC-010)",
        )

    def test_contract_includes_api_key_output(self) -> None:
        self.assertIn(
            "OBSERVABILITY_API_KEY",
            self._contract(),
            msg="module.contract.yaml outputs.produced must include OBSERVABILITY_API_KEY (FR-010, AC-010)",
        )

    def test_contract_includes_observability_username_optional_env(self) -> None:
        self.assertIn(
            "OBSERVABILITY_USERNAME",
            self._contract(),
            msg="module.contract.yaml optional_env must include OBSERVABILITY_USERNAME (FR-010)",
        )

    def test_contract_includes_faro_endpoint_output(self) -> None:
        self.assertIn(
            "FARO_ENDPOINT",
            self._contract(),
            msg="module.contract.yaml outputs.produced must include FARO_ENDPOINT (FR-006, AC-002)",
        )

    def test_contract_includes_faro_cors_optional_env(self) -> None:
        self.assertIn(
            "FARO_CORS_ALLOWED_ORIGINS",
            self._contract(),
            msg="module.contract.yaml optional_env must include FARO_CORS_ALLOWED_ORIGINS (FR-006)",
        )

    def test_contract_includes_observability_dashboards_name_optional_env(self) -> None:
        self.assertIn(
            "OBSERVABILITY_DASHBOARDS_NAME",
            self._contract(),
            msg="module.contract.yaml optional_env must include OBSERVABILITY_DASHBOARDS_NAME (FR-017, AC-010)",
        )


class RuntimeStateContractTests(unittest.TestCase):
    """AC-001, AC-002, AC-009, NFR-OPS-001 — state file structure and OTEL endpoint contract."""

    def test_stackit_runtime_state_has_logs_endpoint_key(self) -> None:
        self.assertTrue(
            re.search(r"^logs_endpoint=", _MOCK_RUNTIME_STATE_STACKIT, re.MULTILINE) is not None,
            msg="observability_runtime state must contain logs_endpoint key on STACKIT lane (AC-001, NFR-OPS-001)",
        )

    def test_stackit_runtime_state_has_metrics_endpoint_key(self) -> None:
        self.assertTrue(
            re.search(r"^metrics_endpoint=", _MOCK_RUNTIME_STATE_STACKIT, re.MULTILINE) is not None,
            msg="observability_runtime state must contain metrics_endpoint key on STACKIT lane (AC-001, NFR-OPS-001)",
        )

    def test_stackit_runtime_state_has_traces_endpoint_key(self) -> None:
        self.assertTrue(
            re.search(r"^traces_endpoint=", _MOCK_RUNTIME_STATE_STACKIT, re.MULTILINE) is not None,
            msg="observability_runtime state must contain traces_endpoint key on STACKIT lane (AC-001, NFR-OPS-001)",
        )

    def test_otel_endpoint_is_in_cluster_dns_on_stackit(self) -> None:
        match = re.search(r"^otel_endpoint=(.+)$", _MOCK_RUNTIME_STATE_STACKIT, re.MULTILINE)
        self.assertIsNotNone(match, msg="otel_endpoint key must be present in STACKIT state (AC-002)")
        self.assertIn(
            "otel-collector.observability.svc.cluster.local",
            match.group(1),
            msg="otel_endpoint must point to in-cluster collector DNS on STACKIT lane (AC-002, NFR-OBS-001)",
        )

    def test_otel_endpoint_is_in_cluster_dns_on_local(self) -> None:
        match = re.search(r"^otel_endpoint=(.+)$", _MOCK_RUNTIME_STATE_LOCAL, re.MULTILINE)
        self.assertIsNotNone(match, msg="otel_endpoint key must be present in local state (AC-002)")
        self.assertIn(
            "otel-collector.observability.svc.cluster.local",
            match.group(1),
            msg="otel_endpoint must be identical in-cluster DNS on local lane (AC-002, NFR-OBS-001)",
        )

    def test_api_key_is_empty_on_local_lane(self) -> None:
        match = re.search(r"^api_key=(.*)$", _MOCK_RUNTIME_STATE_LOCAL, re.MULTILINE)
        self.assertIsNotNone(match, msg="api_key key must be present in local state (AC-009, FR-003)")
        self.assertEqual(
            "",
            match.group(1),
            msg="api_key must be empty string on local lane — credential delivered only via K8s Secret (AC-009, NFR-SEC-001)",
        )

    def test_runtime_state_does_not_contain_password(self) -> None:
        self.assertNotIn(
            "password=",
            _MOCK_RUNTIME_STATE_STACKIT,
            msg="observability_runtime state MUST NOT contain credential password (NFR-SEC-001)",
        )

    def test_runtime_state_has_faro_endpoint_key(self) -> None:
        import re
        match = re.search(r"^faro_endpoint=(.+)$", _MOCK_RUNTIME_STATE_LOCAL, re.MULTILINE)
        self.assertIsNotNone(match, msg="observability_runtime state must contain faro_endpoint key (FR-007)")
        self.assertIn(
            "12347",
            match.group(1),
            msg="faro_endpoint must reference port 12347 (FR-001, AC-001)",
        )


class FaroEndpointShellLibTests(unittest.TestCase):
    """FR-001, FR-002 — observability_faro_endpoint() helper and FARO_ENDPOINT export."""

    def _lib(self) -> str:
        return _SHELL_LIB.read_text(encoding="utf-8")

    def test_faro_endpoint_function_exists(self) -> None:
        self.assertIn(
            "observability_faro_endpoint()",
            self._lib(),
            msg="observability.sh must declare observability_faro_endpoint() (FR-001)",
        )

    def test_faro_endpoint_uses_otel_collector_service_dns(self) -> None:
        self.assertIn(
            "OTEL_COLLECTOR_SERVICE_DNS",
            self._lib(),
            msg="observability_faro_endpoint() must reference OTEL_COLLECTOR_SERVICE_DNS (FR-001)",
        )

    def test_faro_endpoint_uses_faro_collect_path(self) -> None:
        self.assertIn(
            "FARO_COLLECT_PATH",
            self._lib(),
            msg="observability_faro_endpoint() must reference FARO_COLLECT_PATH (FR-001)",
        )

    def test_init_env_exports_faro_endpoint(self) -> None:
        lib = self._lib()
        self.assertIn(
            "FARO_ENDPOINT",
            lib,
            msg="observability_init_env() must export FARO_ENDPOINT via set_default_env (FR-002)",
        )


class FaroReceiverValuesTests(unittest.TestCase):
    """FR-003, FR-004, FR-005, FR-009, FR-010, FR-011 — OTEL values files and ArgoCD manifests."""

    def _local_values(self) -> str:
        return _LOCAL_OTC_VALUES.read_text(encoding="utf-8")

    def _stackit_values(self) -> str:
        return _OTC_VALUES.read_text(encoding="utf-8")

    def test_local_values_has_faro_receiver_port(self) -> None:
        self.assertIn(
            "12347",
            self._local_values(),
            msg="local otel-collector.values.yaml must declare Faro port 12347 (FR-003, AC-003)",
        )

    def test_stackit_values_has_faro_receiver_port(self) -> None:
        self.assertIn(
            "12347",
            self._stackit_values(),
            msg="STACKIT otel-collector.values.yaml must declare Faro port 12347 (FR-004, AC-004)",
        )

    def test_argocd_dev_has_faro_port(self) -> None:
        self.assertIn(
            "12347",
            _ARGOCD_DEV.read_text(encoding="utf-8"),
            msg="dev/observability.yaml must declare Faro port 12347 (FR-005, AC-005)",
        )

    def test_argocd_stage_has_faro_port(self) -> None:
        self.assertIn(
            "12347",
            _ARGOCD_STAGE.read_text(encoding="utf-8"),
            msg="stage/observability.yaml must declare Faro port 12347 (FR-005, AC-005)",
        )

    def test_argocd_prod_has_faro_port(self) -> None:
        self.assertIn(
            "12347",
            _ARGOCD_PROD.read_text(encoding="utf-8"),
            msg="prod/observability.yaml must declare Faro port 12347 (FR-005, AC-005)",
        )

    def test_local_values_has_memory_limiter(self) -> None:
        self.assertIn(
            "memory_limiter",
            self._local_values(),
            msg="local otel-collector.values.yaml must declare memory_limiter processor (FR-009, AC-006)",
        )

    def test_stackit_values_has_memory_limiter(self) -> None:
        self.assertIn(
            "memory_limiter",
            self._stackit_values(),
            msg="STACKIT otel-collector.values.yaml must declare memory_limiter processor (FR-009, AC-006)",
        )

    def test_local_values_has_filter_drop_healthcheck(self) -> None:
        self.assertIn(
            "drop-healthcheck-spans",
            self._local_values(),
            msg="local otel-collector.values.yaml must declare filter/drop-healthcheck-spans (FR-010, AC-007)",
        )

    def test_stackit_values_has_filter_drop_healthcheck(self) -> None:
        self.assertIn(
            "drop-healthcheck-spans",
            self._stackit_values(),
            msg="STACKIT otel-collector.values.yaml must declare filter/drop-healthcheck-spans (FR-010, AC-007)",
        )

    def test_local_values_has_spanmetrics(self) -> None:
        self.assertIn(
            "spanmetrics",
            self._local_values(),
            msg="local otel-collector.values.yaml must declare spanmetrics connector (FR-011, AC-008)",
        )

    def test_memory_limiter_before_batch_local(self) -> None:
        content = self._local_values()
        ml_pos = content.find("memory_limiter")
        batch_pos = content.find("batch")
        self.assertGreater(
            batch_pos,
            ml_pos,
            msg="memory_limiter must appear before batch in local values (NFR-OPS-001, AC-006)",
        )

    def test_memory_limiter_before_batch_stackit(self) -> None:
        content = self._stackit_values()
        ml_pos = content.find("memory_limiter")
        batch_pos = content.find("batch")
        self.assertGreater(
            batch_pos,
            ml_pos,
            msg="memory_limiter must appear before batch in STACKIT values (NFR-OPS-001, AC-006)",
        )

    def test_local_values_cors_uses_env_substitution(self) -> None:
        self.assertIn(
            "${env:FARO_CORS_ALLOWED_ORIGINS}",
            self._local_values(),
            msg="local values must use OTC env substitution for FARO_CORS_ALLOWED_ORIGINS (NFR-SEC-001, FR-003)",
        )

    def test_stackit_values_cors_uses_env_substitution(self) -> None:
        self.assertIn(
            "${env:FARO_CORS_ALLOWED_ORIGINS}",
            self._stackit_values(),
            msg="STACKIT values must use OTC env substitution for FARO_CORS_ALLOWED_ORIGINS (NFR-SEC-001, FR-004)",
        )

    def test_local_values_has_faro_cors_extra_env(self) -> None:
        self.assertIn(
            "FARO_CORS_ALLOWED_ORIGINS",
            self._local_values(),
            msg="local values must declare FARO_CORS_ALLOWED_ORIGINS extraEnv with default * (FR-003)",
        )

    def test_argocd_dev_has_faro_cors_extra_env(self) -> None:
        self.assertIn(
            "FARO_CORS_ALLOWED_ORIGINS",
            _ARGOCD_DEV.read_text(encoding="utf-8"),
            msg="dev/observability.yaml must declare FARO_CORS_ALLOWED_ORIGINS extraEnv (FR-005)",
        )

    def test_argocd_stage_has_faro_cors_extra_env(self) -> None:
        self.assertIn(
            "FARO_CORS_ALLOWED_ORIGINS",
            _ARGOCD_STAGE.read_text(encoding="utf-8"),
            msg="stage/observability.yaml must declare FARO_CORS_ALLOWED_ORIGINS extraEnv (FR-005)",
        )

    def test_argocd_prod_has_faro_cors_extra_env(self) -> None:
        self.assertIn(
            "FARO_CORS_ALLOWED_ORIGINS",
            _ARGOCD_PROD.read_text(encoding="utf-8"),
            msg="prod/observability.yaml must declare FARO_CORS_ALLOWED_ORIGINS extraEnv (FR-005)",
        )


class DashboardProvisioningTests(unittest.TestCase):
    """FR-012 through FR-017 — dashboard provisioning scripts, make targets, seed dashboard."""

    def test_seed_dashboard_exists(self) -> None:
        self.assertTrue(
            _SEED_DASHBOARD.exists(),
            msg="infra/observability/dashboards/golden-signals.json must exist (FR-012, AC-009)",
        )

    def test_seed_dashboard_is_valid_json(self) -> None:
        import json
        self.assertTrue(_SEED_DASHBOARD.exists(), msg="seed dashboard file must exist first")
        data = json.loads(_SEED_DASHBOARD.read_text(encoding="utf-8"))
        self.assertIn(
            "panels",
            data,
            msg="golden-signals.json must be a valid Grafana dashboard JSON with panels key (FR-012, AC-009)",
        )

    def test_dashboard_apply_script_exists(self) -> None:
        self.assertTrue(
            _DASHBOARDS_APPLY_SCRIPT.exists(),
            msg="observability_dashboards_apply.sh must exist (FR-013)",
        )

    def test_dashboard_apply_script_uses_grafana_dashboard_label(self) -> None:
        content = _DASHBOARDS_APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "grafana_dashboard",
            content,
            msg="observability_dashboards_apply.sh must apply ConfigMap with label grafana_dashboard=1 (FR-013, NFR-OPS-002)",
        )

    def test_dashboard_apply_script_uses_dry_run_client(self) -> None:
        content = _DASHBOARDS_APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "dry-run=client",
            content,
            msg="observability_dashboards_apply.sh must use --dry-run=client | kubectl apply for idempotency (FR-013, NFR-OPS-003)",
        )

    def test_dashboard_destroy_script_exists(self) -> None:
        self.assertTrue(
            _DASHBOARDS_DESTROY_SCRIPT.exists(),
            msg="observability_dashboards_destroy.sh must exist (FR-014)",
        )

    def test_dashboard_apply_target_in_makefile_template(self) -> None:
        content = _MAKEFILE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-observability-dashboards-apply",
            content,
            msg="blueprint.generated.mk.tmpl must declare infra-observability-dashboards-apply target (FR-015)",
        )

    def test_bootstrap_seed_dashboard_exists(self) -> None:
        self.assertTrue(
            _BOOTSTRAP_SEED_DASHBOARD.exists(),
            msg="bootstrap template must mirror golden-signals.json seed dashboard (FR-016)",
        )


class PyramidContractRegistrationTests(unittest.TestCase):
    """FR-011, AC-007 — test file is registered in test_pyramid_contract.json."""

    def test_test_contract_registered_in_pyramid_contract(self) -> None:
        content = _PYRAMID_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "tests/infra/modules/observability/test_contract.py",
            content,
            msg="test_contract.py must be registered in test_pyramid_contract.json under unit scope (FR-011, AC-007)",
        )
