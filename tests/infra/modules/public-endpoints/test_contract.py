from __future__ import annotations
import re
import unittest
from pathlib import Path
from tests._shared.helpers import REPO_ROOT

_GATEWAY_TEMPLATE = REPO_ROOT / "scripts" / "templates" / "infra" / "bootstrap" / "infra" / "gateway" / "public-endpoints.yaml.tmpl"
_CERT_MANAGER_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "core" / "cert-manager.values.yaml"
_CERT_MANAGER_TEMPLATE = REPO_ROOT / "scripts" / "templates" / "infra" / "bootstrap" / "infra" / "local" / "helm" / "core" / "cert-manager.values.yaml"
_SHELL_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "public_endpoints.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "public_endpoints_apply.sh"
_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "public_endpoints_destroy.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "public_endpoints_smoke.sh"
_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "public-endpoints" / "module.contract.yaml"
_PYRAMID_CONTRACT = REPO_ROOT / "scripts" / "lib" / "quality" / "test_pyramid_contract.json"
_README = REPO_ROOT / "docs" / "platform" / "modules" / "public-endpoints" / "README.md"
_APPPROJECT_EDGE_ENVS = ("dev", "stage", "prod", "local")


class CertManagerFeatureGateTests(unittest.TestCase):
    def test_ac005_cert_manager_values_has_feature_gate(self) -> None:
        content = _CERT_MANAGER_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "ExperimentalGatewayAPISupport",
            content,
            msg="cert-manager.values.yaml must contain ExperimentalGatewayAPISupport featureGate (AC-005, FR-005)",
        )

    def test_ac005_cert_manager_template_has_feature_gate(self) -> None:
        content = _CERT_MANAGER_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "ExperimentalGatewayAPISupport",
            content,
            msg="bootstrap cert-manager.values.yaml template must contain ExperimentalGatewayAPISupport featureGate (AC-005, FR-005)",
        )


class GatewayTemplateTests(unittest.TestCase):
    def _template(self) -> str:
        return _GATEWAY_TEMPLATE.read_text(encoding="utf-8")

    def test_ac001_template_has_https_listener(self) -> None:
        content = self._template()
        self.assertIn(
            "port: 443",
            content,
            msg="gateway template must contain HTTPS listener on port 443 (AC-001, FR-001)",
        )
        self.assertIn(
            "mode: Terminate",
            content,
            msg="gateway template HTTPS listener must have tls.mode: Terminate (AC-001, FR-001)",
        )

    def test_ac001_template_has_http_listener(self) -> None:
        content = self._template()
        self.assertIn(
            "port: 80",
            content,
            msg="gateway template must contain HTTP listener on port 80 (AC-001, FR-001)",
        )

    def test_ac001_template_has_gatewayclass(self) -> None:
        self.assertIn(
            "kind: GatewayClass",
            self._template(),
            msg="gateway template must contain GatewayClass resource (AC-001, FR-001)",
        )

    def test_ac004_template_has_external_dns_annotation(self) -> None:
        self.assertIn(
            "external-dns.alpha.kubernetes.io/hostname",
            self._template(),
            msg="gateway template must contain external-dns hostname annotation (AC-004, FR-004)",
        )

    def test_ac013_template_has_tls_min_version(self) -> None:
        content = self._template()
        # TLS min version is set via ClientTrafficPolicy in the gateway template.
        # Envoy Gateway TLSVersion enum uses bare version strings ("1.2", "1.3"), not "TLSv1.x".
        self.assertIn(
            '"1.2"',
            content,
            msg='gateway manifest must configure TLS minimum version "1.2" (AC-013, NFR-SEC-002)',
        )
        self.assertNotIn(
            '"1.0"',
            content,
            msg='gateway manifest must NOT permit TLS "1.0" (AC-013, NFR-SEC-002)',
        )
        self.assertNotIn(
            '"1.1"',
            content,
            msg='gateway manifest must NOT permit TLS "1.1" (AC-013, NFR-SEC-002)',
        )


class IssuerCertificateRenderingTests(unittest.TestCase):
    def _lib(self) -> str:
        return _SHELL_LIB.read_text(encoding="utf-8")

    def test_ac002_lib_renders_issuer_manifest(self) -> None:
        content = self._lib()
        self.assertIn(
            "kind: Issuer",
            content,
            msg="public_endpoints.sh must render Issuer manifest (AC-002, FR-002)",
        )

    def test_ac002_lib_renders_acme_issuer_for_stackit(self) -> None:
        self.assertIn(
            "acme:",
            self._lib(),
            msg="public_endpoints.sh must render ACME issuer config for STACKIT profiles (AC-002, FR-002)",
        )

    def test_ac002_lib_renders_selfsigned_issuer_for_local(self) -> None:
        self.assertIn(
            "selfSigned",
            self._lib(),
            msg="public_endpoints.sh must render selfSigned Issuer for local profiles (AC-002, FR-002)",
        )

    def test_ac003_lib_renders_certificate_manifest(self) -> None:
        content = self._lib()
        self.assertIn(
            "kind: Certificate",
            content,
            msg="public_endpoints.sh must render Certificate manifest (AC-003, FR-003)",
        )

    def test_ac003_lib_renders_certificate_with_dns_names(self) -> None:
        self.assertIn(
            "dnsNames",
            self._lib(),
            msg="public_endpoints.sh Certificate manifest must include dnsNames (AC-003, FR-003)",
        )

    def test_ac003_lib_renders_certificate_with_issuer_ref(self) -> None:
        self.assertIn(
            "issuerRef",
            self._lib(),
            msg="public_endpoints.sh Certificate manifest must include issuerRef (AC-003, FR-003)",
        )

    def test_ac015_lib_renders_certificate_with_renew_before(self) -> None:
        self.assertIn(
            "renewBefore",
            self._lib(),
            msg="public_endpoints.sh Certificate manifest must include renewBefore field (AC-015, NFR-OBS-002)",
        )

    def test_ac017_readme_documents_hsts_guidance(self) -> None:
        # BackendTrafficPolicy.responseHeaderModifiers is not a valid EG 1.x field.
        # HSTS is documented as consumer HTTPRoute responsibility in the module README.
        content = _README.read_text(encoding="utf-8")
        self.assertIn(
            "Strict-Transport-Security",
            content,
            msg="README must document Strict-Transport-Security HSTS guidance (AC-017, NFR-SEC-006)",
        )
        self.assertIn(
            "max-age=31536000",
            content,
            msg="README must document HSTS max-age=31536000 (1 year) (AC-017, NFR-SEC-006)",
        )
        self.assertIn(
            "includeSubDomains",
            content,
            msg="README must document HSTS includeSubDomains (AC-017, NFR-SEC-006)",
        )
        self.assertIn(
            "HTTPRoute",
            content,
            msg="README must document HSTS as consumer HTTPRoute responsibility (AC-017, NFR-SEC-006)",
        )

    def test_init_env_requires_issuer_email_for_non_local_profiles(self) -> None:
        content = self._lib()
        # init_env uses the direct $BLUEPRINT_PROFILE glob check (consistent with ACME server
        # selection in the same function) rather than is_local_profile() to avoid a
        # profile.sh source dependency in callers that don't load profile.sh.
        self.assertIn(
            "require_env_vars PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL",
            content,
            msg="public_endpoints_init_env must require PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL for non-local profiles to prevent silent ACME registration failure (NFR-SEC-001)",
        )

    def test_ac018_lib_renders_network_policy(self) -> None:
        content = self._lib()
        self.assertIn(
            "NetworkPolicy",
            content,
            msg="public_endpoints.sh must render NetworkPolicy manifest (AC-018, NFR-SEC-007)",
        )
        self.assertIn(
            "port: 80",
            content,
            msg="NetworkPolicy must allow port 80 for Envoy pods (AC-018, NFR-SEC-007)",
        )
        self.assertIn(
            "port: 443",
            content,
            msg="NetworkPolicy must allow port 443 for Envoy pods (AC-018, NFR-SEC-007)",
        )


class ApplyScriptTests(unittest.TestCase):
    def _apply(self) -> str:
        return _APPLY_SCRIPT.read_text(encoding="utf-8")

    def test_ac009_apply_writes_cluster_issuer_name(self) -> None:
        self.assertIn(
            "cluster_issuer_name",
            self._apply(),
            msg="public_endpoints_apply.sh must write cluster_issuer_name to runtime state (AC-009, NFR-OPS-001)",
        )

    def test_ac009_apply_writes_cluster_issuer_type(self) -> None:
        self.assertIn(
            "cluster_issuer_type",
            self._apply(),
            msg="public_endpoints_apply.sh must write cluster_issuer_type to runtime state (AC-009, NFR-OPS-001)",
        )

    def test_ac009_apply_writes_tls_secret_name(self) -> None:
        self.assertIn(
            "tls_secret_name",
            self._apply(),
            msg="public_endpoints_apply.sh must write tls_secret_name to runtime state (AC-009, NFR-OPS-001)",
        )

    def test_ac019_apply_warns_kms_for_stackit_profiles(self) -> None:
        content = self._apply()
        self.assertIn(
            "stackit-stage",
            content,
            msg="public_endpoints_apply.sh must check for stackit-stage profile for KMS warning (AC-019, NFR-SEC-008)",
        )
        self.assertIn(
            "stackit-prod",
            content,
            msg="public_endpoints_apply.sh must check for stackit-prod profile for KMS warning (AC-019, NFR-SEC-008)",
        )
        self.assertIn(
            "KMS",
            content,
            msg="public_endpoints_apply.sh must emit KMS warning for stackit-stage/prod without KMS module (AC-019, NFR-SEC-008)",
        )


class QualityGateTests(unittest.TestCase):
    def test_ac011_test_contract_registered_in_pyramid_contract(self) -> None:
        content = _PYRAMID_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "tests/infra/modules/public-endpoints/test_contract.py",
            content,
            msg="test_contract.py must be registered in test_pyramid_contract.json under unit scope (AC-011, FR-008)",
        )

    def test_ac012_test_contract_has_at_least_ten_assertions(self) -> None:
        content = Path(__file__).read_text(encoding="utf-8")
        assert_calls = re.findall(r"\bself\.assert", content)
        self.assertGreaterEqual(
            len(assert_calls),
            10,
            msg=f"test_contract.py must contain ≥10 assertions; found {len(assert_calls)} (AC-012, FR-008)",
        )


class DestroyOrderingTests(unittest.TestCase):
    def test_ac020_destroy_deletes_certificate_before_issuer(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        # Use regex to match actual kubectl delete commands, not comment text which also
        # contains "Certificate" and "Issuer" (e.g. "# Certificate MUST be deleted before Issuer").
        cert_match = re.search(r"\bdelete certificate\b", content, re.IGNORECASE)
        issuer_match = re.search(r"\bdelete issuer\b", content, re.IGNORECASE)
        self.assertIsNotNone(
            cert_match,
            msg="public_endpoints_destroy.sh must contain 'delete certificate' command (AC-020, NFR-REL-001)",
        )
        self.assertIsNotNone(
            issuer_match,
            msg="public_endpoints_destroy.sh must contain 'delete issuer' command (AC-020, NFR-REL-001)",
        )
        self.assertLess(
            cert_match.start(),  # type: ignore[union-attr]
            issuer_match.start(),  # type: ignore[union-attr]
            msg="Certificate deletion command must appear before Issuer deletion command in destroy script (AC-020, NFR-REL-001)",
        )

    def test_ac020_destroy_deletes_issuer_before_gateway_baseline(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        issuer_match = re.search(r"\bdelete issuer\b", content, re.IGNORECASE)
        self.assertIsNotNone(
            issuer_match,
            msg="public_endpoints_destroy.sh must contain 'delete issuer' command (AC-020, NFR-REL-001)",
        )
        # Gateway baseline removal is identified by delete_helm_gateway_baseline or run_manifest_delete of gateway
        gateway_pos = content.find("delete_helm_gateway_baseline")
        if gateway_pos == -1:
            gateway_pos = content.find("gateway_manifest_path")
        self.assertGreater(
            gateway_pos,
            issuer_match.start(),  # type: ignore[union-attr]
            msg="Issuer deletion command must appear before gateway baseline removal in destroy script (AC-020, NFR-REL-001)",
        )


class SmokeScriptTests(unittest.TestCase):
    def _smoke(self) -> str:
        return _SMOKE_SCRIPT.read_text(encoding="utf-8")

    def test_ac006_smoke_validates_https_listener(self) -> None:
        content = self._smoke()
        self.assertIn(
            "443",
            content,
            msg="public_endpoints_smoke.sh must validate HTTPS listener on port 443 (AC-006, NFR-OBS-001)",
        )

    def test_ac007_smoke_validates_external_dns_annotation(self) -> None:
        self.assertIn(
            "external-dns.alpha.kubernetes.io/hostname",
            self._smoke(),
            msg="public_endpoints_smoke.sh must validate external-dns annotation (AC-007, NFR-OBS-001)",
        )

    def test_ac008_smoke_validates_issuer_manifest_on_disk(self) -> None:
        content = self._smoke()
        self.assertIn(
            "issuer",
            content.lower(),
            msg="public_endpoints_smoke.sh must validate Issuer manifest file exists on disk (AC-008, NFR-OBS-001)",
        )

    def test_ac008_smoke_validates_certificate_manifest_on_disk(self) -> None:
        content = self._smoke()
        self.assertIn(
            "certificate",
            content.lower(),
            msg="public_endpoints_smoke.sh must validate Certificate manifest file exists on disk (AC-008, NFR-OBS-001)",
        )


class AppProjectEdgeTests(unittest.TestCase):
    def test_ac010_all_envs_have_certmanager_issuer_in_whitelist(self) -> None:
        for env in _APPPROJECT_EDGE_ENVS:
            path = REPO_ROOT / "infra" / "gitops" / "argocd" / "overlays" / env / "appproject-edge.yaml"
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                "cert-manager.io/Issuer",
                content,
                msg=f"appproject-edge.yaml for {env} must include cert-manager.io/Issuer in namespaceResourceWhitelist (AC-010, FR-007)",
            )

    def test_ac010_all_envs_have_certmanager_certificate_in_whitelist(self) -> None:
        for env in _APPPROJECT_EDGE_ENVS:
            path = REPO_ROOT / "infra" / "gitops" / "argocd" / "overlays" / env / "appproject-edge.yaml"
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                "cert-manager.io/Certificate",
                content,
                msg=f"appproject-edge.yaml for {env} must include cert-manager.io/Certificate in namespaceResourceWhitelist (AC-010, FR-007)",
            )


class ModuleContractTests(unittest.TestCase):
    def test_ac016_contract_declares_cluster_issuer_name(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME",
            content,
            msg="module.contract.yaml must declare PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME optional env var (AC-016, FR-006)",
        )

    def test_ac016_contract_declares_cluster_issuer_email(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL",
            content,
            msg="module.contract.yaml must declare PUBLIC_ENDPOINTS_CLUSTER_ISSUER_EMAIL optional env var (AC-016, FR-006)",
        )

    def test_ac016_contract_declares_acme_server(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "PUBLIC_ENDPOINTS_ACME_SERVER",
            content,
            msg="module.contract.yaml must declare PUBLIC_ENDPOINTS_ACME_SERVER optional env var (AC-016, FR-006)",
        )

    def test_ac016_contract_declares_tls_secret_name(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME",
            content,
            msg="module.contract.yaml must declare PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME optional env var (AC-016, FR-006)",
        )


class ProfileAwareAcmeTests(unittest.TestCase):
    def test_ac014_init_env_uses_staging_for_stackit_dev(self) -> None:
        content = _SHELL_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "acme-staging-v02.api.letsencrypt.org",
            content,
            msg="public_endpoints.sh init_env must set staging ACME server for non-prod profiles (AC-014, NFR-SEC-004)",
        )

    def test_ac014_init_env_uses_production_for_stackit_prod(self) -> None:
        content = _SHELL_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "acme-v02.api.letsencrypt.org/directory",
            content,
            msg="public_endpoints.sh init_env must set production ACME server for stackit-prod (AC-014, NFR-SEC-004)",
        )
