from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from tests._shared.helpers import REPO_ROOT


def _load_checker_module():
    module_path = REPO_ROOT / "scripts/bin/quality/check_sdd_assets.py"
    spec = importlib.util.spec_from_file_location("quality_sdd_assets_checker", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load checker module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _contract_raw(*, catalog_file: str = ".spec-kit/control-catalog.md") -> dict:
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
                    "control_catalog_file": catalog_file,
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
                    "required_signoffs": [
                        "Product",
                        "Architecture",
                        "Security",
                        "Operations",
                    ],
                    "adr_path_field": "ADR path",
                    "adr_status_field": "ADR status",
                    "adr_status_approved_values": ["approved"],
                    "adr_path_allowed_prefixes": [
                        "docs/blueprint/architecture/decisions/",
                        "docs/platform/architecture/decisions/",
                    ],
                    "implementation_sections": ["Implementation", "Build"],
                    "clarification_marker_token": "NEEDS CLARIFICATION",
                    "acceptance_criteria_required": True,
                    "requirement_traceability_required": True,
                },
                "normative_language": {
                    "normative_heading_keyword": "Normative",
                    "informative_heading_keyword": "Informative",
                    "forbidden_ambiguous_terms_in_normative_sections": [
                        "should",
                        "may",
                        "could",
                        "might",
                        "either",
                        "and/or",
                        "as needed",
                        "approximately",
                        "etc.",
                    ],
                    "unresolved_marker_tokens": ["TBD", "TBC", "TODO", "FIXME", "???"],
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


def _write_valid_control_catalog(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# SDD Control Catalog",
                "",
                "| Control ID | Normative Control | Applies In Phase(s) | Validation Command | Evidence Artifact(s) | Owner | Gate |",
                "|---|---|---|---|---|---|---|",
                "| SDD-C-001 | Requirement MUST be deterministic. | Discover, Specify | make quality-sdd-check | specs/<work-item>/spec.md | Architecture | fail |",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_work_item(repo_root: Path, *, control_id: str = "SDD-C-001", include_frontend_profile: bool = True) -> None:
    specs_root = repo_root / "specs"
    specs_root.mkdir(parents=True, exist_ok=True)
    (specs_root / "README.md").write_text("# Specs\n", encoding="utf-8")
    work_item = specs_root / "2026-04-15-fixture"
    work_item.mkdir(parents=True, exist_ok=True)

    (work_item / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (work_item / "plan.md").write_text(
        "\n".join(
            [
                "# Plan",
                "## App Onboarding Contract (Normative)",
                "- Required minimum make targets:",
                "  - `apps-bootstrap`",
                "  - `apps-smoke`",
                "  - `backend-test-unit`",
                "  - `backend-test-integration`",
                "  - `backend-test-contracts`",
                "  - `backend-test-e2e`",
                "  - `touchpoints-test-unit`",
                "  - `touchpoints-test-integration`",
                "  - `touchpoints-test-contracts`",
                "  - `touchpoints-test-e2e`",
                "  - `test-unit-all`",
                "  - `test-integration-all`",
                "  - `test-contracts-all`",
                "  - `test-e2e-all-local`",
                "  - `infra-port-forward-start`",
                "  - `infra-port-forward-stop`",
                "  - `infra-port-forward-cleanup`",
                "## Risk and Rollback (Normative)",
                "- Risk: runtime drift can break generated-consumer onboarding.",
                "- Rollback: revert SDD contract and template updates together.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "tasks.md").write_text(
        "\n".join(
            [
                "# Tasks",
                "## Gate Checks",
                "- [ ] G-001 Confirm `SPEC_READY=true` in `spec.md`",
                "## Implementation",
                "- [ ] T-001 Implement behavior",
                "## App Onboarding Minimum Targets (Normative)",
                "- [ ] A-001 `apps-bootstrap` and `apps-smoke` are available",
                "- [ ] A-002 `backend-test-unit`, `backend-test-integration`, `backend-test-contracts`, `backend-test-e2e` are available",
                "- [ ] A-003 `touchpoints-test-unit`, `touchpoints-test-integration`, `touchpoints-test-contracts`, `touchpoints-test-e2e` are available",
                "- [ ] A-004 `test-unit-all`, `test-integration-all`, `test-contracts-all`, `test-e2e-all-local` are available",
                "- [ ] A-005 `infra-port-forward-start`, `infra-port-forward-stop`, `infra-port-forward-cleanup` are available",
            ]
        ),
        encoding="utf-8",
    )
    (work_item / "traceability.md").write_text(
        "\n".join(
            [
                "# Traceability",
                "| Requirement | Control IDs | Implementation | Tests | Documentation Evidence | Operational Evidence |",
                "|---|---|---|---|---|---|",
                "| FR-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
                "| NFR-SEC-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
                "| NFR-OBS-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
                "| NFR-REL-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
                "| NFR-OPS-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
                "| AC-001 | SDD-C-001 | scripts/example.py | tests/example_test.py | docs/example.md | artifacts/example.json |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "graph.json").write_text(
        "\n".join(
            [
                "{",
                '  "graph_version": 1,',
                '  "work_item": "2026-04-15-fixture",',
                '  "nodes": [',
                '    {"id": "FR-001", "type": "requirement"},',
                '    {"id": "NFR-SEC-001", "type": "requirement"},',
                '    {"id": "NFR-OBS-001", "type": "requirement"},',
                '    {"id": "NFR-REL-001", "type": "requirement"},',
                '    {"id": "NFR-OPS-001", "type": "requirement"},',
                '    {"id": "AC-001", "type": "acceptance"}',
                "  ],",
                '  "edges": [',
                '    {"from": "FR-001", "to": "AC-001", "relation": "validated_by"},',
                '    {"from": "NFR-SEC-001", "to": "AC-001", "relation": "constrains"},',
                '    {"from": "NFR-OBS-001", "to": "AC-001", "relation": "constrains"},',
                '    {"from": "NFR-REL-001", "to": "AC-001", "relation": "constrains"},',
                '    {"from": "NFR-OPS-001", "to": "AC-001", "relation": "constrains"}',
                "  ]",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "evidence_manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "work_item": "specs/2026-04-15-fixture",
                "generated_by": "spec-evidence-manifest",
                "generated_at_utc": "",
                "files": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "context_pack.md").write_text(
        "\n".join(
            [
                "# Work Item Context Pack",
                "",
                "## Context Snapshot",
                "- Work item: specs/2026-04-15-fixture",
                "",
                "## Required Commands",
                "- `make quality-sdd-check`",
                "- `make quality-hardening-review`",
                "- `make spec-pr-context`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "pr_context.md").write_text(
        "\n".join(
            [
                "# PR Context",
                "",
                "## Summary",
                "- Scope: fixture",
                "",
                "## Requirement Coverage",
                "- FR-001 / AC-001",
                "",
                "## Key Reviewer Files",
                "- specs/2026-04-15-fixture/spec.md",
                "",
                "## Validation Evidence",
                "- make quality-sdd-check",
                "",
                "## Risk and Rollback",
                "- Risk: fixture",
                "- Rollback: fixture",
                "",
                "## Deferred Proposals",
                "- none",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (work_item / "hardening_review.md").write_text(
        "\n".join(
            [
                "# Hardening Review",
                "",
                "## Repository-Wide Findings Fixed",
                "- none",
                "",
                "## Observability and Diagnostics Changes",
                "- none",
                "",
                "## Architecture and Code Quality Compliance",
                "- no boundary violations detected",
                "",
                "## Proposals Only (Not Implemented)",
                "- none",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    stack_profile_lines = [
        "- Backend stack profile: python_plus_fastapi_pydantic_v2",
        "- Test automation profile: pytest_vitest_playwright_pact",
        "- Agent execution model: single-agent",
        "- Managed service preference: stackit-managed-first",
        "- Managed service exception rationale: none",
        "- Runtime profile: local-first-docker-desktop-kubernetes",
        "- Local Kubernetes context policy: docker-desktop-preferred",
        "- Local provisioning stack: crossplane-plus-helm",
        "- Runtime identity baseline: eso-plus-argocd-plus-keycloak",
        "- Local-first exception rationale: none",
    ]
    if include_frontend_profile:
        stack_profile_lines.insert(1, "- Frontend stack profile: vue_router_pinia_onyx")

    spec_lines = [
        "# Specification",
        "",
        "## Spec Readiness Gate (Blocking)",
        "- SPEC_READY: false",
        "- Open questions count: 0",
        "- Unresolved alternatives count: 0",
        "- Unresolved TODO markers count: 0",
        "- Pending assumptions count: 0",
        "- Open clarification markers count: 0",
        "- Product sign-off: pending",
        "- Architecture sign-off: pending",
        "- Security sign-off: pending",
        "- Operations sign-off: pending",
        "- Missing input blocker token: BLOCKED_MISSING_INPUTS",
        "- ADR path:",
        "- ADR status: proposed",
        "",
        "## Applicable Guardrail Controls (Normative)",
        f"- Applicable control IDs: {control_id}",
        "",
        "## Implementation Stack Profile (Normative)",
        *stack_profile_lines,
        "",
        "## Blueprint Upstream Defect Escalation (Normative)",
        "- Upstream issue URL: https://github.com/example/stackit-platform-blueprint/issues/999",
        "- Temporary workaround path: scripts/bin/quality/check_sdd_assets.py",
        "- Replacement trigger: upstream fix merged and released",
        "- Workaround review date: 2026-04-20",
        "",
        "## Normative Requirements",
        "### Functional Requirements (Normative)",
        "- FR-001 MUST define one deterministic behavior.",
        "### Non-Functional Requirements (Normative)",
        "- NFR-SEC-001 MUST define enforceable security behavior.",
        "- NFR-OBS-001 MUST define logs, metrics, and traces expectations.",
        "- NFR-REL-001 MUST define resilience and rollback behavior.",
        "- NFR-OPS-001 MUST define operability and diagnostics behavior.",
        "## Normative Acceptance Criteria",
        "- AC-001 MUST be objectively testable.",
        "",
        "## Informative Notes (Non-Normative)",
        "- Context: fixture content.",
    ]
    (work_item / "spec.md").write_text("\n".join(spec_lines) + "\n", encoding="utf-8")


class SddAssetCheckerTests(unittest.TestCase):
    def test_valid_fixture_passes_control_and_spec_checks(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root)

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])
            self.assertEqual(catalog_ids, {"SDD-C-001"})

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertEqual(spec_violations, [])

    def test_invalid_catalog_table_shape_is_rejected(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            broken_catalog = repo_root / ".spec-kit/control-catalog.md"
            broken_catalog.parent.mkdir(parents=True, exist_ok=True)
            broken_catalog.write_text(
                "\n".join(
                    [
                        "# SDD Control Catalog",
                        "",
                        "| Control ID | Normative Control | Applies In Phase(s) | Validation Command | Evidence Artifact(s) | Owner |",
                        "|---|---|---|---|---|---|",
                        "| SDD-C-001 | Requirement MUST be deterministic. | Discover | make quality-sdd-check | specs/<work-item>/spec.md | Architecture |",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            _write_work_item(repo_root)

            contract_raw = _contract_raw()
            violations, _ = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertTrue(
                any("missing required columns" in violation.message for violation in violations),
                msg=[violation.message for violation in violations],
            )

    def test_unknown_control_id_in_spec_is_rejected(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root, control_id="SDD-C-999")

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertTrue(
                any("unknown control ID" in violation.message for violation in spec_violations),
                msg=[violation.message for violation in spec_violations],
            )

    def test_missing_stack_profile_field_is_rejected(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root, include_frontend_profile=False)

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertTrue(
                any("missing stack profile field: Frontend stack profile" in violation.message for violation in spec_violations),
                msg=[violation.message for violation in spec_violations],
            )

    def test_managed_service_exception_requires_explicit_rationale(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root)
            spec_path = repo_root / "specs/2026-04-15-fixture/spec.md"
            spec_content = spec_path.read_text(encoding="utf-8")
            spec_content = spec_content.replace(
                "- Managed service preference: stackit-managed-first",
                "- Managed service preference: explicit-consumer-exception",
            ).replace(
                "- Managed service exception rationale: none",
                "- Managed service exception rationale: none",
            )
            spec_path.write_text(spec_content, encoding="utf-8")

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertTrue(
                any(
                    "managed service exception rationale must be explicitly set" in violation.message
                    for violation in spec_violations
                ),
                msg=[violation.message for violation in spec_violations],
            )

    def test_missing_app_onboarding_plan_section_is_rejected(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root)
            (repo_root / "specs/2026-04-15-fixture/plan.md").write_text("# Plan\n", encoding="utf-8")

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertTrue(
                any("App Onboarding Contract" in violation.message for violation in spec_violations),
                msg=[violation.message for violation in spec_violations],
            )

    def test_graph_requirement_drift_is_rejected(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root)

            graph_path = repo_root / "specs/2026-04-15-fixture/graph.json"
            graph_content = graph_path.read_text(encoding="utf-8")
            graph_content = graph_content.replace('"id": "FR-001"', '"id": "FR-999"', 1)
            graph_path.write_text(graph_content, encoding="utf-8")

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertTrue(
                any("graph.json missing requirement/acceptance node ID from spec.md" in violation.message for violation in spec_violations),
                msg=[violation.message for violation in spec_violations],
            )

    def test_spec_ready_true_ignores_readiness_field_marker_labels(self) -> None:
        checker = _load_checker_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _write_valid_control_catalog(repo_root / ".spec-kit/control-catalog.md")
            _write_work_item(repo_root)

            adr_relative_path = "docs/blueprint/architecture/decisions/ADR-20260415-fixture.md"
            adr_path = repo_root / adr_relative_path
            adr_path.parent.mkdir(parents=True, exist_ok=True)
            adr_path.write_text("# ADR fixture\n", encoding="utf-8")

            spec_path = repo_root / "specs/2026-04-15-fixture/spec.md"
            spec_content = spec_path.read_text(encoding="utf-8")
            spec_content = spec_content.replace("- SPEC_READY: false", "- SPEC_READY: true")
            spec_content = spec_content.replace("- Product sign-off: pending", "- Product sign-off: approved")
            spec_content = spec_content.replace(
                "- Architecture sign-off: pending",
                "- Architecture sign-off: approved",
            )
            spec_content = spec_content.replace("- Security sign-off: pending", "- Security sign-off: approved")
            spec_content = spec_content.replace("- Operations sign-off: pending", "- Operations sign-off: approved")
            spec_content = spec_content.replace(
                "- Missing input blocker token: BLOCKED_MISSING_INPUTS",
                "- Missing input blocker token: none",
            )
            spec_content = spec_content.replace("- ADR path:", f"- ADR path: {adr_relative_path}")
            spec_content = spec_content.replace("- ADR status: proposed", "- ADR status: approved")
            spec_path.write_text(spec_content, encoding="utf-8")

            contract_raw = _contract_raw()
            catalog_violations, catalog_ids = checker._load_control_catalog(contract_raw=contract_raw, repo_root=repo_root)
            self.assertEqual(catalog_violations, [])

            spec_violations = checker._validate_work_item_specs(contract_raw, repo_root, catalog_ids)
            self.assertEqual(spec_violations, [], msg=[violation.message for violation in spec_violations])


if __name__ == "__main__":
    unittest.main()
