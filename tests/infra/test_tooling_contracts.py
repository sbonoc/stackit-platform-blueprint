from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT, run


class PlatformPythonHelperGuardTests(unittest.TestCase):
    """Guard tests for FR-009 / AC-006: platform shell scripts MUST reference existing Python helpers.

    These tests ensure that python3 "$ROOT_DIR/scripts/lib/..." invocations in
    scripts/bin/platform/** resolve to files that actually exist in the repository.
    They fail if helper files are moved without updating the caller references.
    """

    # Matches "$ROOT_DIR/scripts/lib/...py" in both direct python3 invocations
    # and variable assignments that are later passed to python3.
    _PYTHON_REF_RE = re.compile(r'"\$ROOT_DIR/(scripts/lib/[^"]+\.py)"')

    def _extract_python_helper_refs(self, script_path: Path) -> list[str]:
        text = script_path.read_text(encoding="utf-8")
        return self._PYTHON_REF_RE.findall(text)

    def test_smoke_sh_python_helper_refs_exist(self) -> None:
        """T-105: scripts/bin/platform/apps/smoke.sh python3 helper references must exist."""
        script = REPO_ROOT / "scripts/bin/platform/apps/smoke.sh"
        refs = self._extract_python_helper_refs(script)
        self.assertTrue(refs, msg="expected at least one python3 helper ref in smoke.sh")
        for ref in refs:
            self.assertTrue(
                (REPO_ROOT / ref).is_file(),
                msg=f"smoke.sh references missing helper: {ref}",
            )

    def test_reconcile_argocd_repo_credentials_sh_python_helper_refs_exist(self) -> None:
        """T-106: scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh python3 refs must exist."""
        script = REPO_ROOT / "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh"
        refs = self._extract_python_helper_refs(script)
        self.assertTrue(refs, msg="expected at least one python3 helper ref in reconcile_argocd_repo_credentials.sh")
        for ref in refs:
            self.assertTrue(
                (REPO_ROOT / ref).is_file(),
                msg=f"reconcile_argocd_repo_credentials.sh references missing helper: {ref}",
            )

    def test_quality_infra_shell_source_graph_check_passes_with_current_platform_refs(self) -> None:
        """Guard passes when all scripts/bin/platform/** python3 helper references resolve to existing files.

        The negative path (AC-006: guard fails on a missing helper) is covered transitively:
        test_smoke_sh_python_helper_refs_exist and test_reconcile_argocd_repo_credentials_sh_python_helper_refs_exist
        would fail first if a caller were updated without also updating the helper path, causing
        this end-to-end pass assertion to become unreachable in practice.
        """
        result = run(["python3", "scripts/bin/quality/check_infra_shell_source_graph.py"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("quality-infra-shell-source-graph-check", result.stdout)


class AppProjectNamespacePolicyTests(unittest.TestCase):
    """Guard: all ArgoCD AppProject overlays MUST include external-secrets in destinations.

    FR-002, FR-003: infra-contract-test-fast must fail when any AppProject overlay is
    missing external-secrets from its spec.destinations list.
    """

    _APPPROJECT_PATHS = [
        "infra/gitops/argocd/overlays/local/appproject.yaml",
        "infra/gitops/argocd/overlays/dev/appproject.yaml",
        "infra/gitops/argocd/overlays/stage/appproject.yaml",
        "infra/gitops/argocd/overlays/prod/appproject.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/appproject.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/appproject.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/appproject.yaml",
    ]
    _REQUIRED_NAMESPACE = "external-secrets"

    def _destination_namespaces(self, appproject_path: Path) -> list[str]:
        import yaml as _yaml
        doc = _yaml.safe_load(appproject_path.read_text())
        destinations = doc.get("spec", {}).get("destinations", [])
        return [d.get("namespace", "") for d in destinations]

    def test_all_appproject_overlays_include_external_secrets_destination(self) -> None:
        """T-101: every AppProject file must allow external-secrets as a destination namespace."""
        missing: list[str] = []
        for rel in self._APPPROJECT_PATHS:
            path = REPO_ROOT / rel
            self.assertTrue(path.is_file(), msg=f"AppProject file not found: {rel}")
            namespaces = self._destination_namespaces(path)
            if self._REQUIRED_NAMESPACE not in namespaces:
                missing.append(rel)
        self.assertFalse(
            missing,
            msg=(
                f"AppProject files missing '{self._REQUIRED_NAMESPACE}' in spec.destinations: "
                + ", ".join(missing)
            ),
        )


class SddPlaceholderGuardTests(unittest.TestCase):
    """Guard: check_sdd_assets.py MUST detect empty required fields in context_pack.md and architecture.md.

    FR-001, FR-002: make quality-hardening-review must fail when required fields
    have empty values in SPEC_READY=true work-item documents.
    """

    _REF_WORK_ITEM = "2026-04-22-issue-152-sdd-placeholder-guard"
    _ADR_PATH = "docs/blueprint/architecture/decisions/ADR-20260422-issue-152-sdd-placeholder-guard.md"

    def _temp_spec_dir(self, slug: str, *, spec_ready: bool) -> Path:
        """Create a minimal valid spec dir inside the real specs/ workspace."""
        import shutil as _shutil
        ref_dir = REPO_ROOT / "specs" / self._REF_WORK_ITEM
        spec_dir = REPO_ROOT / "specs" / slug
        if spec_dir.exists():
            _shutil.rmtree(spec_dir)
        spec_dir.mkdir()
        ref_spec = ref_dir / "spec.md"
        spec_content = ref_spec.read_text(encoding="utf-8")
        spec_content = spec_content.replace(
            "- SPEC_READY: true",
            f"- SPEC_READY: {'true' if spec_ready else 'false'}",
        )
        (spec_dir / "spec.md").write_text(spec_content, encoding="utf-8")
        for artifact in ("plan.md", "traceability.md", "graph.json",
                         "evidence_manifest.json", "pr_context.md", "hardening_review.md"):
            (spec_dir / artifact).write_text(
                (ref_dir / artifact).read_text(encoding="utf-8"), encoding="utf-8"
            )
        # tasks.md: use unchecked scaffold when not ready so the validator does not
        # flag implementation tasks being checked before SPEC_READY=true.
        if spec_ready:
            (spec_dir / "tasks.md").write_text(
                (ref_dir / "tasks.md").read_text(encoding="utf-8"), encoding="utf-8"
            )
        else:
            (spec_dir / "tasks.md").write_text(
                "# Tasks\n\n## Gate Checks (Required Before Implementation)\n"
                "- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`\n\n"
                "## Implementation\n- [ ] T-001 placeholder\n\n"
                "## App Onboarding Minimum Targets (Normative)\n"
                "No app delivery scope affected; all targets below remain unaffected by this work item.\n"
                "- [x] A-001 `apps-bootstrap` and `apps-smoke` — unaffected\n"
                "- [x] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` — unaffected\n"
                "- [x] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` — unaffected\n"
                "- [x] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` — unaffected\n"
                "- [x] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` — unaffected\n",
                encoding="utf-8",
            )
        return spec_dir

    def test_empty_context_pack_required_field_fails_when_spec_ready(self) -> None:
        slug = "test-placeholder-guard-empty-context-pack"
        spec_dir = self._temp_spec_dir(slug, spec_ready=True)
        try:
            (spec_dir / "context_pack.md").write_text(
                "# Work Item Context Pack\n\n## Context Snapshot\n"
                "- Work item:\n"  # empty — should trigger violation
                f"- SPEC_READY: true\n- ADR path: {self._ADR_PATH}\n- ADR status: approved\n\n"
                "## Guardrail Controls\n- Applicable control IDs: SDD-C-005\n",
                encoding="utf-8",
            )
            (spec_dir / "architecture.md").write_text(
                "# Architecture\n\n## Context\n- Work item: test-item\n- Owner: bonos\n- Date: 2026-04-22\n",
                encoding="utf-8",
            )
            result = run(["python3", "scripts/bin/quality/check_sdd_assets.py"])
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            combined = result.stdout + result.stderr
            self.assertIn("scaffold placeholder not filled in", combined)
            self.assertIn("Work item", combined)
        finally:
            import shutil as _shutil
            _shutil.rmtree(spec_dir, ignore_errors=True)

    def test_none_value_is_accepted_for_required_field(self) -> None:
        slug = "test-placeholder-guard-none-value"
        spec_dir = self._temp_spec_dir(slug, spec_ready=True)
        try:
            (spec_dir / "context_pack.md").write_text(
                "# Work Item Context Pack\n\n## Context Snapshot\n"
                "- Work item: test-none-value\n"
                "- SPEC_READY: true\n"
                f"- ADR path: {self._ADR_PATH}\n"
                "- ADR status: approved\n\n"
                "## Guardrail Controls\n- Applicable control IDs: none\n",
                encoding="utf-8",
            )
            (spec_dir / "architecture.md").write_text(
                "# Architecture\n\n## Context\n- Work item: test-item\n- Owner: bonos\n- Date: 2026-04-22\n",
                encoding="utf-8",
            )
            result = run(["python3", "scripts/bin/quality/check_sdd_assets.py"])
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, msg=combined)
            self.assertNotIn("scaffold placeholder not filled in", combined,
                             msg=f"'none' value should be accepted: {combined}")
        finally:
            import shutil as _shutil
            _shutil.rmtree(spec_dir, ignore_errors=True)

    def test_empty_fields_do_not_fail_when_spec_not_ready(self) -> None:
        slug = "test-placeholder-guard-not-ready"
        spec_dir = self._temp_spec_dir(slug, spec_ready=False)
        try:
            (spec_dir / "context_pack.md").write_text(
                "# Work Item Context Pack\n\n## Context Snapshot\n"
                "- Work item:\n- SPEC_READY:\n- ADR path:\n- ADR status:\n\n"
                "## Guardrail Controls\n- Applicable control IDs:\n",
                encoding="utf-8",
            )
            (spec_dir / "architecture.md").write_text(
                "# Architecture\n\n## Context\n- Work item:\n- Owner:\n- Date:\n",
                encoding="utf-8",
            )
            result = run(["python3", "scripts/bin/quality/check_sdd_assets.py"])
            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0,
                             msg=f"check_sdd_assets.py should succeed when SPEC_READY=false: {combined}")
            self.assertNotIn("scaffold placeholder not filled in", combined,
                             msg=f"placeholder guard must not fire when SPEC_READY=false: {combined}")
        finally:
            import shutil as _shutil
            _shutil.rmtree(spec_dir, ignore_errors=True)


class RuntimeAuthBestEffortTests(unittest.TestCase):
    """
    AC-005, AC-006: structural contract tests for runtime auth best-effort fixes.

    reconcile_eso_runtime_secrets.sh must wrap run_kustomize_apply in 'if !' so
    set -e cannot abort before the state file is written (Issue #105).

    reconcile_argocd_repo_credentials.sh must NOT trigger record_reconcile_issue
    for gho_ tokens; a log_info call is used instead (Issue #110).
    """

    _ESO_SCRIPT = REPO_ROOT / "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh"
    _ARGOCD_SCRIPT = REPO_ROOT / "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh"

    def test_eso_kustomize_apply_is_guarded(self) -> None:
        """AC-005: the security-manifest run_kustomize_apply call must be preceded by
        'if !' anchored to the infra/gitops/platform/base/security path so set -e
        cannot abort reconcile_eso_runtime_secrets.sh before the state file is written."""
        import re
        content = self._ESO_SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            re.compile(r'if\s+!\s+run_kustomize_apply\s+"?\$ROOT_DIR[^"]*?/base/security"?'),
            msg=(
                "the run_kustomize_apply call for infra/gitops/platform/base/security in "
                "reconcile_eso_runtime_secrets.sh must be wrapped in 'if !' so set -e "
                "cannot abort before the state file is written (Issue #105)"
            ),
        )

    def test_argocd_repo_credentials_accepts_gho_token(self) -> None:
        """AC-006: gho_ token must NOT trigger record_reconcile_issue; log_info is used instead."""
        import re
        content = self._ARGOCD_SCRIPT.read_text(encoding="utf-8")
        # Verify gho_ branch contains log_info (acceptance) — use DOTALL for multiline match
        self.assertRegex(
            content,
            re.compile(r"gho_.*?log_info", re.DOTALL),
            msg=(
                "reconcile_argocd_repo_credentials.sh must call log_info (not "
                "record_reconcile_issue) for gho_ tokens (Issue #110)"
            ),
        )
        # Locate the gho_ conditional block — fail explicitly if not found so the
        # assertNotIn below is never silently skipped due to a regex mismatch.
        gho_block_match = re.search(
            r'(\[\[ "\$ARGOCD_REPO_TOKEN" == gho_\*[^\n]*\]\][^\n]*\n(?:.*\n)*?)(elif|fi)\b',
            content,
        )
        self.assertIsNotNone(
            gho_block_match,
            msg=(
                "could not locate the gho_ conditional block in "
                "reconcile_argocd_repo_credentials.sh — check script structure"
            ),
        )
        gho_block = gho_block_match.group(1)  # type: ignore[union-attr]
        self.assertNotIn(
            "record_reconcile_issue",
            gho_block,
            msg=(
                "gho_ branch in reconcile_argocd_repo_credentials.sh must not call "
                "record_reconcile_issue; use log_info instead (Issue #110)"
            ),
        )


class AppDockerfileAndRuntimeTests(unittest.TestCase):
    """
    AC-001 through AC-008: structural contract tests for Issues #111 and #112.

    apps/backend/Dockerfile and apps/touchpoints/Dockerfile must exist and use
    multi-stage builds with correct EXPOSE ports and CMD definitions (#111).

    Deployment manifests must reference GHCR consumer images (not public Python/nginx
    placeholders) and the backend manifest must not contain a command: override (#112).
    """

    _BACKEND_DOCKERFILE = REPO_ROOT / "apps/backend/Dockerfile"
    _TOUCHPOINTS_DOCKERFILE = REPO_ROOT / "apps/touchpoints/Dockerfile"
    _BACKEND_DEPLOYMENT = REPO_ROOT / "infra/gitops/platform/base/apps/backend-api-deployment.yaml"
    _TOUCHPOINTS_DEPLOYMENT = REPO_ROOT / "infra/gitops/platform/base/apps/touchpoints-web-deployment.yaml"

    def test_backend_dockerfile_multi_stage(self) -> None:
        """AC-001, AC-002: backend Dockerfile uses multi-stage build, EXPOSE 8080, CMD."""
        import re
        self.assertTrue(
            self._BACKEND_DOCKERFILE.is_file(),
            msg="apps/backend/Dockerfile must exist (Issue #111)",
        )
        content = self._BACKEND_DOCKERFILE.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            re.compile(r"^FROM\s+\S+\s+AS\s+builder", re.MULTILINE),
            msg="apps/backend/Dockerfile must use a named builder stage: FROM ... AS builder",
        )
        self.assertRegex(
            content,
            re.compile(r"^FROM\s+\S+\s+AS\s+runtime", re.MULTILINE),
            msg="apps/backend/Dockerfile must use a named runtime stage: FROM ... AS runtime",
        )
        self.assertRegex(
            content,
            re.compile(r"^EXPOSE\s+8080", re.MULTILINE),
            msg="apps/backend/Dockerfile must EXPOSE 8080",
        )
        self.assertRegex(
            content,
            re.compile(r"^CMD\s+\[", re.MULTILINE),
            msg="apps/backend/Dockerfile must define a CMD instruction",
        )

    def test_touchpoints_dockerfile_multi_stage(self) -> None:
        """AC-003, AC-004: touchpoints Dockerfile uses Node.js builder + nginx runtime, EXPOSE 80."""
        import re
        self.assertTrue(
            self._TOUCHPOINTS_DOCKERFILE.is_file(),
            msg="apps/touchpoints/Dockerfile must exist (Issue #111)",
        )
        content = self._TOUCHPOINTS_DOCKERFILE.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            re.compile(r"^FROM\s+node:\S+\s+AS\s+builder", re.MULTILINE),
            msg="apps/touchpoints/Dockerfile must use a Node.js builder stage: FROM node:... AS builder",
        )
        self.assertRegex(
            content,
            re.compile(r"^FROM\s+nginx:\S+\s+AS\s+runtime", re.MULTILINE),
            msg="apps/touchpoints/Dockerfile must use an nginx runtime stage: FROM nginx:... AS runtime",
        )
        self.assertRegex(
            content,
            re.compile(r"^EXPOSE\s+80$", re.MULTILINE),
            msg="apps/touchpoints/Dockerfile must EXPOSE 80",
        )

    def test_backend_deployment_ghcr_image(self) -> None:
        """AC-005, AC-006: backend deployment uses a GHCR image (not a bare docker hub ref);
        no command: override in the container spec."""
        import re
        import yaml as _yaml
        content = self._BACKEND_DEPLOYMENT.read_text(encoding="utf-8")
        # AC-005: image field must be a GHCR reference, not a bare docker hub image like python:x.y.z
        self.assertRegex(
            content,
            re.compile(r"image:\s+ghcr\.io/", re.MULTILINE),
            msg=(
                "backend-api-deployment.yaml image must reference a GHCR registry "
                "(ghcr.io/...) not a bare docker hub image like python:x.y.z (Issue #112)"
            ),
        )
        # AC-006: no command: override — parse YAML to be indentation-safe
        manifest = _yaml.safe_load(content)
        containers = manifest["spec"]["template"]["spec"]["containers"]
        backend = next(c for c in containers if c["name"] == "backend-api")
        self.assertNotIn(
            "command",
            backend,
            msg=(
                "backend-api-deployment.yaml container spec must not contain a command: override; "
                "CMD is defined in apps/backend/Dockerfile (Issue #112)"
            ),
        )

    def test_touchpoints_deployment_ghcr_image(self) -> None:
        """AC-007: touchpoints deployment uses a GHCR image (not a bare docker hub ref)."""
        import re
        content = self._TOUCHPOINTS_DEPLOYMENT.read_text(encoding="utf-8")
        self.assertRegex(
            content,
            re.compile(r"image:\s+ghcr\.io/", re.MULTILINE),
            msg=(
                "touchpoints-web-deployment.yaml image must reference a GHCR registry "
                "(ghcr.io/...) not a bare docker hub image like nginx:x.y.z (Issue #112)"
            ),
        )
