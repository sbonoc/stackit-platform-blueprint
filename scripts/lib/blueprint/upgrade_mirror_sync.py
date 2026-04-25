"""Stage 6: Bootstrap template mirror sync for the scripted upgrade pipeline.

For every path mutated by Stages 2–5, checks whether a mirror exists under
scripts/templates/blueprint/bootstrap/<path> and overwrites it from the
workspace copy.

Requirement: FR-011.
"""
from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


_MIRROR_ROOT = "scripts/templates/blueprint/bootstrap"


@dataclass(frozen=True)
class MirrorSyncResult:
    success: bool
    message: str
    synced_paths: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "synced_paths": self.synced_paths,
        }


def sync_bootstrap_mirrors(
    repo_root: Path,
    modified_paths: list[str],
) -> MirrorSyncResult:
    """For each modified path, sync its bootstrap mirror if one exists.

    Args:
        repo_root: Absolute path to the consumer repository root.
        modified_paths: Repo-relative paths modified by Stages 2–5.

    Returns:
        MirrorSyncResult with the list of paths whose mirrors were updated.
    """
    mirror_root = repo_root / _MIRROR_ROOT
    synced: list[str] = []

    for rel_path in modified_paths:
        workspace_file = repo_root / rel_path
        mirror_file = mirror_root / rel_path

        if not mirror_file.exists():
            continue
        if not workspace_file.exists():
            continue

        mirror_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(workspace_file), str(mirror_file))
        synced.append(rel_path)

    return MirrorSyncResult(
        success=True,
        message=f"mirror sync complete: {len(synced)} mirror(s) updated",
        synced_paths=synced,
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Stage 6: sync bootstrap template mirrors for modified workspace files.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--modified-paths-json",
        type=Path,
        default=None,
        help="JSON file containing a list of repo-relative modified paths.",
    )
    args = parser.parse_args()

    if args.modified_paths_json and args.modified_paths_json.exists():
        modified_paths = json.loads(args.modified_paths_json.read_text(encoding="utf-8"))
    else:
        # Fall back to scanning all files in the mirror root that also exist in workspace.
        mirror_root = args.repo_root / _MIRROR_ROOT
        if not mirror_root.exists():
            print("[PIPELINE] Stage 6: no bootstrap mirror root found; skipping.")
            return 0
        modified_paths = [
            str(p.relative_to(mirror_root))
            for p in mirror_root.rglob("*")
            if p.is_file()
        ]

    result = sync_bootstrap_mirrors(args.repo_root, modified_paths)
    print(f"[PIPELINE] Stage 6: {result.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
