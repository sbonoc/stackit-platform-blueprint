#!/usr/bin/env python3
"""Validate Spec-Driven Development assets, readiness gates, and language policy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


APPROVED_SIGNOFF_VALUES = {"approved", "true", "yes", "done", "signed"}


@dataclass(frozen=True)
class Violation:
    path: str
    message: str


@dataclass(frozen=True)
class MarkdownSection:
    title: str
    level: int
    content: str


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _contains_in_order(content: str, phrases: list[str]) -> bool:
    cursor = 0
    normalized = content.lower()
    for phrase in phrases:
        pos = normalized.find(phrase.lower(), cursor)
        if pos < 0:
            return False
        cursor = pos + len(phrase)
    return True


def _template_doc_path(template_root: Path, doc_name: str) -> Path | None:
    direct = template_root / doc_name
    if direct.is_file():
        return direct
    tmpl = template_root / f"{doc_name}.tmpl"
    if tmpl.is_file():
        return tmpl
    return None


def _split_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    inner = stripped.strip("|")
    cells = re.split(r"(?<!\\)\|", inner)
    return [cell.strip().replace("\\|", "|") for cell in cells]


def _is_markdown_table_delimiter(line: str) -> bool:
    cells = _split_table_cells(line)
    if not cells:
        return False
    return all(bool(re.fullmatch(r":?-{3,}:?", cell)) for cell in cells)


def _extract_first_markdown_table(content: str) -> tuple[list[str], list[list[str]]]:
    lines = content.splitlines()
    for idx in range(len(lines) - 1):
        header_cells = _split_table_cells(lines[idx])
        if not header_cells:
            continue
        if not _is_markdown_table_delimiter(lines[idx + 1]):
            continue

        rows: list[list[str]] = []
        cursor = idx + 2
        while cursor < len(lines):
            row_cells = _split_table_cells(lines[cursor])
            if not row_cells:
                break
            rows.append(row_cells)
            cursor += 1
        return header_cells, rows
    return [], []


def _split_markdown_sections(content: str) -> list[MarkdownSection]:
    sections: list[MarkdownSection] = []
    current_title = "(root)"
    current_level = 0
    buffer: list[str] = []

    for line in content.splitlines():
        header_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if header_match:
            sections.append(
                MarkdownSection(
                    title=current_title,
                    level=current_level,
                    content="\n".join(buffer).strip(),
                )
            )
            current_title = header_match.group(2).strip()
            current_level = len(header_match.group(1))
            buffer = []
            continue
        buffer.append(line)

    sections.append(
        MarkdownSection(
            title=current_title,
            level=current_level,
            content="\n".join(buffer).strip(),
        )
    )
    return sections


def _parse_bullet_kv(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content.splitlines():
        match = re.match(r"^\s*-\s*([^:]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        values[key] = value
    return values


def _parse_non_negative_int(value: str) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    if match is None:
        return None
    return int(match.group(0))


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_regex_text(value: str) -> str:
    # Contract values are parsed with a lightweight YAML reader that preserves backslashes.
    # Normalize double-escaped regex literals (for example "\\b") before compilation.
    return value.replace("\\\\", "\\")


def _load_json_or_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="surrogateescape")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ValueError(
                f"{path.relative_to(REPO_ROOT)} must be JSON-compatible when PyYAML is unavailable"
            ) from exc
        payload = yaml.safe_load(raw)

    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(REPO_ROOT)} must be a mapping")
    return payload


def _contains_term(content: str, term: str) -> bool:
    normalized = content.lower()
    needle = term.lower()
    if not needle:
        return False
    if re.search(r"[a-z0-9]", needle) and " " not in needle and re.fullmatch(r"[a-z0-9.-]+", needle):
        pattern = re.compile(rf"\b{re.escape(needle)}\b")
        return pattern.search(normalized) is not None
    return needle in normalized


def _checked_tasks_in_sections(tasks_content: str, section_keywords: list[str]) -> bool:
    if not section_keywords:
        section_keywords = ["implementation", "build"]

    lowered_keywords = [item.lower() for item in section_keywords]
    sections = _split_markdown_sections(tasks_content)
    checked_pattern = re.compile(r"^\s*-\s*\[[xX]\]\s+")

    for section in sections:
        section_name = section.title.lower()
        if not any(keyword in section_name for keyword in lowered_keywords):
            continue
        for line in section.content.splitlines():
            if checked_pattern.match(line):
                return True
    return False


def _section_contains_all_targets(section_content: str, required_targets: list[str]) -> list[str]:
    missing: list[str] = []
    lowered = section_content.lower()
    for target in required_targets:
        if target.lower() not in lowered:
            missing.append(target)
    return missing


def _strip_readiness_gate_labels_for_marker_scan(
    aggregate_content: str,
    *,
    readiness_field_names: list[str],
) -> str:
    sanitized = aggregate_content
    for field_name in readiness_field_names:
        if not field_name:
            continue
        sanitized = re.sub(
            rf"^\s*[-*]\s+{re.escape(field_name)}\s*:\s*.*$",
            "",
            sanitized,
            flags=re.IGNORECASE | re.MULTILINE,
        )
    return sanitized


def _work_item_dirs(specs_root: Path) -> list[Path]:
    if not specs_root.is_dir():
        return []
    candidates = []
    for path in sorted(specs_root.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        candidates.append(path)
    return candidates


def _load_control_catalog(
    *,
    contract_raw: dict[str, Any],
    repo_root: Path,
) -> tuple[list[Violation], set[str]]:
    violations: list[Violation] = []
    discovered_ids: set[str] = set()

    spec_raw = _as_mapping(contract_raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    artifacts_raw = _as_mapping(sdd_raw.get("artifacts"))
    governance_raw = _as_mapping(sdd_raw.get("governance"))
    control_catalog_raw = _as_mapping(governance_raw.get("control_catalog"))

    catalog_file = str(artifacts_raw.get("control_catalog_file", "")).strip()
    id_pattern_text = str(control_catalog_raw.get("id_pattern", "")).strip()
    required_columns = _as_list_of_str(control_catalog_raw.get("required_columns"))
    allowed_gate_values = {value.strip().lower() for value in _as_list_of_str(control_catalog_raw.get("allowed_gate_values"))}

    if not catalog_file:
        violations.append(
            Violation(path="blueprint/contract.yaml", message="artifacts.control_catalog_file must be set")
        )
        return violations, discovered_ids

    catalog_path = repo_root / catalog_file
    if not catalog_path.is_file():
        violations.append(Violation(path=catalog_file, message="control catalog file is missing"))
        return violations, discovered_ids

    if not id_pattern_text:
        violations.append(
            Violation(path="blueprint/contract.yaml", message="governance.control_catalog.id_pattern must be set")
        )
        return violations, discovered_ids

    try:
        id_pattern = re.compile(id_pattern_text)
    except re.error as exc:
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message=f"governance.control_catalog.id_pattern is invalid regex: {exc}",
            )
        )
        return violations, discovered_ids

    content = catalog_path.read_text(encoding="utf-8", errors="surrogateescape")
    header, rows = _extract_first_markdown_table(content)
    if not header:
        violations.append(Violation(path=catalog_file, message="control catalog must include a markdown table"))
        return violations, discovered_ids

    missing_columns = [column for column in required_columns if column not in header]
    if missing_columns:
        violations.append(
            Violation(
                path=catalog_file,
                message=f"control catalog table missing required columns: {', '.join(missing_columns)}",
            )
        )
        return violations, discovered_ids

    id_col = header.index("Control ID") if "Control ID" in header else -1
    gate_col = header.index("Gate") if "Gate" in header else -1
    for row_index, row in enumerate(rows, start=1):
        if len(row) < len(header):
            violations.append(
                Violation(
                    path=catalog_file,
                    message=f"control catalog row {row_index} has fewer columns than header",
                )
            )
            continue

        control_id = row[id_col].strip() if id_col >= 0 else ""
        if not control_id:
            continue
        if id_pattern.fullmatch(control_id) is None:
            violations.append(
                Violation(
                    path=catalog_file,
                    message=f"control catalog row {row_index} has invalid control ID: {control_id}",
                )
            )
            continue
        if control_id in discovered_ids:
            violations.append(
                Violation(
                    path=catalog_file,
                    message=f"control catalog has duplicate control ID: {control_id}",
                )
            )
            continue
        discovered_ids.add(control_id)

        if gate_col >= 0 and allowed_gate_values:
            gate_value = row[gate_col].strip().lower()
            if gate_value and gate_value not in allowed_gate_values:
                violations.append(
                    Violation(
                        path=catalog_file,
                        message=(
                            f"control catalog row {row_index} has unsupported gate value: {row[gate_col].strip()}"
                        ),
                    )
                )

    if not discovered_ids:
        violations.append(Violation(path=catalog_file, message="control catalog must define at least one control ID"))

    return violations, discovered_ids


def _find_section(sections: list[MarkdownSection], keyword: str) -> MarkdownSection | None:
    lowered = keyword.lower().strip()
    for section in sections:
        if lowered in section.title.lower():
            return section
    return None


def _validate_work_item_specs(
    contract_raw: dict[str, Any],
    repo_root: Path,
    catalog_control_ids: set[str],
) -> list[Violation]:
    violations: list[Violation] = []
    spec_raw = _as_mapping(contract_raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    if not sdd_raw:
        return violations

    artifacts_raw = _as_mapping(sdd_raw.get("artifacts"))
    required_documents = _as_list_of_str(artifacts_raw.get("required_work_item_documents"))
    specs_readme = artifacts_raw.get("specs_workspace_readme", "specs/README.md")
    specs_workspace = Path(str(specs_readme)).parent
    work_items = _work_item_dirs(repo_root / specs_workspace)

    readiness_raw = _as_mapping(sdd_raw.get("readiness_gate"))
    status_field = str(readiness_raw.get("status_field", "SPEC_READY")).strip()
    required_value = str(readiness_raw.get("required_value", "true")).strip().lower()
    blocked_marker = str(readiness_raw.get("blocked_marker", "BLOCKED_MISSING_INPUTS")).strip()
    required_zero_fields = _as_list_of_str(readiness_raw.get("required_zero_fields"))
    required_signoffs = _as_list_of_str(readiness_raw.get("required_signoffs"))
    implementation_sections = _as_list_of_str(readiness_raw.get("implementation_sections"))
    adr_path_field = str(readiness_raw.get("adr_path_field", "ADR path")).strip()
    adr_status_field = str(readiness_raw.get("adr_status_field", "ADR status")).strip()
    adr_status_approved_values = {
        value.strip().lower()
        for value in _as_list_of_str(readiness_raw.get("adr_status_approved_values"))
        if value.strip()
    }
    if not adr_status_approved_values:
        adr_status_approved_values = {"approved"}
    adr_path_allowed_prefixes = _as_list_of_str(readiness_raw.get("adr_path_allowed_prefixes"))
    acceptance_criteria_required = bool(readiness_raw.get("acceptance_criteria_required", False))
    requirement_traceability_required = bool(readiness_raw.get("requirement_traceability_required", False))

    normative_raw = _as_mapping(sdd_raw.get("normative_language"))
    normative_keyword = str(normative_raw.get("normative_heading_keyword", "Normative")).strip()
    informative_keyword = str(normative_raw.get("informative_heading_keyword", "Informative")).strip()
    forbidden_terms = _as_list_of_str(normative_raw.get("forbidden_ambiguous_terms_in_normative_sections"))
    unresolved_tokens = _as_list_of_str(normative_raw.get("unresolved_marker_tokens"))

    governance_raw = _as_mapping(sdd_raw.get("governance"))
    spec_requirements_raw = _as_mapping(governance_raw.get("spec_requirements"))
    app_onboarding_raw = _as_mapping(governance_raw.get("app_onboarding_contract"))
    publish_raw = _as_mapping(governance_raw.get("publish_contract"))
    escalation_raw = _as_mapping(governance_raw.get("blueprint_defect_escalation_contract"))
    control_section_keyword = str(
        spec_requirements_raw.get("control_section_heading_keyword", "Applicable Guardrail Controls")
    ).strip()
    control_id_pattern_text = _normalize_regex_text(
        str(spec_requirements_raw.get("control_id_pattern", r"\bSDD-C-[0-9]{3}\b")).strip()
    )
    stack_profile_keyword = str(
        spec_requirements_raw.get("stack_profile_section_heading_keyword", "Implementation Stack Profile")
    ).strip()
    stack_profile_required_fields = _as_list_of_str(spec_requirements_raw.get("stack_profile_required_fields"))
    allowed_agent_execution_models = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("stack_profile_allowed_agent_execution_models"))
        if value.strip()
    }
    managed_service_allowed_values = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("managed_service_preference_allowed_values"))
        if value.strip()
    }
    runtime_profile_allowed_values = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("runtime_profile_allowed_values"))
        if value.strip()
    }
    local_kube_context_policy_allowed_values = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("local_kube_context_policy_allowed_values"))
        if value.strip()
    }
    local_provisioning_stack_allowed_values = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("local_provisioning_stack_allowed_values"))
        if value.strip()
    }
    runtime_identity_baseline_allowed_values = {
        value.strip().lower()
        for value in _as_list_of_str(spec_requirements_raw.get("runtime_identity_baseline_allowed_values"))
        if value.strip()
    }

    app_onboarding_plan_section_keyword = str(
        app_onboarding_raw.get("required_plan_section_keyword", "App Onboarding Contract")
    ).strip()
    app_onboarding_tasks_section_keyword = str(
        app_onboarding_raw.get("required_tasks_section_keyword", "App Onboarding Minimum Targets")
    ).strip()
    app_onboarding_required_targets = _as_list_of_str(app_onboarding_raw.get("required_make_targets"))
    publish_required_pr_context_sections = _as_list_of_str(publish_raw.get("required_pr_context_sections"))
    publish_required_hardening_review_sections = _as_list_of_str(
        publish_raw.get("required_hardening_review_sections")
    )
    escalation_section_keyword = str(
        escalation_raw.get("required_spec_section_keyword", "Blueprint Upstream Defect Escalation")
    ).strip()
    escalation_required_fields = _as_list_of_str(escalation_raw.get("required_fields"))
    clarification_marker_token = str(readiness_raw.get("clarification_marker_token", "")).strip()
    clarification_count_field = next(
        (field for field in required_zero_fields if "clarification" in field.lower()),
        "",
    )
    # Required fields per work-item document (scaffold placeholder guard).
    # Keys are filename (e.g. "context_pack.md"), values are lists of field names.
    _raw_doc_required_fields = readiness_raw.get("work_item_document_required_fields")
    work_item_document_required_fields: dict[str, list[str]] = {}
    if isinstance(_raw_doc_required_fields, dict):
        for _doc_name, _fields in _raw_doc_required_fields.items():
            work_item_document_required_fields[str(_doc_name)] = _as_list_of_str(_fields)

    try:
        control_id_pattern = re.compile(control_id_pattern_text)
    except re.error:
        control_id_pattern = re.compile(r"\bSDD-C-[0-9]{3}\b")

    requirement_pattern = re.compile(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3})\b")
    acceptance_pattern = re.compile(r"\bAC-\d{3}\b")

    for work_item_dir in work_items:
        missing_docs: list[str] = []
        for document_name in required_documents:
            doc_path = work_item_dir / document_name
            if not doc_path.is_file():
                missing_docs.append(document_name)
        for document_name in missing_docs:
            violations.append(
                Violation(
                    path=str(work_item_dir.relative_to(repo_root) / document_name),
                    message="missing required SDD work-item document",
                )
            )
        if missing_docs:
            continue

        plan_path = work_item_dir / "plan.md"
        spec_path = work_item_dir / "spec.md"
        tasks_path = work_item_dir / "tasks.md"
        traceability_path = work_item_dir / "traceability.md"
        graph_path = work_item_dir / "graph.json"
        evidence_manifest_path = work_item_dir / "evidence_manifest.json"
        context_pack_path = work_item_dir / "context_pack.md"
        pr_context_path = work_item_dir / "pr_context.md"
        hardening_review_path = work_item_dir / "hardening_review.md"

        plan_content = plan_path.read_text(encoding="utf-8", errors="surrogateescape")
        spec_content = spec_path.read_text(encoding="utf-8", errors="surrogateescape")
        tasks_content = tasks_path.read_text(encoding="utf-8", errors="surrogateescape")
        traceability_content = traceability_path.read_text(encoding="utf-8", errors="surrogateescape")
        context_pack_content = context_pack_path.read_text(encoding="utf-8", errors="surrogateescape")
        pr_context_content = pr_context_path.read_text(encoding="utf-8", errors="surrogateescape")
        hardening_review_content = hardening_review_path.read_text(encoding="utf-8", errors="surrogateescape")

        sections = _split_markdown_sections(spec_content)
        plan_sections = _split_markdown_sections(plan_content)
        pr_context_sections = _split_markdown_sections(pr_context_content)
        hardening_review_sections = _split_markdown_sections(hardening_review_content)

        readiness_section = _find_section(sections, "Readiness Gate")
        if readiness_section is None:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message="missing 'Readiness Gate' section",
                )
            )
            continue

        readiness_fields = _parse_bullet_kv(readiness_section.content)
        status_value = readiness_fields.get(status_field.lower(), "")
        if not status_value:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing readiness status field: {status_field}",
                )
            )
            continue

        spec_ready = _is_truthy(status_value)
        if adr_path_field and adr_path_field.lower() not in readiness_fields:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing readiness field: {adr_path_field}",
                )
            )
        if adr_status_field and adr_status_field.lower() not in readiness_fields:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing readiness field: {adr_status_field}",
                )
            )

        adr_path_value = readiness_fields.get(adr_path_field.lower(), "").strip()
        adr_status_value = readiness_fields.get(adr_status_field.lower(), "").strip().lower()
        if required_value == "true" and not spec_ready and _checked_tasks_in_sections(tasks_content, implementation_sections):
            violations.append(
                Violation(
                    path=str(tasks_path.relative_to(repo_root)),
                    message="implementation tasks are checked while SPEC_READY is not true",
                )
            )

        if spec_ready and blocked_marker and blocked_marker in spec_content:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"{blocked_marker} marker present while SPEC_READY=true",
                )
            )

        if spec_ready:
            if not adr_path_value:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"{adr_path_field} must be set when SPEC_READY=true",
                    )
                )
            else:
                # Keep implementation-ready specs anchored to canonical ADR decision roots.
                if adr_path_allowed_prefixes and not any(
                    adr_path_value.startswith(prefix) for prefix in adr_path_allowed_prefixes
                ):
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                f"{adr_path_field} must start with one of: "
                                + ", ".join(adr_path_allowed_prefixes)
                            ),
                        )
                    )
                resolved_adr_path = (repo_root / adr_path_value).resolve()
                try:
                    resolved_adr_path.relative_to(repo_root.resolve())
                except ValueError:
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=f"{adr_path_field} must resolve inside repository root",
                        )
                    )
                else:
                    if not resolved_adr_path.is_file():
                        violations.append(
                            Violation(
                                path=str(spec_path.relative_to(repo_root)),
                                message=f"{adr_path_field} points to missing file: {adr_path_value}",
                            )
                        )

            if not adr_status_value:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"{adr_status_field} must be set when SPEC_READY=true",
                    )
                )
            elif adr_status_value not in adr_status_approved_values:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            f"{adr_status_field} must be one of: "
                            + ", ".join(sorted(adr_status_approved_values))
                        ),
                    )
                )

        for field_name in required_zero_fields:
            field_value = readiness_fields.get(field_name.lower(), "")
            parsed = _parse_non_negative_int(field_value)
            if parsed is None:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"readiness gate missing numeric field: {field_name}",
                    )
                )
                continue
            if spec_ready and parsed != 0:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"readiness field must be zero when SPEC_READY=true: {field_name}",
                    )
                )

        for signoff in required_signoffs:
            key = f"{signoff} sign-off".lower()
            signoff_value = readiness_fields.get(key, "")
            if not signoff_value:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"missing sign-off field: {signoff} sign-off",
                    )
                )
                continue
            if spec_ready and signoff_value.strip().lower() not in APPROVED_SIGNOFF_VALUES:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"sign-off must be approved when SPEC_READY=true: {signoff}",
                    )
                )

        aggregate = "\n".join((spec_content, tasks_content, traceability_content)).lower()
        readiness_field_names_for_marker_scan = [
            status_field,
            adr_path_field,
            adr_status_field,
            "Missing input blocker token",
            *required_zero_fields,
            *[f"{signoff} sign-off" for signoff in required_signoffs],
        ]
        aggregate_for_marker_scan = _strip_readiness_gate_labels_for_marker_scan(
            aggregate,
            readiness_field_names=readiness_field_names_for_marker_scan,
        )

        clarification_count = 0
        if clarification_count_field:
            parsed_clarification_count = _parse_non_negative_int(
                readiness_fields.get(clarification_count_field.lower(), "")
            )
            if parsed_clarification_count is None:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"readiness gate missing numeric field: {clarification_count_field}",
                    )
                )
            else:
                clarification_count = parsed_clarification_count

        clarification_token_present = False
        if clarification_marker_token:
            clarification_token_present = _contains_term(aggregate_for_marker_scan, clarification_marker_token)
            if spec_ready and clarification_token_present:
                violations.append(
                    Violation(
                        path=str(work_item_dir.relative_to(repo_root)),
                        message=(
                            "clarification marker token present while SPEC_READY=true: "
                            f"{clarification_marker_token}"
                        ),
                    )
                )
            if clarification_count_field:
                if clarification_token_present and clarification_count == 0:
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                f"{clarification_count_field} must be > 0 when marker token "
                                f"'{clarification_marker_token}' is present"
                            ),
                        )
                    )
                if not clarification_token_present and clarification_count > 0:
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                f"{clarification_count_field} must be 0 when marker token "
                                f"'{clarification_marker_token}' is absent"
                            ),
                        )
                    )

        if spec_ready and unresolved_tokens:
            for token in unresolved_tokens:
                if _contains_term(aggregate_for_marker_scan, token):
                    violations.append(
                        Violation(
                            path=str(work_item_dir.relative_to(repo_root)),
                            message=f"unresolved marker token present while SPEC_READY=true: {token}",
                        )
                    )

        normative_sections = [
            section for section in sections if normative_keyword and normative_keyword.lower() in section.title.lower()
        ]
        informative_sections = [
            section for section in sections if informative_keyword and informative_keyword.lower() in section.title.lower()
        ]

        if not normative_sections:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing section heading containing keyword: {normative_keyword}",
                )
            )
        if not informative_sections:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing section heading containing keyword: {informative_keyword}",
                )
            )

        for section in normative_sections:
            normalized_content = section.content.lower()
            for term in forbidden_terms:
                if _contains_term(normalized_content, term):
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                "forbidden ambiguous term in normative section "
                                f"'{section.title}': {term}"
                            ),
                        )
                    )

        control_section = _find_section(sections, control_section_keyword)
        if control_section is None:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing section heading containing keyword: {control_section_keyword}",
                )
            )
        else:
            declared_controls = sorted(set(control_id_pattern.findall(control_section.content)))
            if not declared_controls:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message="applicable guardrail controls section must include at least one SDD-C-### ID",
                    )
                )
            elif catalog_control_ids:
                for control_id in declared_controls:
                    if control_id not in catalog_control_ids:
                        violations.append(
                            Violation(
                                path=str(spec_path.relative_to(repo_root)),
                                message=f"unknown control ID in applicable guardrail controls section: {control_id}",
                            )
                        )

        stack_section = _find_section(sections, stack_profile_keyword)
        if stack_section is None:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message=f"missing section heading containing keyword: {stack_profile_keyword}",
                )
            )
        else:
            stack_fields = _parse_bullet_kv(stack_section.content)
            for field in stack_profile_required_fields:
                value = stack_fields.get(field.lower(), "")
                if value:
                    continue
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=f"missing stack profile field: {field}",
                    )
                )

            agent_key = next(
                (field for field in stack_profile_required_fields if field.lower() == "agent execution model"),
                "Agent execution model",
            ).lower()
            agent_value = stack_fields.get(agent_key, "").strip().lower()
            if agent_value and allowed_agent_execution_models and agent_value not in allowed_agent_execution_models:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported agent execution model: "
                            f"{stack_fields.get(agent_key, '').strip()} (allowed: "
                            + ", ".join(sorted(allowed_agent_execution_models))
                            + ")"
                        ),
                    )
                )

            managed_service_key = next(
                (field for field in stack_profile_required_fields if field.lower() == "managed service preference"),
                "Managed service preference",
            ).lower()
            managed_service_value = stack_fields.get(managed_service_key, "").strip().lower()
            if managed_service_value and managed_service_allowed_values and managed_service_value not in managed_service_allowed_values:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported managed service preference: "
                            f"{stack_fields.get(managed_service_key, '').strip()} (allowed: "
                            + ", ".join(sorted(managed_service_allowed_values))
                            + ")"
                        ),
                    )
                )

            exception_rationale_key = next(
                (
                    field
                    for field in stack_profile_required_fields
                    if field.lower() == "managed service exception rationale"
                ),
                "Managed service exception rationale",
            ).lower()
            exception_rationale_value = stack_fields.get(exception_rationale_key, "").strip()
            if managed_service_value == "explicit-consumer-exception":
                if not exception_rationale_value or exception_rationale_value.lower() == "none":
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                "managed service exception rationale must be explicitly set when "
                                "Managed service preference is explicit-consumer-exception"
                            ),
                        )
                    )

            runtime_profile_key = next(
                (field for field in stack_profile_required_fields if field.lower() == "runtime profile"),
                "Runtime profile",
            ).lower()
            runtime_profile_value = stack_fields.get(runtime_profile_key, "").strip().lower()
            if runtime_profile_value and runtime_profile_allowed_values and runtime_profile_value not in runtime_profile_allowed_values:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported runtime profile: "
                            f"{stack_fields.get(runtime_profile_key, '').strip()} (allowed: "
                            + ", ".join(sorted(runtime_profile_allowed_values))
                            + ")"
                        ),
                    )
                )

            local_kube_context_policy_key = next(
                (
                    field
                    for field in stack_profile_required_fields
                    if field.lower() == "local kubernetes context policy"
                ),
                "Local Kubernetes context policy",
            ).lower()
            local_kube_context_policy_value = stack_fields.get(local_kube_context_policy_key, "").strip().lower()
            if (
                local_kube_context_policy_value
                and local_kube_context_policy_allowed_values
                and local_kube_context_policy_value not in local_kube_context_policy_allowed_values
            ):
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported local kubernetes context policy: "
                            f"{stack_fields.get(local_kube_context_policy_key, '').strip()} (allowed: "
                            + ", ".join(sorted(local_kube_context_policy_allowed_values))
                            + ")"
                        ),
                    )
                )

            local_provisioning_stack_key = next(
                (
                    field
                    for field in stack_profile_required_fields
                    if field.lower() == "local provisioning stack"
                ),
                "Local provisioning stack",
            ).lower()
            local_provisioning_stack_value = stack_fields.get(local_provisioning_stack_key, "").strip().lower()
            if (
                local_provisioning_stack_value
                and local_provisioning_stack_allowed_values
                and local_provisioning_stack_value not in local_provisioning_stack_allowed_values
            ):
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported local provisioning stack: "
                            f"{stack_fields.get(local_provisioning_stack_key, '').strip()} (allowed: "
                            + ", ".join(sorted(local_provisioning_stack_allowed_values))
                            + ")"
                        ),
                    )
                )

            runtime_identity_baseline_key = next(
                (
                    field
                    for field in stack_profile_required_fields
                    if field.lower() == "runtime identity baseline"
                ),
                "Runtime identity baseline",
            ).lower()
            runtime_identity_baseline_value = stack_fields.get(runtime_identity_baseline_key, "").strip().lower()
            if (
                runtime_identity_baseline_value
                and runtime_identity_baseline_allowed_values
                and runtime_identity_baseline_value not in runtime_identity_baseline_allowed_values
            ):
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "unsupported runtime identity baseline: "
                            f"{stack_fields.get(runtime_identity_baseline_key, '').strip()} (allowed: "
                            + ", ".join(sorted(runtime_identity_baseline_allowed_values))
                            + ")"
                        ),
                    )
                )

            local_first_exception_rationale_key = next(
                (
                    field
                    for field in stack_profile_required_fields
                    if field.lower() == "local-first exception rationale"
                ),
                "Local-first exception rationale",
            ).lower()
            local_first_exception_rationale_value = stack_fields.get(local_first_exception_rationale_key, "").strip()
            if runtime_profile_value and runtime_profile_value != "local-first-docker-desktop-kubernetes":
                if not local_first_exception_rationale_value or local_first_exception_rationale_value.lower() == "none":
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                "local-first exception rationale must be explicitly set when "
                                "Runtime profile is not local-first-docker-desktop-kubernetes"
                            ),
                        )
                    )

        if app_onboarding_plan_section_keyword:
            app_onboarding_plan_section = _find_section(plan_sections, app_onboarding_plan_section_keyword)
            if app_onboarding_plan_section is None:
                violations.append(
                    Violation(
                        path=str(plan_path.relative_to(repo_root)),
                        message=(
                            "missing section heading containing keyword: "
                            f"{app_onboarding_plan_section_keyword}"
                        ),
                    )
                )
            elif app_onboarding_required_targets:
                missing_targets = _section_contains_all_targets(
                    app_onboarding_plan_section.content,
                    app_onboarding_required_targets,
                )
                for missing_target in missing_targets:
                    violations.append(
                        Violation(
                            path=str(plan_path.relative_to(repo_root)),
                            message=(
                                f"app onboarding plan section missing required make target: {missing_target}"
                            ),
                        )
                    )

        if app_onboarding_tasks_section_keyword:
            task_sections = _split_markdown_sections(tasks_content)
            app_onboarding_tasks_section: MarkdownSection | None = None
            for section in task_sections:
                if app_onboarding_tasks_section_keyword.lower() in section.title.lower():
                    app_onboarding_tasks_section = section
                    break
            if app_onboarding_tasks_section is None:
                violations.append(
                    Violation(
                        path=str(tasks_path.relative_to(repo_root)),
                        message=(
                            "missing section heading containing keyword: "
                            f"{app_onboarding_tasks_section_keyword}"
                        ),
                    )
                )
            elif app_onboarding_required_targets:
                missing_targets = _section_contains_all_targets(
                    app_onboarding_tasks_section.content,
                    app_onboarding_required_targets,
                )
                for missing_target in missing_targets:
                    violations.append(
                        Violation(
                            path=str(tasks_path.relative_to(repo_root)),
                            message=(
                                f"app onboarding tasks section missing required make target: {missing_target}"
                            ),
                        )
                    )

        if escalation_section_keyword:
            escalation_section = _find_section(sections, escalation_section_keyword)
            if escalation_section is None:
                violations.append(
                    Violation(
                        path=str(spec_path.relative_to(repo_root)),
                        message=(
                            "missing section heading containing keyword: "
                            f"{escalation_section_keyword}"
                        ),
                    )
                )
            else:
                escalation_fields = _parse_bullet_kv(escalation_section.content)
                for field_name in escalation_required_fields:
                    field_value = escalation_fields.get(field_name.lower(), "").strip()
                    if field_value:
                        continue
                    violations.append(
                        Violation(
                            path=str(spec_path.relative_to(repo_root)),
                            message=(
                                "blueprint defect escalation section missing required field value: "
                                f"{field_name}"
                            ),
                        )
                    )

        for required_section in publish_required_pr_context_sections:
            if _find_section(pr_context_sections, required_section) is None:
                violations.append(
                    Violation(
                        path=str(pr_context_path.relative_to(repo_root)),
                        message=(
                            "missing section heading containing keyword: "
                            f"{required_section}"
                        ),
                    )
                )

        for required_section in publish_required_hardening_review_sections:
            if _find_section(hardening_review_sections, required_section) is None:
                violations.append(
                    Violation(
                        path=str(hardening_review_path.relative_to(repo_root)),
                        message=(
                            "missing section heading containing keyword: "
                            f"{required_section}"
                        ),
                    )
                )

        requirement_ids = sorted(set(requirement_pattern.findall(spec_content)))
        acceptance_ids = sorted(set(acceptance_pattern.findall(spec_content)))

        if acceptance_criteria_required and not acceptance_ids:
            violations.append(
                Violation(
                    path=str(spec_path.relative_to(repo_root)),
                    message="missing acceptance criteria IDs (AC-xxx)",
                )
            )

        if requirement_traceability_required and spec_ready:
            for requirement_id in requirement_ids:
                if requirement_id not in traceability_content:
                    violations.append(
                        Violation(
                            path=str(traceability_path.relative_to(repo_root)),
                            message=f"missing requirement traceability mapping for {requirement_id}",
                        )
                    )
            for acceptance_id in acceptance_ids:
                if acceptance_id not in traceability_content:
                    violations.append(
                        Violation(
                            path=str(traceability_path.relative_to(repo_root)),
                            message=f"missing acceptance traceability mapping for {acceptance_id}",
                        )
                    )

        try:
            graph_payload = _load_json_or_yaml(graph_path)
        except ValueError as exc:
            violations.append(Violation(path=str(graph_path.relative_to(repo_root)), message=str(exc)))
            graph_payload = {}

        graph_nodes = graph_payload.get("nodes")
        graph_ids: set[str] = set()
        if isinstance(graph_nodes, list):
            for node in graph_nodes:
                if not isinstance(node, dict):
                    continue
                node_id = str(node.get("id", "")).strip()
                if not node_id:
                    continue
                graph_ids.add(node_id)
        else:
            violations.append(
                Violation(
                    path=str(graph_path.relative_to(repo_root)),
                    message="graph.json must define a nodes list",
                )
            )

        spec_traceability_ids = set(requirement_ids + acceptance_ids)
        graph_traceability_ids = {
            item
            for item in graph_ids
            if re.fullmatch(r"(?:FR-\d{3}|NFR-[A-Z]+-\d{3}|AC-\d{3})", item)
        }

        for missing_id in sorted(spec_traceability_ids - graph_traceability_ids):
            violations.append(
                Violation(
                    path=str(graph_path.relative_to(repo_root)),
                    message=f"graph.json missing requirement/acceptance node ID from spec.md: {missing_id}",
                )
            )
        for stale_id in sorted(graph_traceability_ids - spec_traceability_ids):
            violations.append(
                Violation(
                    path=str(graph_path.relative_to(repo_root)),
                    message=f"graph.json contains stale requirement/acceptance ID not present in spec.md: {stale_id}",
                )
            )

        traceability_ids = set(re.findall(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3}|AC-\d{3})\b", traceability_content))
        for missing_id in sorted(spec_traceability_ids - traceability_ids):
            violations.append(
                Violation(
                    path=str(traceability_path.relative_to(repo_root)),
                    message=f"traceability.md missing requirement/acceptance ID from spec.md: {missing_id}",
                )
            )
        for stale_id in sorted(traceability_ids - spec_traceability_ids):
            violations.append(
                Violation(
                    path=str(traceability_path.relative_to(repo_root)),
                    message=f"traceability.md contains stale requirement/acceptance ID not present in spec.md: {stale_id}",
                )
            )

        try:
            evidence_manifest_payload = _load_json_or_yaml(evidence_manifest_path)
        except ValueError as exc:
            violations.append(Violation(path=str(evidence_manifest_path.relative_to(repo_root)), message=str(exc)))
            evidence_manifest_payload = {}

        if evidence_manifest_payload:
            for required_key in ("manifest_version", "work_item", "generated_by", "generated_at_utc", "files"):
                if required_key not in evidence_manifest_payload:
                    violations.append(
                        Violation(
                            path=str(evidence_manifest_path.relative_to(repo_root)),
                            message=f"evidence_manifest.json missing required key: {required_key}",
                        )
                    )

            files_raw = evidence_manifest_payload.get("files")
            if files_raw is not None and not isinstance(files_raw, list):
                violations.append(
                    Violation(
                        path=str(evidence_manifest_path.relative_to(repo_root)),
                        message="evidence_manifest.json files field must be a list",
                    )
                )
            elif isinstance(files_raw, list):
                for idx, entry in enumerate(files_raw):
                    if not isinstance(entry, dict):
                        violations.append(
                            Violation(
                                path=str(evidence_manifest_path.relative_to(repo_root)),
                                message=f"evidence_manifest.json files[{idx}] must be a mapping",
                            )
                        )
                        continue
                    if not str(entry.get("path", "")).strip():
                        violations.append(
                            Violation(
                                path=str(evidence_manifest_path.relative_to(repo_root)),
                                message=f"evidence_manifest.json files[{idx}] missing path",
                            )
                        )
                    if not str(entry.get("sha256", "")).strip():
                        violations.append(
                            Violation(
                                path=str(evidence_manifest_path.relative_to(repo_root)),
                                message=f"evidence_manifest.json files[{idx}] missing sha256",
                            )
                        )

        if not context_pack_content.strip():
            violations.append(
                Violation(
                    path=str(context_pack_path.relative_to(repo_root)),
                    message="context_pack.md must not be empty",
                )
            )
        if "Context Snapshot" not in context_pack_content:
            violations.append(
                Violation(
                    path=str(context_pack_path.relative_to(repo_root)),
                    message="context_pack.md must include 'Context Snapshot' section",
                )
            )

        # Scaffold placeholder guard: assert required fields are non-empty in
        # work-item documents declared in readiness_gate.work_item_document_required_fields.
        # Only enforced when SPEC_READY=true — in-progress specs may still have placeholders.
        if not spec_ready:
            continue
        _doc_contents: dict[str, tuple[Path, str]] = {
            "context_pack.md": (context_pack_path, context_pack_content),
        }
        architecture_path = work_item_dir / "architecture.md"
        if architecture_path.is_file():
            _doc_contents["architecture.md"] = (
                architecture_path,
                architecture_path.read_text(encoding="utf-8", errors="surrogateescape"),
            )
        for _doc_name, _required_fields in work_item_document_required_fields.items():
            if _doc_name not in _doc_contents:
                continue
            _doc_path, _doc_text = _doc_contents[_doc_name]
            _kv = _parse_bullet_kv(_doc_text)
            for _field in _required_fields:
                if not _kv.get(_field.lower(), "").strip():
                    violations.append(
                        Violation(
                            path=str(_doc_path.relative_to(repo_root)),
                            message=f"required field '{_field}' is empty or missing (scaffold placeholder not filled in)",
                        )
                    )

    return violations


def _validate_contract_assets(contract_raw: dict[str, Any], repo_root: Path) -> list[Violation]:
    violations: list[Violation] = []
    spec_raw = _as_mapping(contract_raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    if not sdd_raw:
        return [Violation(path="blueprint/contract.yaml", message="missing spec.spec_driven_development_contract section")]

    lifecycle_raw = _as_mapping(sdd_raw.get("lifecycle"))
    phases = _as_list_of_str(lifecycle_raw.get("phases"))
    if not phases:
        violations.append(Violation(path="blueprint/contract.yaml", message="SDD lifecycle phases must be declared"))

    branch_contract_raw = _as_mapping(sdd_raw.get("branch_contract"))
    for required_key in (
        "dedicated_branch_required_by_default",
        "explicit_opt_out_flag",
        "default_prefix",
        "branch_name_pattern",
        "enforce_non_default_branch",
    ):
        if required_key not in branch_contract_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"branch_contract.{required_key} is required",
                )
            )

    repository_raw = _as_mapping(spec_raw.get("repository"))
    branch_naming_raw = _as_mapping(repository_raw.get("branch_naming"))
    allowed_prefixes = _as_list_of_str(branch_naming_raw.get("purpose_prefixes"))

    default_prefix = str(branch_contract_raw.get("default_prefix", "")).strip()
    if default_prefix and allowed_prefixes and default_prefix not in allowed_prefixes:
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message="branch_contract.default_prefix must be declared in repository.branch_naming.purpose_prefixes",
            )
        )

    explicit_opt_out_flag = str(branch_contract_raw.get("explicit_opt_out_flag", "")).strip()
    if explicit_opt_out_flag and not explicit_opt_out_flag.startswith("--"):
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message="branch_contract.explicit_opt_out_flag must be a long-form CLI flag (for example --no-create-branch)",
            )
        )

    branch_pattern = str(branch_contract_raw.get("branch_name_pattern", "")).strip()
    if branch_pattern and "<work-item-slug>" not in branch_pattern:
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message="branch_contract.branch_name_pattern must document <work-item-slug>",
            )
        )
    if branch_pattern and "<YYYY-MM-DD>" not in branch_pattern:
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message="branch_contract.branch_name_pattern must document <YYYY-MM-DD>",
            )
        )

    artifacts_raw = _as_mapping(sdd_raw.get("artifacts"))
    for required_key in (
        "policy_mapping_file",
        "control_catalog_source_file",
        "control_catalog_file",
        "specs_workspace_readme",
        "blueprint_template_root",
        "consumer_template_root",
        "required_work_item_documents",
        "required_paths",
    ):
        if required_key not in artifacts_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"artifacts.{required_key} is required",
                )
            )

    required_paths = _as_list_of_str(artifacts_raw.get("required_paths"))
    for relative_path in required_paths:
        if not (repo_root / relative_path).exists():
            violations.append(Violation(path=relative_path, message="required SDD asset path is missing"))

    required_documents = _as_list_of_str(artifacts_raw.get("required_work_item_documents"))
    blueprint_template_root = artifacts_raw.get("blueprint_template_root", "")
    consumer_template_root = artifacts_raw.get("consumer_template_root", "")

    if isinstance(blueprint_template_root, str) and blueprint_template_root.strip():
        root_path = repo_root / blueprint_template_root
        for document in required_documents:
            candidate = _template_doc_path(root_path, document)
            if candidate is None:
                violations.append(
                    Violation(
                        path=blueprint_template_root,
                        message=f"missing required blueprint SDD template document: {document}",
                    )
                )
    else:
        violations.append(
            Violation(path="blueprint/contract.yaml", message="artifacts.blueprint_template_root must be set")
        )

    if isinstance(consumer_template_root, str) and consumer_template_root.strip():
        root_path = repo_root / consumer_template_root
        for document in required_documents:
            candidate = _template_doc_path(root_path, document)
            if candidate is None:
                violations.append(
                    Violation(
                        path=consumer_template_root,
                        message=f"missing required consumer SDD template document: {document}",
                    )
                )
    else:
        violations.append(
            Violation(path="blueprint/contract.yaml", message="artifacts.consumer_template_root must be set")
        )

    governance_raw = _as_mapping(sdd_raw.get("governance"))
    required_guardrails = _as_list_of_str(governance_raw.get("required_guardrails"))
    for required_key in (
        "required_guardrails",
        "control_catalog",
        "spec_requirements",
        "app_onboarding_contract",
        "publish_contract",
        "blueprint_defect_escalation_contract",
    ):
        if required_key not in governance_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.{required_key} is required",
                )
            )

    control_catalog_raw = _as_mapping(governance_raw.get("control_catalog"))
    for required_key in ("id_pattern", "required_columns", "allowed_gate_values"):
        if required_key not in control_catalog_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.control_catalog.{required_key} is required",
                )
            )

    spec_requirements_raw = _as_mapping(governance_raw.get("spec_requirements"))
    for required_key in (
        "control_section_heading_keyword",
        "control_id_pattern",
        "stack_profile_section_heading_keyword",
        "stack_profile_required_fields",
        "stack_profile_allowed_agent_execution_models",
        "managed_service_preference_allowed_values",
        "runtime_profile_allowed_values",
        "local_kube_context_policy_allowed_values",
        "local_provisioning_stack_allowed_values",
        "runtime_identity_baseline_allowed_values",
    ):
        if required_key not in spec_requirements_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.spec_requirements.{required_key} is required",
                )
            )

    app_onboarding_raw = _as_mapping(governance_raw.get("app_onboarding_contract"))
    for required_key in (
        "required_plan_section_keyword",
        "required_tasks_section_keyword",
        "required_make_targets",
    ):
        if required_key not in app_onboarding_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.app_onboarding_contract.{required_key} is required",
                )
            )

    publish_raw = _as_mapping(governance_raw.get("publish_contract"))
    for required_key in (
        "required_pr_context_sections",
        "required_hardening_review_sections",
        "required_pr_template_headings",
        "required_pr_template_paths",
    ):
        if required_key not in publish_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.publish_contract.{required_key} is required",
                )
            )

    escalation_raw = _as_mapping(governance_raw.get("blueprint_defect_escalation_contract"))
    for required_key in ("required_spec_section_keyword", "required_fields"):
        if required_key not in escalation_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"governance.blueprint_defect_escalation_contract.{required_key} is required",
                )
            )

    policy_mapping_path = artifacts_raw.get("policy_mapping_file", "")
    if isinstance(policy_mapping_path, str) and policy_mapping_path.strip():
        policy_file = repo_root / policy_mapping_path
        if policy_file.is_file():
            policy_content = policy_file.read_text(encoding="utf-8", errors="surrogateescape").lower()
            for guardrail in required_guardrails:
                if guardrail.lower() not in policy_content:
                    violations.append(
                        Violation(
                            path=policy_mapping_path,
                            message=f"policy mapping is missing required guardrail keyword: {guardrail}",
                        )
                    )
        else:
            violations.append(Violation(path=policy_mapping_path, message="policy mapping file is missing"))

    control_catalog_source_path = artifacts_raw.get("control_catalog_source_file", "")
    if isinstance(control_catalog_source_path, str) and control_catalog_source_path.strip():
        source_file = repo_root / control_catalog_source_path
        if not source_file.is_file():
            violations.append(
                Violation(
                    path=control_catalog_source_path,
                    message="control catalog source file is missing",
                )
            )
    else:
        violations.append(
            Violation(
                path="blueprint/contract.yaml",
                message="artifacts.control_catalog_source_file must be set",
            )
        )

    publish_raw = _as_mapping(governance_raw.get("publish_contract"))
    required_pr_template_headings = _as_list_of_str(publish_raw.get("required_pr_template_headings"))
    required_pr_template_paths = _as_list_of_str(publish_raw.get("required_pr_template_paths"))
    for template_path in required_pr_template_paths:
        candidate = repo_root / template_path
        if not candidate.is_file():
            violations.append(Violation(path=template_path, message="required PR template file is missing"))
            continue
        content = candidate.read_text(encoding="utf-8", errors="surrogateescape")
        sections = _split_markdown_sections(content)
        for heading in required_pr_template_headings:
            if _find_section(sections, heading) is None:
                violations.append(
                    Violation(
                        path=template_path,
                        message=f"missing section heading containing keyword: {heading}",
                    )
                )

    readiness_raw = _as_mapping(sdd_raw.get("readiness_gate"))
    for required_key in (
        "status_field",
        "required_value",
        "blocked_marker",
        "required_zero_fields",
        "required_signoffs",
        "adr_path_field",
        "adr_status_field",
        "adr_status_approved_values",
        "adr_path_allowed_prefixes",
        "implementation_sections",
        "clarification_marker_token",
        "documentation_sync_required",
        "documentation_validation_commands",
    ):
        if required_key not in readiness_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"readiness_gate.{required_key} is required",
                )
            )

    if bool(readiness_raw.get("documentation_sync_required", False)):
        doc_commands = _as_list_of_str(readiness_raw.get("documentation_validation_commands"))
        expected_commands = {"make docs-build", "make docs-smoke"}
        for command in expected_commands:
            if command not in doc_commands:
                violations.append(
                    Violation(
                        path="blueprint/contract.yaml",
                        message=f"readiness_gate.documentation_validation_commands must include: {command}",
                    )
                )

    normative_raw = _as_mapping(sdd_raw.get("normative_language"))
    for required_key in (
        "normative_heading_keyword",
        "informative_heading_keyword",
        "forbidden_ambiguous_terms_in_normative_sections",
        "unresolved_marker_tokens",
    ):
        if required_key not in normative_raw:
            violations.append(
                Violation(
                    path="blueprint/contract.yaml",
                    message=f"normative_language.{required_key} is required",
                )
            )

    agents_files = [
        "AGENTS.md",
        "scripts/templates/consumer/init/AGENTS.md.tmpl",
    ]
    for agents_file in agents_files:
        content_path = repo_root / agents_file
        if not content_path.is_file():
            violations.append(Violation(path=agents_file, message="governance file is missing"))
            continue
        content = content_path.read_text(encoding="utf-8", errors="surrogateescape")
        if phases and not _contains_in_order(content, phases):
            phase_text = " -> ".join(phases)
            violations.append(
                Violation(path=agents_file, message=f"must reference SDD phases in order: {phase_text}")
            )
        if "BLOCKED_MISSING_INPUTS" not in content:
            violations.append(
                Violation(path=agents_file, message="must document BLOCKED_MISSING_INPUTS blocking token")
            )

    quality_raw = _as_mapping(sdd_raw.get("quality"))
    check_script = quality_raw.get("check_script")
    if isinstance(check_script, str) and check_script.strip():
        if not (repo_root / check_script).is_file():
            violations.append(Violation(path=check_script, message="declared SDD quality check script is missing"))
    else:
        violations.append(Violation(path="blueprint/contract.yaml", message="quality.check_script must be set"))

    spec_scaffold_path = repo_root / "scripts/bin/blueprint/spec_scaffold.py"
    if not spec_scaffold_path.is_file():
        violations.append(Violation(path="scripts/bin/blueprint/spec_scaffold.py", message="SDD scaffold script is missing"))
    else:
        scaffold_content = spec_scaffold_path.read_text(encoding="utf-8", errors="surrogateescape")
        if "dedicated_branch_required_by_default" not in scaffold_content:
            violations.append(
                Violation(
                    path="scripts/bin/blueprint/spec_scaffold.py",
                    message="must enforce branch_contract.dedicated_branch_required_by_default",
                )
            )
        if explicit_opt_out_flag and explicit_opt_out_flag not in scaffold_content:
            violations.append(
                Violation(
                    path="scripts/bin/blueprint/spec_scaffold.py",
                    message=(
                        "must support branch_contract.explicit_opt_out_flag: "
                        f"{explicit_opt_out_flag}"
                    ),
                )
            )
        if "--branch" not in scaffold_content:
            violations.append(
                Violation(
                    path="scripts/bin/blueprint/spec_scaffold.py",
                    message="must support explicit branch override flag (--branch)",
                )
            )

    make_paths = [
        ("make/blueprint.generated.mk", "generated"),
        ("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl", "template"),
    ]
    for make_path, label in make_paths:
        candidate = repo_root / make_path
        if not candidate.is_file():
            violations.append(Violation(path=make_path, message=f"{label} makefile is missing"))
            continue
        content = candidate.read_text(encoding="utf-8", errors="surrogateescape")
        if "spec-scaffold:" not in content:
            violations.append(Violation(path=make_path, message="missing spec-scaffold target"))
            continue
        if "SPEC_BRANCH" not in content:
            violations.append(
                Violation(
                    path=make_path,
                    message="spec-scaffold target must expose SPEC_BRANCH passthrough",
                )
            )
        if "SPEC_NO_BRANCH" not in content:
            violations.append(
                Violation(
                    path=make_path,
                    message="spec-scaffold target must expose SPEC_NO_BRANCH passthrough",
                )
            )
        if explicit_opt_out_flag and explicit_opt_out_flag not in content:
            violations.append(
                Violation(
                    path=make_path,
                    message=(
                        "spec-scaffold target must pass branch_contract.explicit_opt_out_flag to CLI: "
                        f"{explicit_opt_out_flag}"
                    ),
                )
            )

    return violations


def main() -> int:
    contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
    violations = _validate_contract_assets(contract.raw, REPO_ROOT)
    control_catalog_violations, control_ids = _load_control_catalog(contract_raw=contract.raw, repo_root=REPO_ROOT)
    violations.extend(control_catalog_violations)
    violations.extend(_validate_work_item_specs(contract.raw, REPO_ROOT, control_ids))

    if violations:
        for violation in violations:
            print(
                f"[quality-sdd-check] {violation.path}: {violation.message}",
                file=sys.stderr,
            )
        return 1

    print("[quality-sdd-check] validated SDD assets, readiness gates, and language policy", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
