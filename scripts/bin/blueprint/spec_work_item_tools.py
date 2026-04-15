#!/usr/bin/env python3
"""Generate deterministic SDD work-item helper artifacts."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


def _as_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _resolve_work_item_dir(repo_root: Path, work_item: str | None) -> Path:
    specs_root = repo_root / "specs"
    if not specs_root.is_dir():
        raise ValueError("specs/ directory is missing")

    if work_item:
        raw = Path(work_item)
        candidates = []
        if raw.is_absolute():
            candidates.append(raw)
        else:
            candidates.append(repo_root / raw)
            candidates.append(specs_root / raw)
        for candidate in candidates:
            if candidate.is_dir():
                return candidate.resolve()
        raise ValueError(f"unable to resolve work-item directory from: {work_item}")

    candidates = [
        path
        for path in sorted(specs_root.iterdir())
        if path.is_dir() and not path.name.startswith(".") and (path / "spec.md").is_file()
    ]
    if not candidates:
        raise ValueError("no SDD work-item directories found under specs/")
    return candidates[-1].resolve()


def _split_markdown_sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = "(root)"
    buffer: list[str] = []

    for line in content.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            sections.append((current_title, "\n".join(buffer).strip()))
            current_title = match.group(2).strip()
            buffer = []
            continue
        buffer.append(line)
    sections.append((current_title, "\n".join(buffer).strip()))
    return sections


def _find_section_content(content: str, heading_keyword: str) -> str:
    keyword = heading_keyword.lower().strip()
    for title, section_content in _split_markdown_sections(content):
        if keyword in title.lower():
            return section_content
    return ""


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


def _collect_requirement_ids(spec_content: str) -> list[str]:
    requirement_pattern = re.compile(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3})\b")
    acceptance_pattern = re.compile(r"\bAC-\d{3}\b")
    return sorted(set(requirement_pattern.findall(spec_content) + acceptance_pattern.findall(spec_content)))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contract_required_documents(repo_root: Path) -> list[str]:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    spec_raw = _as_mapping(contract.raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    artifacts_raw = _as_mapping(sdd_raw.get("artifacts"))
    required_documents = _as_list_of_str(artifacts_raw.get("required_work_item_documents"))
    if not required_documents:
        raise ValueError("spec.spec_driven_development_contract.artifacts.required_work_item_documents is empty")
    return required_documents


def _cmd_impact(*, repo_root: Path, work_item_dir: Path, output_path: Path) -> int:
    spec_path = work_item_dir / "spec.md"
    traceability_path = work_item_dir / "traceability.md"
    graph_path = work_item_dir / "graph.yaml"
    evidence_manifest_path = work_item_dir / "evidence_manifest.json"

    spec_content = spec_path.read_text(encoding="utf-8", errors="surrogateescape")
    traceability_content = traceability_path.read_text(encoding="utf-8", errors="surrogateescape")
    graph_payload = _load_json_or_yaml(graph_path)

    requirement_ids = _collect_requirement_ids(spec_content)
    graph_nodes = graph_payload.get("nodes")
    if not isinstance(graph_nodes, list):
        raise ValueError(f"{graph_path.relative_to(repo_root)} must define a nodes list")
    graph_ids = sorted(
        {
            str(node.get("id", "")).strip()
            for node in graph_nodes
            if isinstance(node, dict) and str(node.get("id", "")).strip()
        }
    )
    graph_relevant_ids = sorted(
        {
            item
            for item in graph_ids
            if re.fullmatch(r"(?:FR-\d{3}|NFR-[A-Z]+-\d{3}|AC-\d{3})", item)
        }
    )
    missing_in_graph = sorted(set(requirement_ids) - set(graph_relevant_ids))
    stale_in_graph = sorted(set(graph_relevant_ids) - set(requirement_ids))

    graph_edges = graph_payload.get("edges")
    edge_count = len(graph_edges) if isinstance(graph_edges, list) else 0

    traceability_ids = sorted(
        set(re.findall(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3}|AC-\d{3})\b", traceability_content))
    )
    missing_in_traceability = sorted(set(requirement_ids) - set(traceability_ids))

    impacted_paths: list[str] = []
    if evidence_manifest_path.is_file():
        manifest = _load_json_or_yaml(evidence_manifest_path)
        files_raw = manifest.get("files")
        if isinstance(files_raw, list):
            impacted_paths = sorted(
                {
                    str(item.get("path", "")).strip()
                    for item in files_raw
                    if isinstance(item, dict) and str(item.get("path", "")).strip()
                }
            )

    lines: list[str] = []
    lines.append("# Spec Impact Summary")
    lines.append("")
    lines.append(f"- Work item: `{work_item_dir.relative_to(repo_root).as_posix()}`")
    lines.append(f"- Generated at (UTC): `{_utc_now()}`")
    lines.append(f"- Graph nodes: `{len(graph_ids)}`")
    lines.append(f"- Graph edges: `{edge_count}`")
    lines.append(f"- Spec requirement/acceptance IDs: `{len(requirement_ids)}`")
    lines.append("")
    lines.append("## Drift Signals")
    lines.append(
        "- IDs missing in graph: "
        + (", ".join(f"`{item}`" for item in missing_in_graph) if missing_in_graph else "none")
    )
    lines.append(
        "- IDs missing in traceability: "
        + (", ".join(f"`{item}`" for item in missing_in_traceability) if missing_in_traceability else "none")
    )
    lines.append(
        "- Stale graph IDs not present in spec: "
        + (", ".join(f"`{item}`" for item in stale_in_graph) if stale_in_graph else "none")
    )
    lines.append("")
    lines.append("## Impacted Paths")
    if impacted_paths:
        for path in impacted_paths:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none recorded in `evidence_manifest.json`")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[spec-impact] wrote {output_path.relative_to(repo_root)}")
    return 0


def _cmd_evidence_manifest(
    *,
    repo_root: Path,
    work_item_dir: Path,
    output_path: Path,
    include_paths: list[str],
) -> int:
    required_docs = _contract_required_documents(repo_root)
    relative_work_item = work_item_dir.relative_to(repo_root).as_posix()

    file_candidates: set[Path] = set()
    for document in required_docs:
        candidate = work_item_dir / document
        if candidate.is_file():
            file_candidates.add(candidate)

    for include in include_paths:
        raw = Path(include)
        if raw.is_absolute():
            candidate = raw
        else:
            candidate = work_item_dir / raw
            if not candidate.exists():
                candidate = repo_root / raw
        if not candidate.is_file():
            raise ValueError(f"--include path does not exist or is not a file: {include}")
        file_candidates.add(candidate.resolve())

    files_payload = []
    for file_path in sorted(file_candidates):
        try:
            repo_relative = file_path.relative_to(repo_root).as_posix()
        except ValueError:
            repo_relative = file_path.as_posix()
        files_payload.append(
            {
                "path": repo_relative,
                "sha256": _sha256(file_path),
                "bytes": file_path.stat().st_size,
            }
        )

    manifest = {
        "manifest_version": 1,
        "work_item": relative_work_item,
        "generated_by": "spec-evidence-manifest",
        "generated_at_utc": _utc_now(),
        "files": files_payload,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        f"[spec-evidence-manifest] wrote {output_path.relative_to(repo_root)} "
        f"with {len(files_payload)} file entries"
    )
    return 0


def _cmd_context_pack(*, repo_root: Path, work_item_dir: Path, output_path: Path) -> int:
    spec_path = work_item_dir / "spec.md"
    spec_content = spec_path.read_text(encoding="utf-8", errors="surrogateescape")
    readiness_section = _find_section_content(spec_content, "Readiness Gate")
    controls_section = _find_section_content(spec_content, "Applicable Guardrail Controls")
    readiness_fields = _parse_bullet_kv(readiness_section)

    required_docs = _contract_required_documents(repo_root)
    control_ids = sorted(set(re.findall(r"\bSDD-C-[0-9]{3}\b", controls_section)))

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    spec_raw = _as_mapping(contract.raw.get("spec"))
    sdd_raw = _as_mapping(spec_raw.get("spec_driven_development_contract"))
    readiness_raw = _as_mapping(sdd_raw.get("readiness_gate"))
    quality_raw = _as_mapping(sdd_raw.get("quality"))
    docs_commands = _as_list_of_str(readiness_raw.get("documentation_validation_commands"))
    commands: list[str] = []
    check_target = str(quality_raw.get("check_target", "")).strip()
    if check_target:
        commands.append(f"make {check_target}")
    commands.extend(["make quality-sdd-check-all", "make quality-hooks-run", "make infra-validate"])
    commands.extend(docs_commands)
    commands = list(dict.fromkeys(commands))

    lines: list[str] = []
    lines.append("# Work Item Context Pack")
    lines.append("")
    lines.append("## Context Snapshot")
    lines.append(f"- Work item: `{work_item_dir.relative_to(repo_root).as_posix()}`")
    lines.append("- Generated at (UTC): `" + _utc_now() + "`")
    lines.append("- SPEC_READY: `" + readiness_fields.get("spec_ready", "unknown") + "`")
    lines.append("- ADR path: `" + readiness_fields.get("adr path", "") + "`")
    lines.append("- ADR status: `" + readiness_fields.get("adr status", "") + "`")
    lines.append("")
    lines.append("## Guardrail Controls")
    if control_ids:
        lines.append("- Applicable control IDs: " + ", ".join(f"`{item}`" for item in control_ids))
    else:
        lines.append("- Applicable control IDs: none")
    lines.append("")
    lines.append("## Required Commands")
    for command in commands:
        lines.append(f"- `{command}`")
    lines.append("")
    lines.append("## Artifact Index")
    for document in required_docs:
        lines.append(f"- `{document}`")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[spec-context-pack] wrote {output_path.relative_to(repo_root)}")
    return 0


def _extract_bullets(content: str) -> list[str]:
    bullets: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*[-*]\s+(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if value:
            bullets.append(value)
    return bullets


def _cmd_pr_context(*, repo_root: Path, work_item_dir: Path, output_path: Path) -> int:
    spec_path = work_item_dir / "spec.md"
    traceability_path = work_item_dir / "traceability.md"
    plan_path = work_item_dir / "plan.md"
    context_pack_path = work_item_dir / "context_pack.md"
    hardening_review_path = work_item_dir / "hardening_review.md"
    evidence_manifest_path = work_item_dir / "evidence_manifest.json"

    spec_content = spec_path.read_text(encoding="utf-8", errors="surrogateescape")
    traceability_content = traceability_path.read_text(encoding="utf-8", errors="surrogateescape")
    plan_content = plan_path.read_text(encoding="utf-8", errors="surrogateescape")
    context_pack_content = context_pack_path.read_text(encoding="utf-8", errors="surrogateescape")
    hardening_review_content = hardening_review_path.read_text(encoding="utf-8", errors="surrogateescape")

    requirement_ids = sorted(set(re.findall(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3})\b", spec_content)))
    acceptance_ids = sorted(set(re.findall(r"\bAC-\d{3}\b", spec_content)))
    traceability_ids = sorted(
        set(re.findall(r"\b(?:FR-\d{3}|NFR-[A-Z]+-\d{3}|AC-\d{3})\b", traceability_content))
    )

    manifest_files: list[str] = []
    if evidence_manifest_path.is_file():
        manifest_payload = _load_json_or_yaml(evidence_manifest_path)
        files_raw = manifest_payload.get("files")
        if isinstance(files_raw, list):
            manifest_files = sorted(
                {
                    str(item.get("path", "")).strip()
                    for item in files_raw
                    if isinstance(item, dict) and str(item.get("path", "")).strip()
                }
            )

    required_commands = sorted(
        set(re.findall(r"`(make [^`]+)`", context_pack_content))
    )

    risk_section = _find_section_content(plan_content, "Risk")
    rollback_section = _find_section_content(plan_content, "Rollback")
    risk_bullets = _extract_bullets(risk_section)
    rollback_bullets = _extract_bullets(rollback_section)

    deferred_section = _find_section_content(hardening_review_content, "Proposals Only")
    deferred_bullets = _extract_bullets(deferred_section)

    lines: list[str] = []
    lines.append("# PR Context")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Work item: `{work_item_dir.relative_to(repo_root).as_posix()}`")
    lines.append(f"- Generated at (UTC): `{_utc_now()}`")
    lines.append("- Scope: SDD lifecycle artifact packaging for reviewer handoff.")
    lines.append("")
    lines.append("## Requirement Coverage")
    lines.append(
        "- Requirements (FR/NFR): "
        + (", ".join(f"`{item}`" for item in requirement_ids) if requirement_ids else "none detected in `spec.md`")
    )
    lines.append(
        "- Acceptance criteria (AC): "
        + (", ".join(f"`{item}`" for item in acceptance_ids) if acceptance_ids else "none detected in `spec.md`")
    )
    lines.append(
        "- Traceability IDs present: "
        + (", ".join(f"`{item}`" for item in traceability_ids) if traceability_ids else "none detected")
    )
    lines.append("")
    lines.append("## Key Reviewer Files")
    reviewer_files = manifest_files or [f"{work_item_dir.relative_to(repo_root).as_posix()}/spec.md"]
    for file_path in reviewer_files:
        lines.append(f"- `{file_path}`")
    lines.append("")
    lines.append("## Validation Evidence")
    if required_commands:
        for command in required_commands:
            lines.append(f"- `{command}`")
    else:
        lines.append("- No validation commands discovered in `context_pack.md`")
    lines.append("")
    lines.append("## Risk and Rollback")
    if risk_bullets:
        lines.append("- Risk notes:")
        for bullet in risk_bullets:
            lines.append(f"  - {bullet}")
    else:
        lines.append("- Risk notes: not explicitly captured under a `Risk` section in `plan.md`.")
    if rollback_bullets:
        lines.append("- Rollback notes:")
        for bullet in rollback_bullets:
            lines.append(f"  - {bullet}")
    else:
        lines.append("- Rollback notes: not explicitly captured under a `Rollback` section in `plan.md`.")
    lines.append("")
    lines.append("## Deferred Proposals")
    if deferred_bullets:
        for bullet in deferred_bullets:
            lines.append(f"- {bullet}")
    else:
        lines.append("- none recorded in `hardening_review.md`.")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[spec-pr-context] wrote {output_path.relative_to(repo_root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    impact_parser = subparsers.add_parser(
        "impact",
        help="Generate graph-based impact summary markdown for a work item.",
    )
    impact_parser.add_argument("--work-item", help="Work-item directory path or slug under specs/")
    impact_parser.add_argument(
        "--output",
        help="Output path for impact markdown (default: artifacts/spec/<work-item>/impact.md)",
    )

    manifest_parser = subparsers.add_parser(
        "evidence-manifest",
        help="Generate deterministic checksum evidence manifest for a work item.",
    )
    manifest_parser.add_argument("--work-item", help="Work-item directory path or slug under specs/")
    manifest_parser.add_argument(
        "--output",
        help="Output path for evidence manifest (default: <work-item>/evidence_manifest.json)",
    )
    manifest_parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Additional file path to include in evidence manifest (repeatable).",
    )

    context_parser = subparsers.add_parser(
        "context-pack",
        help="Generate normalized context pack markdown from work-item artifacts.",
    )
    context_parser.add_argument("--work-item", help="Work-item directory path or slug under specs/")
    context_parser.add_argument(
        "--output",
        help="Output path for context pack markdown (default: <work-item>/context_pack.md)",
    )

    pr_context_parser = subparsers.add_parser(
        "pr-context",
        help="Generate deterministic PR context markdown for a work item.",
    )
    pr_context_parser.add_argument("--work-item", help="Work-item directory path or slug under specs/")
    pr_context_parser.add_argument(
        "--output",
        help="Output path for PR context markdown (default: <work-item>/pr_context.md)",
    )

    args = parser.parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    work_item_dir = _resolve_work_item_dir(repo_root, getattr(args, "work_item", None))

    if args.command == "impact":
        if args.output:
            output_path = (Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output).resolve()
        else:
            output_path = (
                repo_root / "artifacts/spec" / work_item_dir.name / "impact.md"
            ).resolve()
        return _cmd_impact(repo_root=repo_root, work_item_dir=work_item_dir, output_path=output_path)

    if args.command == "evidence-manifest":
        if args.output:
            output_path = (Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output).resolve()
        else:
            output_path = (work_item_dir / "evidence_manifest.json").resolve()
        return _cmd_evidence_manifest(
            repo_root=repo_root,
            work_item_dir=work_item_dir,
            output_path=output_path,
            include_paths=list(args.include),
        )

    if args.command == "context-pack":
        if args.output:
            output_path = (Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output).resolve()
        else:
            output_path = (work_item_dir / "context_pack.md").resolve()
        return _cmd_context_pack(repo_root=repo_root, work_item_dir=work_item_dir, output_path=output_path)

    if args.command == "pr-context":
        if args.output:
            output_path = (Path(args.output) if Path(args.output).is_absolute() else repo_root / args.output).resolve()
        else:
            output_path = (work_item_dir / "pr_context.md").resolve()
        return _cmd_pr_context(repo_root=repo_root, work_item_dir=work_item_dir, output_path=output_path)

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
