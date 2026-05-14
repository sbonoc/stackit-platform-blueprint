"""Blueprint SDD bypass track regression tests.

AC-001: bypass path skips non-essential artifact checks for valid exception + authorized-by.
AC-002: no specs/ dir -> exit 0 (chore passive pass, regression guard).
AC-003: SPEC_READY:true + no exception -> all 10 artifacts still required (no regression).
AC-004: bypass path emits sdd_exception_gate_total metric line.
AC-005: exception set but no authorized-by -> violation raised.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT

_WORK_ITEM_SLUG = "2026-01-01-bypass-fixture"


def _load_checker():
    module_path = REPO_ROOT / "scripts/bin/quality/check_sdd_assets.py"
    spec = importlib.util.spec_from_file_location("quality_sdd_assets_checker_bypass", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load checker module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["quality_sdd_assets_checker_bypass"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _contract_raw() -> dict:
    return {
        "spec": {
            "spec_driven_development_contract": {
                "branch_contract": {
                    "dedicated_branch_required_by_default": True,
                    "explicit_opt_out_flag": "--no-create-branch",
                    "default_prefix": "codex/",
                    "branch_name_pattern": "<prefix><YYYY-MM-DD>-<work-item-slug>",
                    "enforce_non_default_branch": True,
                },
                "artifacts": {
                    "control_catalog_file": ".spec-kit/control-catalog.md",
                    "specs_workspace_readme": "specs/README.md",
                    "required_work_item_documents": [
                        "architecture.md",
                        "spec.md",
                        "plan.md",
                        "tasks.md",
                        "traceability.md",
                        "graph.json",
                        "evidence_manifest.json",
                        "context_pack.md",
                        "pr_context.md",
                        "hardening_review.md",
                    ],
                },
                "readiness_gate": {
                    "status_field": "SPEC_READY",
                    "required_value": "true",
                    "blocked_marker": "BLOCKED_MISSING_INPUTS",
                    "required_zero_fields": [
                        "Open questions count",
                        "Unresolved alternatives count",
                        "Unresolved TODO markers count",
                        "Pending assumptions count",
                        "Open clarification markers count",
                    ],
                    "required_signoffs": ["Product", "Architecture", "Security", "Operations"],
                    "adr_path_field": "ADR path",
                    "adr_status_field": "ADR status",
                    "adr_status_approved_values": ["approved"],
                    "adr_path_allowed_prefixes": ["docs/"],
                    "implementation_sections": ["Implementation"],
                    "clarification_marker_token": "NEEDS CLARIFICATION",
                    "acceptance_criteria_required": False,
                    "requirement_traceability_required": False,
                },
                "normative_language": {
                    "normative_heading_keyword": "Normative",
                    "informative_heading_keyword": "Informative",
                    "forbidden_ambiguous_terms_in_normative_sections": ["should", "may"],
                    "unresolved_marker_tokens": ["TBD", "TODO"],
                },
                "governance": {
                    "control_catalog": {
                        "id_pattern": "^SDD-C-[0-9]{3}$",
                        "required_columns": [
                            "Control ID",
                            "Normative Control",
                            "Applies In Phase(s)",
                            "Validation Command",
                            "Evidence Artifact(s)",
                            "Owner",
                            "Gate",
                        ],
                        "allowed_gate_values": ["fail", "warn"],
                    },
                    "spec_requirements": {
                        "control_section_heading_keyword": "Applicable Guardrail Controls",
                        "control_id_pattern": r"\bSDD-C-[0-9]{3}\b",
                        "stack_profile_section_heading_keyword": "Implementation Stack Profile",
                        "stack_profile_required_fields": [
                            "Backend stack profile",
                            "Frontend stack profile",
                            "Test automation profile",
                            "Agent execution model",
                            "Managed service preference",
                            "Managed service exception rationale",
                            "Runtime profile",
                            "Local Kubernetes context policy",
                            "Local provisioning stack",
                            "Runtime identity baseline",
                            "Local-first exception rationale",
                        ],
                        "stack_profile_allowed_agent_execution_models": [
                            "single-agent",
                            "specialized-subagents-isolated-worktrees",
                        ],
                        "managed_service_preference_allowed_values": [
                            "stackit-managed-first",
                            "explicit-consumer-exception",
                        ],
                        "runtime_profile_allowed_values": [
                            "local-first-docker-desktop-kubernetes",
                            "stackit-managed-runtime",
                        ],
                        "local_kube_context_policy_allowed_values": [
                            "docker-desktop-preferred",
                            "explicit-override-required",
                            "not-applicable-stackit-runtime",
                        ],
                        "local_provisioning_stack_allowed_values": [
                            "crossplane-plus-helm",
                            "terraform-plus-argocd",
                        ],
                        "runtime_identity_baseline_allowed_values": [
                            "eso-plus-argocd-plus-keycloak",
                            "custom-approved-exception",
                        ],
                    },
                    "app_onboarding_contract": {
                        "required_plan_section_keyword": "App Onboarding Contract",
                        "required_tasks_section_keyword": "App Onboarding Minimum Targets",
                        "required_make_targets": [
                            "apps-bootstrap",
                            "apps-smoke",
                            "backend-test-unit",
                            "backend-test-integration",
                            "backend-test-contracts",
                            "backend-test-e2e",
                            "touchpoints-test-unit",
                            "touchpoints-test-integration",
                            "touchpoints-test-contracts",
                            "touchpoints-test-e2e",
                            "test-unit-all",
                            "test-integration-all",
                            "test-contracts-all",
                            "test-e2e-all-local",
                            "infra-port-forward-start",
                            "infra-port-forward-stop",
                            "infra-port-forward-cleanup",
                        ],
                    },
                    "publish_contract": {
                        "required_pr_context_sections": [
                            "Summary",
                            "Requirement Coverage",
                            "Key Reviewer Files",
                            "Validation Evidence",
                            "Risk and Rollback",
                            "Deferred Proposals",
                        ],
                        "required_hardening_review_sections": [
                            "Repository-Wide Findings Fixed",
                            "Observability and Diagnostics Changes",
                            "Architecture and Code Quality Compliance",
                            "Proposals Only (Not Implemented)",
                        ],
                        "required_pr_template_headings": [
                            "Summary",
                            "Requirement and Contract Coverage",
                            "Key Reviewer Files",
                            "Validation Evidence",
                            "Risk and Rollback",
                            "Deferred Proposals (Not Implemented)",
                        ],
                        "required_pr_template_paths": [],
                    },
                    "blueprint_defect_escalation_contract": {
                        "required_spec_section_keyword": "Blueprint Upstream Defect Escalation",
                        "required_fields": [
                            "Upstream issue URL",
                            "Temporary workaround path",
                            "Replacement trigger",
                            "Workaround review date",
                        ],
                    },
                },
            }
        }
    }


def _write_control_catalog(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# SDD Control Catalog\n\n"
        "| Control ID | Normative Control | Applies In Phase(s) | Validation Command | Evidence Artifact(s) | Owner | Gate |\n"
        "|---|---|---|---|---|---|---|\n"
        "| SDD-C-001 | Requirement MUST be deterministic. | Discover, Specify | make quality-sdd-check | specs/<work-item>/spec.md | Architecture | fail |\n",
        encoding="utf-8",
    )


def _bypass_spec_md(*, exception_type: str = "upgrade", authorized_by: str = "testuser") -> str:
    lines = [
        "# Specification",
        "",
        "## Spec Readiness Gate (Blocking)",
        "- SPEC_READY: false",
        "- SPEC_PRODUCT_READY: false",
        "- Open questions count: 0",
        "- Unresolved alternatives count: 0",
        "- Unresolved TODO markers count: 0",
        "- Pending assumptions count: 0",
        "- Open clarification markers count: 0",
        "- Product sign-off: pending",
        "- Architecture sign-off: pending",
        "- Security sign-off: pending",
        "- Operations sign-off: pending",
        "- Missing input blocker token: none",
        "- ADR path: docs/example-adr.md",
        "- ADR status: proposed",
        f"- SPEC_READY_EXCEPTION: {exception_type}",
        f"- authorized-by: {authorized_by}",
        "",
        "## Applicable Guardrail Controls (Normative)",
        "- Applicable control IDs: SDD-C-001",
        "- Control exception rationale: none",
        "",
        "## Implementation Stack Profile (Normative)",
        "- Backend stack profile: none",
        "- Frontend stack profile: none",
        "- Test automation profile: pytest",
        "- Agent execution model: single-agent",
        "- Managed service preference: explicit-consumer-exception",
        "- Managed service exception rationale: tooling only",
        "- Runtime profile: local-first-docker-desktop-kubernetes",
        "- Local Kubernetes context policy: docker-desktop-preferred",
        "- Local provisioning stack: crossplane-plus-helm",
        "- Runtime identity baseline: custom-approved-exception",
        "- Local-first exception rationale: tooling only",
        "",
        "## Normative Requirements",
        "### Functional Requirements (Normative)",
        "- FR-001 MUST define behavior.",
        "",
        "## Informative Notes (Non-Normative)",
        "- Context: test fixture.",
    ]
    return "\n".join(lines) + "\n"


def _exception_set_no_authorized_by_spec_md() -> str:
    lines = [
        "# Specification",
        "",
        "## Spec Readiness Gate (Blocking)",
        "- SPEC_READY: false",
        "- SPEC_PRODUCT_READY: false",
        "- Open questions count: 0",
        "- Unresolved alternatives count: 0",
        "- Unresolved TODO markers count: 0",
        "- Pending assumptions count: 0",
        "- Open clarification markers count: 0",
        "- Product sign-off: pending",
        "- Architecture sign-off: pending",
        "- Security sign-off: pending",
        "- Operations sign-off: pending",
        "- Missing input blocker token: none",
        "- ADR path: docs/example-adr.md",
        "- ADR status: proposed",
        "- SPEC_READY_EXCEPTION: bug-fix",
        "- authorized-by: none",
        "",
        "## Applicable Guardrail Controls (Normative)",
        "- Applicable control IDs: SDD-C-001",
        "- Control exception rationale: none",
        "",
        "## Implementation Stack Profile (Normative)",
        "- Backend stack profile: none",
        "- Frontend stack profile: none",
        "- Test automation profile: pytest",
        "- Agent execution model: single-agent",
        "- Managed service preference: explicit-consumer-exception",
        "- Managed service exception rationale: tooling only",
        "- Runtime profile: local-first-docker-desktop-kubernetes",
        "- Local Kubernetes context policy: docker-desktop-preferred",
        "- Local provisioning stack: crossplane-plus-helm",
        "- Runtime identity baseline: custom-approved-exception",
        "- Local-first exception rationale: tooling only",
        "",
        "## Normative Requirements",
        "### Functional Requirements (Normative)",
        "- FR-001 MUST define behavior.",
        "",
        "## Informative Notes (Non-Normative)",
        "- Context: test fixture.",
    ]
    return "\n".join(lines) + "\n"


def _full_sdd_spec_md() -> str:
    lines = [
        "# Specification",
        "",
        "## Spec Readiness Gate (Blocking)",
        "- SPEC_READY: true",
        "- SPEC_PRODUCT_READY: true",
        "- Open questions count: 0",
        "- Unresolved alternatives count: 0",
        "- Unresolved TODO markers count: 0",
        "- Pending assumptions count: 0",
        "- Open clarification markers count: 0",
        "- Product sign-off: approved",
        "- Architecture sign-off: approved",
        "- Security sign-off: approved",
        "- Operations sign-off: approved",
        "- Missing input blocker token: none",
        "- ADR path: docs/example-adr.md",
        "- ADR status: approved",
        "",
        "## Applicable Guardrail Controls (Normative)",
        "- Applicable control IDs: SDD-C-001",
        "- Control exception rationale: none",
        "",
        "## Implementation Stack Profile (Normative)",
        "- Backend stack profile: none",
        "- Frontend stack profile: none",
        "- Test automation profile: pytest",
        "- Agent execution model: single-agent",
        "- Managed service preference: explicit-consumer-exception",
        "- Managed service exception rationale: tooling only",
        "- Runtime profile: local-first-docker-desktop-kubernetes",
        "- Local Kubernetes context policy: docker-desktop-preferred",
        "- Local provisioning stack: crossplane-plus-helm",
        "- Runtime identity baseline: custom-approved-exception",
        "- Local-first exception rationale: tooling only",
        "",
        "## Normative Requirements",
        "### Functional Requirements (Normative)",
        "- FR-001 MUST define behavior.",
        "",
        "## Informative Notes (Non-Normative)",
        "- Context: test fixture.",
    ]
    return "\n".join(lines) + "\n"


class SddBypassTrackTests(unittest.TestCase):
    def test_bypass_path_skips_artifact_checks(self) -> None:
        """AC-001: bypass path skips non-essential artifact checks."""
        checker = _load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            work_item = repo_root / "specs" / _WORK_ITEM_SLUG
            work_item.mkdir(parents=True, exist_ok=True)
            (repo_root / "specs" / "README.md").write_text("# Specs\n", encoding="utf-8")
            (work_item / "spec.md").write_text(
                _bypass_spec_md(exception_type="upgrade", authorized_by="testuser"),
                encoding="utf-8",
            )
            (work_item / "pr_context.md").write_text("# PR Context\n", encoding="utf-8")

            contract_raw = _contract_raw()
            _, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)

            missing_doc_violations = [
                v for v in violations if "missing required SDD work-item document" in v.message
            ]
            self.assertEqual(
                missing_doc_violations,
                [],
                msg=f"expected no missing-doc violations on bypass path, got: {missing_doc_violations}",
            )

    def test_no_specs_dir_exits_zero(self) -> None:
        """AC-002: no specs/ dir -> exit 0 (chore passive pass, regression guard)."""
        checker = _load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_control_catalog(repo_root / ".spec-kit/control-catalog.md")

            contract_raw = _contract_raw()
            _, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)

            self.assertEqual(violations, [], msg=f"expected no violations when no specs/ dir exists, got: {violations}")

    def test_full_sdd_path_unaffected(self) -> None:
        """AC-003: SPEC_READY:true + no exception -> all 10 artifacts still required."""
        checker = _load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            work_item = repo_root / "specs" / _WORK_ITEM_SLUG
            work_item.mkdir(parents=True, exist_ok=True)
            (repo_root / "specs" / "README.md").write_text("# Specs\n", encoding="utf-8")
            (work_item / "spec.md").write_text(_full_sdd_spec_md(), encoding="utf-8")

            contract_raw = _contract_raw()
            _, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)

            missing_doc_violations = [
                v for v in violations if "missing required SDD work-item document" in v.message
            ]
            self.assertGreater(
                len(missing_doc_violations),
                0,
                msg="expected missing-doc violations for full-SDD spec missing 9 artifacts",
            )

    def test_metric_emitted_on_bypass_path(self) -> None:
        """AC-004: bypass path emits sdd_exception_gate_total metric line."""
        checker = _load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            work_item = repo_root / "specs" / _WORK_ITEM_SLUG
            work_item.mkdir(parents=True, exist_ok=True)
            (repo_root / "specs" / "README.md").write_text("# Specs\n", encoding="utf-8")
            (work_item / "spec.md").write_text(
                _bypass_spec_md(exception_type="bug-fix", authorized_by="testuser"),
                encoding="utf-8",
            )
            (work_item / "pr_context.md").write_text("# PR Context\n", encoding="utf-8")

            contract_raw = _contract_raw()
            _, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)

            captured = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = captured
            try:
                checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            finally:
                sys.stdout = old_stdout

            output = captured.getvalue()
            self.assertIn(
                "name=sdd_exception_gate_total",
                output,
                msg=f"expected sdd_exception_gate_total metric in stdout, got: {output!r}",
            )

    def test_missing_authorized_by_raises_violation(self) -> None:
        """AC-005: exception set but authorized-by absent/none -> violation raised."""
        checker = _load_checker()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            work_item = repo_root / "specs" / _WORK_ITEM_SLUG
            work_item.mkdir(parents=True, exist_ok=True)
            (repo_root / "specs" / "README.md").write_text("# Specs\n", encoding="utf-8")
            (work_item / "spec.md").write_text(
                _exception_set_no_authorized_by_spec_md(),
                encoding="utf-8",
            )
            (work_item / "pr_context.md").write_text("# PR Context\n", encoding="utf-8")

            contract_raw = _contract_raw()
            _, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)

            self.assertTrue(
                any("authorized-by" in v.message for v in violations),
                msg=f"expected authorized-by violation, got: {[v.message for v in violations]}",
            )


if __name__ == "__main__":
    unittest.main()
