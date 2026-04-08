#!/usr/bin/env python3
"""ArgoCD GitHub repository URL contract helpers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402


ARGOCD_REPOSITORY_IDENTITY_PATHS: tuple[Path, ...] = (
    Path("infra/gitops/argocd/root/applicationset-platform-environments.yaml"),
    Path("infra/gitops/argocd/environments/dev/platform-application.yaml"),
    Path("infra/gitops/argocd/environments/stage/platform-application.yaml"),
    Path("infra/gitops/argocd/environments/prod/platform-application.yaml"),
    Path("infra/gitops/argocd/overlays/local/appproject.yaml"),
    Path("infra/gitops/argocd/overlays/local/application-platform-local.yaml"),
    Path("infra/gitops/argocd/overlays/dev/appproject.yaml"),
    Path("infra/gitops/argocd/overlays/dev/applicationset-platform-environments.yaml"),
    Path("infra/gitops/argocd/overlays/stage/appproject.yaml"),
    Path("infra/gitops/argocd/overlays/stage/applicationset-platform-environments.yaml"),
    Path("infra/gitops/argocd/overlays/prod/appproject.yaml"),
    Path("infra/gitops/argocd/overlays/prod/applicationset-platform-environments.yaml"),
)

GITHUB_REPO_HTTPS_PATTERN = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$")
REPO_URL_KEY_PATTERN = re.compile(r"^\s*repoURL:\s*(?P<url>\S+)\s*$")
LIST_ENTRY_PATTERN = re.compile(r"^\s*-\s*(?P<value>\S+)\s*$")
REPO_URL_REWRITE_PATTERN = re.compile(
    r"(^\s*repoURL:\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
    flags=re.MULTILINE,
)
LIST_REWRITE_PATTERN = re.compile(
    r"(^\s*-\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
    flags=re.MULTILINE,
)
GITHUB_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class RepoUrlOccurrence:
    path: Path
    line_number: int
    value: str


def canonical_github_https_repo_url(github_org: str, github_repo: str) -> str:
    org = github_org.strip()
    repo = github_repo.strip()
    if not GITHUB_SEGMENT_PATTERN.fullmatch(org):
        raise ValueError(f"github org is invalid; expected [A-Za-z0-9_.-]+, got {github_org!r}")
    if not GITHUB_SEGMENT_PATTERN.fullmatch(repo):
        raise ValueError(f"github repo is invalid; expected [A-Za-z0-9_.-]+, got {github_repo!r}")
    return f"https://github.com/{org}/{repo}.git"


def render_argocd_repo_url_replacements(content: str, repo_url: str) -> str:
    if not GITHUB_REPO_HTTPS_PATTERN.fullmatch(repo_url):
        raise ValueError(
            "repo_url must use HTTPS GitHub URL format (https://github.com/<org>/<repo>.git); "
            f"found {repo_url}"
        )
    updated = REPO_URL_REWRITE_PATTERN.sub(rf"\g<1>{repo_url}\g<2>", content)
    updated = LIST_REWRITE_PATTERN.sub(rf"\g<1>{repo_url}\g<2>", updated)
    return updated


def _collect_occurrences(repo_root: Path) -> list[RepoUrlOccurrence]:
    occurrences: list[RepoUrlOccurrence] = []
    for relative_path in ARGOCD_REPOSITORY_IDENTITY_PATHS:
        path = repo_root / relative_path
        if not path.is_file():
            continue
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = raw_line.strip()
            value = ""
            repo_match = REPO_URL_KEY_PATTERN.match(raw_line)
            if repo_match:
                value = repo_match.group("url")
            else:
                list_match = LIST_ENTRY_PATTERN.match(raw_line)
                if list_match and "github.com" in stripped:
                    value = list_match.group("value")
            if not value:
                continue
            value = value.strip().strip('"').strip("'")
            if "github.com" not in value:
                continue
            occurrences.append(RepoUrlOccurrence(path=relative_path, line_number=line_number, value=value))
    return occurrences


def validate_argocd_https_repo_url_contract(repo_root: Path) -> list[str]:
    errors: list[str] = []
    occurrences = _collect_occurrences(repo_root)
    if not occurrences:
        return [
            "missing ArgoCD GitHub repository URL references in managed repo identity manifests; "
            "run blueprint-init-repo or restore init-managed Argo files"
        ]

    unique_values = sorted({item.value for item in occurrences})
    for item in occurrences:
        if GITHUB_REPO_HTTPS_PATTERN.fullmatch(item.value):
            continue
        errors.append(
            f"{item.path.as_posix()}:{item.line_number} must use HTTPS GitHub URL "
            f"(https://github.com/<org>/<repo>.git); found {item.value}"
        )

    if len(unique_values) > 1:
        errors.append(
            "ArgoCD GitHub repository URL mismatch across managed manifests: " + ", ".join(unique_values)
        )
    return errors


def canonical_argocd_https_repo_url(repo_root: Path) -> str:
    errors = validate_argocd_https_repo_url_contract(repo_root)
    if errors:
        raise ValueError("\n".join(errors))
    occurrences = _collect_occurrences(repo_root)
    values = sorted({item.value for item in occurrences})
    if len(values) != 1:
        raise ValueError("unable to resolve canonical ArgoCD GitHub repository URL")
    return values[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve managed ArgoCD manifests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate HTTPS URL shape and consistency across ArgoCD repo identity manifests.")
    subparsers.add_parser("canonical-url", help="Print canonical HTTPS GitHub repo URL from managed ArgoCD manifests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)

    if args.command == "validate":
        errors = validate_argocd_https_repo_url_contract(repo_root)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(canonical_argocd_https_repo_url(repo_root))
        return 0

    if args.command == "canonical-url":
        try:
            print(canonical_argocd_https_repo_url(repo_root))
        except ValueError as exc:
            for line in str(exc).splitlines():
                print(line, file=sys.stderr)
            return 1
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
