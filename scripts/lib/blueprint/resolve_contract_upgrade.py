"""Stage 3: Deterministic contract file resolution for the scripted upgrade pipeline.

Reads the conflict JSON produced by the upgrade engine for blueprint/contract.yaml
and applies explicit merge rules so consumer identity fields always survive:

  - Preserves consumer identity: metadata.name, spec.repository.repo_mode,
    spec.repository.description (FR-005).
  - Merges spec.repository.required_files additively: takes all blueprint entries
    from source_content; retains consumer-added entries whose files exist on disk;
    drops consumer-added entries whose files no longer exist (FR-006).
  - Takes spec.repository.consumer_init.source_artifact_prune_globs_on_init from
    source_content only; drops any blueprint glob that matches existing paths in
    the consumer root (FR-007).
  - All other fields: taken from source_content (blueprint-managed).

Emits artifacts/blueprint/contract_resolve_decisions.json (FR-008).
"""
from __future__ import annotations

import fnmatch
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContractResolveResult:
    success: bool
    message: str
    dropped_required_files: list[str] = field(default_factory=list)
    kept_consumer_required_files: list[str] = field(default_factory=list)
    dropped_prune_globs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "dropped_required_files": self.dropped_required_files,
            "kept_consumer_required_files": self.kept_consumer_required_files,
            "dropped_prune_globs": self.dropped_prune_globs,
        }


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_CONFLICT_JSON_RELATIVE = "artifacts/blueprint/conflicts/blueprint/contract.yaml.conflict.json"
_DECISIONS_JSON_RELATIVE = "artifacts/blueprint/contract_resolve_decisions.json"
_CONTRACT_RELATIVE = "blueprint/contract.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_nested(data: dict, *keys: str, default=None):
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur


def _glob_matches_any(pattern: str, repo_root: Path) -> bool:
    """Return True if the glob pattern matches at least one existing path under repo_root."""
    for candidate in repo_root.rglob("*"):
        rel = str(candidate.relative_to(repo_root))
        if fnmatch.fnmatch(rel, pattern):
            return True
    return False


def _merge_required_files(
    source_entries: list[str],
    target_entries: list[str],
    repo_root: Path,
) -> tuple[list[str], list[str], list[str]]:
    """Merge required_files per FR-006.

    Returns (merged, kept_consumer_additions, dropped_consumer_additions).
    """
    source_set = set(source_entries)
    kept: list[str] = []
    dropped: list[str] = []

    for path in target_entries:
        if path in source_set:
            continue  # already covered by blueprint entries
        if (repo_root / path).exists():
            kept.append(path)
        else:
            dropped.append(path)

    merged = list(source_entries) + kept
    return merged, kept, dropped


def _filter_prune_globs(
    source_globs: list[str],
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    """Filter prune globs per FR-007.

    Returns (kept_globs, dropped_globs).
    Globs that match existing consumer content are dropped to prevent
    accidental deletion of real consumer work.
    """
    kept: list[str] = []
    dropped: list[str] = []
    for glob in source_globs:
        if _glob_matches_any(glob, repo_root):
            dropped.append(glob)
        else:
            kept.append(glob)
    return kept, dropped


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------


def resolve_contract_conflict(repo_root: Path) -> ContractResolveResult:
    """Resolve blueprint/contract.yaml conflict using deterministic merge rules.

    If the conflict JSON does not exist, this is a no-op (the contract was not
    conflicted during apply) and the function returns success immediately.
    """
    conflict_path = repo_root / _CONFLICT_JSON_RELATIVE
    if not conflict_path.exists():
        return ContractResolveResult(
            success=True,
            message="no-op: blueprint/contract.yaml conflict JSON not present",
        )

    try:
        conflict = json.loads(conflict_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ContractResolveResult(
            success=False,
            message=f"failed to parse conflict JSON at {conflict_path}: {exc}",
        )

    try:
        source = yaml.safe_load(conflict.get("source_content", "")) or {}
        target = yaml.safe_load(conflict.get("target_content", "")) or {}
    except Exception as exc:
        return ContractResolveResult(
            success=False,
            message=f"failed to parse contract YAML from conflict JSON: {exc}",
        )

    # Start with source (blueprint-managed) as the base.
    resolved = source.copy()

    # FR-005 — Preserve consumer identity fields.
    if "metadata" not in resolved:
        resolved["metadata"] = {}
    if "name" in (target.get("metadata") or {}):
        resolved["metadata"]["name"] = target["metadata"]["name"]

    target_repo = _get_nested(target, "spec", "repository") or {}
    source_repo = _get_nested(source, "spec", "repository") or {}

    if "spec" not in resolved:
        resolved["spec"] = {}
    if "repository" not in resolved["spec"]:
        resolved["spec"]["repository"] = {}

    if "repo_mode" in target_repo:
        resolved["spec"]["repository"]["repo_mode"] = target_repo["repo_mode"]
    if "description" in target_repo:
        resolved["spec"]["repository"]["description"] = target_repo["description"]

    # FR-006 — Merge required_files additively.
    source_required: list[str] = source_repo.get("required_files") or []
    target_required: list[str] = target_repo.get("required_files") or []
    merged_required, kept_consumer, dropped_consumer = _merge_required_files(
        source_required, target_required, repo_root
    )
    resolved["spec"]["repository"]["required_files"] = merged_required

    # FR-007 — Filter prune globs from source only; drop those matching consumer content.
    source_consumer_init = _get_nested(source, "spec", "repository", "consumer_init") or {}
    source_prune_globs: list[str] = source_consumer_init.get(
        "source_artifact_prune_globs_on_init"
    ) or []
    kept_globs, dropped_globs = _filter_prune_globs(source_prune_globs, repo_root)
    if "consumer_init" not in resolved["spec"]["repository"]:
        resolved["spec"]["repository"]["consumer_init"] = {}
    resolved["spec"]["repository"]["consumer_init"][
        "source_artifact_prune_globs_on_init"
    ] = kept_globs

    # Write resolved contract YAML.
    contract_path = repo_root / _CONTRACT_RELATIVE
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        yaml.dump(resolved, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # FR-008 — Emit decision JSON.
    decisions = {
        "path": "blueprint/contract.yaml",
        "dropped_required_files": dropped_consumer,
        "kept_consumer_required_files": kept_consumer,
        "dropped_prune_globs": dropped_globs,
        "kept_prune_globs": kept_globs,
    }
    decisions_path = repo_root / _DECISIONS_JSON_RELATIVE
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    decisions_path.write_text(json.dumps(decisions, indent=2), encoding="utf-8")

    return ContractResolveResult(
        success=True,
        message="blueprint/contract.yaml resolved using deterministic merge rules",
        dropped_required_files=dropped_consumer,
        kept_consumer_required_files=kept_consumer,
        dropped_prune_globs=dropped_globs,
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Stage 3: resolve blueprint/contract.yaml conflict.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    result = resolve_contract_conflict(args.repo_root)
    if result.success:
        print(f"[PIPELINE] Stage 3: {result.message}")
        if result.dropped_required_files:
            print(
                f"[PIPELINE] Stage 3: dropped {len(result.dropped_required_files)} "
                f"consumer required_files entries (files absent from disk): "
                f"{result.dropped_required_files}"
            )
        if result.dropped_prune_globs:
            print(
                f"[PIPELINE] Stage 3: dropped {len(result.dropped_prune_globs)} "
                f"prune globs matching existing consumer paths: {result.dropped_prune_globs}"
            )
        return 0
    print(f"[PIPELINE] Stage 3: FAILED — {result.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
