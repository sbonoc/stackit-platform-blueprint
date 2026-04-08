#!/usr/bin/env python3
"""JSON helpers for ArgoCD repo credential reconciliation."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
from pathlib import Path
import sys


def cmd_render_source_patch(args: argparse.Namespace) -> int:
    payload = {
        "stringData": {
            "ARGOCD_REPO_TYPE": args.repo_type,
            "ARGOCD_REPO_URL": args.repo_url,
            "ARGOCD_REPO_USERNAME": args.repo_username,
            "ARGOCD_REPO_TOKEN": args.repo_token,
        }
    }
    Path(args.output_path).write_text(json.dumps(payload), encoding="utf-8")
    return 0


def _decode_secret_data(data: dict[str, object], key: str) -> str | None:
    raw = data.get(key)
    if not isinstance(raw, str) or raw == "":
        return None
    try:
        return base64.b64decode(raw, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        raise ValueError(f"target secret key '{key}' contains invalid base64 content")


def cmd_validate_target_secret(args: argparse.Namespace) -> int:
    try:
        secret = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"failed to parse target secret JSON from stdin: {exc.msg}", file=sys.stderr)
        return 1

    if not isinstance(secret, dict):
        print("failed to parse target secret JSON from stdin: expected top-level object", file=sys.stderr)
        return 1

    errors: list[str] = []

    labels = secret.get("metadata", {}).get("labels", {})
    if labels.get("argocd.argoproj.io/secret-type") != "repository":
        errors.append("target secret metadata.labels.argocd.argoproj.io/secret-type must equal repository")

    data = secret.get("data", {})
    for key in ("type", "url", "username", "password"):
        if not data.get(key):
            errors.append(f"target secret missing required data key: {key}")

    try:
        decoded_type = _decode_secret_data(data, "type")
    except ValueError as exc:
        errors.append(str(exc))
        decoded_type = None
    if decoded_type is not None and decoded_type != "git":
        errors.append(f"target secret key 'type' must decode to git; found {decoded_type}")

    try:
        decoded_url = _decode_secret_data(data, "url")
    except ValueError as exc:
        errors.append(str(exc))
        decoded_url = None
    if decoded_url is not None and decoded_url != args.expected_url:
        errors.append(f"target secret key 'url' must decode to {args.expected_url}; found {decoded_url}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    patch_parser = subparsers.add_parser("render-source-patch")
    patch_parser.add_argument("output_path")
    patch_parser.add_argument("repo_type")
    patch_parser.add_argument("repo_url")
    patch_parser.add_argument("repo_username")
    patch_parser.add_argument("repo_token")
    patch_parser.set_defaults(func=cmd_render_source_patch)

    validate_parser = subparsers.add_parser("validate-target-secret")
    validate_parser.add_argument("expected_url")
    validate_parser.set_defaults(func=cmd_validate_target_secret)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
