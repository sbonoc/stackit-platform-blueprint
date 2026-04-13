#!/usr/bin/env python3
"""Helpers for runtime ESO target secret contract verification."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Literal


TargetSecretCheckStatus = Literal["ready", "missing-secret", "missing-keys", "verify-error"]

TARGET_SECRET_CHECK_KIND = "runtime-target-secret-contract-check"
TARGET_SECRET_CHECK_SCHEMA_VERSION = "v1"
TARGET_SECRET_CHECK_REPORT_KIND = "runtime-target-secret-contract-check-report"
TARGET_SECRET_CHECK_REPORT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class TargetSecretContractCheck:
    kind: str
    schemaVersion: str
    checkedAtUtc: str
    namespace: str
    secretName: str
    requiredKeys: list[str]
    observedKeys: list[str]
    missingKeys: list[str]
    status: TargetSecretCheckStatus
    reason: str
    verifyError: str

    @classmethod
    def build(
        cls,
        *,
        namespace: str,
        secret_name: str,
        required_keys: list[str],
        observed_keys: list[str],
        missing_keys: list[str],
        status: TargetSecretCheckStatus,
        reason: str,
        verify_error: str,
    ) -> TargetSecretContractCheck:
        return cls(
            kind=TARGET_SECRET_CHECK_KIND,
            schemaVersion=TARGET_SECRET_CHECK_SCHEMA_VERSION,
            checkedAtUtc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            namespace=namespace,
            secretName=secret_name,
            requiredKeys=required_keys,
            observedKeys=observed_keys,
            missingKeys=missing_keys,
            status=status,
            reason=reason,
            verifyError=verify_error,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TargetSecretContractCheckReport:
    kind: str
    schemaVersion: str
    generatedAtUtc: str
    counts: dict[str, int]
    checks: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _parse_json_candidate(candidate: str) -> dict[str, object] | None:
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _parse_secret_payload(raw_payload: str) -> dict[str, object] | None:
    payload = _parse_json_candidate(raw_payload)
    if payload is not None:
        return payload

    compact = raw_payload.strip()
    start = compact.find("{")
    end = compact.rfind("}")
    if start == -1 or end <= start:
        return None
    return _parse_json_candidate(compact[start : end + 1])


def _split_required_keys(keys_csv: str) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for item in keys_csv.split(","):
        key = item.strip()
        if key == "" or key in seen:
            continue
        keys.append(key)
        seen.add(key)
    return keys


def _exit_code_for_status(status: TargetSecretCheckStatus) -> int:
    if status == "ready":
        return 0
    if status in {"missing-secret", "missing-keys"}:
        return 1
    return 2


def _csv_or_none(values: list[str]) -> str:
    if not values:
        return "none"
    return ",".join(values)


def check_target_secret_contract(
    *,
    namespace: str,
    secret_name: str,
    required_keys: list[str],
    secret_present: bool,
    raw_payload: str,
) -> TargetSecretContractCheck:
    if not secret_present:
        return TargetSecretContractCheck.build(
            namespace=namespace,
            secret_name=secret_name,
            required_keys=required_keys,
            observed_keys=[],
            missing_keys=required_keys,
            status="missing-secret",
            reason="missing-target-secret",
            verify_error="none",
        )

    if raw_payload.strip() == "":
        return TargetSecretContractCheck.build(
            namespace=namespace,
            secret_name=secret_name,
            required_keys=required_keys,
            observed_keys=[],
            missing_keys=[],
            status="verify-error",
            reason="empty-secret-json",
            verify_error="empty-secret-json",
        )

    payload = _parse_secret_payload(raw_payload)
    if payload is None:
        return TargetSecretContractCheck.build(
            namespace=namespace,
            secret_name=secret_name,
            required_keys=required_keys,
            observed_keys=[],
            missing_keys=[],
            status="verify-error",
            reason="invalid-secret-json",
            verify_error="invalid-secret-json",
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        return TargetSecretContractCheck.build(
            namespace=namespace,
            secret_name=secret_name,
            required_keys=required_keys,
            observed_keys=[],
            missing_keys=[],
            status="verify-error",
            reason="missing-secret-data-map",
            verify_error="missing-secret-data-map",
        )

    observed_keys = [str(key).strip() for key in data if str(key).strip() != ""]
    missing_keys: list[str] = []
    for key in required_keys:
        value = data.get(key)
        if value is None or str(value).strip() == "":
            missing_keys.append(key)

    if missing_keys:
        return TargetSecretContractCheck.build(
            namespace=namespace,
            secret_name=secret_name,
            required_keys=required_keys,
            observed_keys=sorted(observed_keys),
            missing_keys=missing_keys,
            status="missing-keys",
            reason="missing-required-keys",
            verify_error="none",
        )

    return TargetSecretContractCheck.build(
        namespace=namespace,
        secret_name=secret_name,
        required_keys=required_keys,
        observed_keys=sorted(observed_keys),
        missing_keys=[],
        status="ready",
        reason="ok",
        verify_error="none",
    )


def _write_json(path: str | None, payload: dict[str, object]) -> None:
    if not path:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_verify_required_keys(args: argparse.Namespace) -> int:
    required_keys = _split_required_keys(args.keys_csv)
    raw_payload = sys.stdin.read()
    check = check_target_secret_contract(
        namespace="unknown",
        secret_name="unknown",
        required_keys=required_keys,
        secret_present=True,
        raw_payload=raw_payload,
    )

    if check.status == "ready":
        print("ok")
        return 0
    if check.status == "missing-keys":
        print(" ".join(check.missingKeys))
        return 1
    print(f"__verify_error__:{check.reason}")
    return 2


def cmd_check_target_secret(args: argparse.Namespace) -> int:
    required_keys = _split_required_keys(args.required_keys)
    secret_present = args.secret_present == "true"
    raw_payload = sys.stdin.read() if secret_present else ""
    check = check_target_secret_contract(
        namespace=args.namespace,
        secret_name=args.secret_name,
        required_keys=required_keys,
        secret_present=secret_present,
        raw_payload=raw_payload,
    )
    payload = check.to_dict()
    _write_json(args.output_json, payload)

    if args.summary:
        print(f"{check.status}\t{_csv_or_none(check.missingKeys)}\t{check.reason}")
    else:
        print(json.dumps(payload, sort_keys=True))
    return _exit_code_for_status(check.status)


def _parse_check_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object")
    return payload


def cmd_render_check_report(args: argparse.Namespace) -> int:
    checks: list[dict[str, object]] = []
    counts = {
        "total": 0,
        "ready": 0,
        "missingSecret": 0,
        "missingKeys": 0,
        "verifyError": 0,
    }

    for check_file in args.check_files:
        payload = _parse_check_payload(Path(check_file))
        status = payload.get("status")
        if not isinstance(status, str):
            raise ValueError(f"{check_file}: missing string status field")
        checks.append(payload)
        counts["total"] += 1
        if status == "ready":
            counts["ready"] += 1
        elif status == "missing-secret":
            counts["missingSecret"] += 1
        elif status == "missing-keys":
            counts["missingKeys"] += 1
        elif status == "verify-error":
            counts["verifyError"] += 1
        else:
            raise ValueError(f"{check_file}: unsupported status '{status}'")

    report = TargetSecretContractCheckReport(
        kind=TARGET_SECRET_CHECK_REPORT_KIND,
        schemaVersion=TARGET_SECRET_CHECK_REPORT_SCHEMA_VERSION,
        generatedAtUtc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        counts=counts,
        checks=checks,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(output_path))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify-required-keys")
    verify_parser.add_argument("keys_csv")
    verify_parser.set_defaults(func=cmd_verify_required_keys)

    check_parser = subparsers.add_parser("check-target-secret")
    check_parser.add_argument("--namespace", required=True)
    check_parser.add_argument("--secret-name", required=True)
    check_parser.add_argument("--required-keys", required=True)
    check_parser.add_argument(
        "--secret-present",
        choices=("true", "false"),
        default="true",
    )
    check_parser.add_argument("--summary", action="store_true")
    check_parser.add_argument("--output-json")
    check_parser.set_defaults(func=cmd_check_target_secret)

    report_parser = subparsers.add_parser("render-check-report")
    report_parser.add_argument("--output", required=True)
    report_parser.add_argument("check_files", nargs="*")
    report_parser.set_defaults(func=cmd_render_check_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
