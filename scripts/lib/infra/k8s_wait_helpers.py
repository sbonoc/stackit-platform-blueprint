#!/usr/bin/env python3
"""Kubernetes wait helper utilities used by shell wrappers."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import socket
from urllib.parse import urlparse


def _extract_server_url(kubeconfig_path: Path) -> str:
    text = kubeconfig_path.read_text(encoding="utf-8")
    match = re.search(r"^\s*server:\s*(\S+)\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"server field not found in kubeconfig: {kubeconfig_path}")
    return match.group(1)


def cmd_server_url(args: argparse.Namespace) -> int:
    print(_extract_server_url(Path(args.kubeconfig_path)))
    return 0


def cmd_server_host(args: argparse.Namespace) -> int:
    parsed = urlparse(_extract_server_url(Path(args.kubeconfig_path)))
    if not parsed.hostname:
        raise ValueError(f"unable to parse hostname from kubeconfig server URL: {args.kubeconfig_path}")
    print(parsed.hostname)
    return 0


def cmd_dns_resolves(args: argparse.Namespace) -> int:
    try:
        socket.getaddrinfo(args.host, None)
    except OSError:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    server_url_parser = subparsers.add_parser("server-url")
    server_url_parser.add_argument("kubeconfig_path")
    server_url_parser.set_defaults(func=cmd_server_url)

    server_host_parser = subparsers.add_parser("server-host")
    server_host_parser.add_argument("kubeconfig_path")
    server_host_parser.set_defaults(func=cmd_server_host)

    dns_parser = subparsers.add_parser("dns-resolves")
    dns_parser.add_argument("host")
    dns_parser.set_defaults(func=cmd_dns_resolves)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
