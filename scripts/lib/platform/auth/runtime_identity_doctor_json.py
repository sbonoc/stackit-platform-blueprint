#!/usr/bin/env python3
"""Helpers for runtime identity doctor consolidated diagnostics."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Literal


DoctorStatus = Literal["success", "success-with-warnings", "failed"]
IssueSeverity = Literal["warning", "failure"]

DOCTOR_REPORT_KIND = "runtime-identity-doctor-report"
DOCTOR_REPORT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class ArtifactState:
    name: str
    path: str
    present: bool
    status: str
    entries: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorIssue:
    severity: IssueSeverity
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_path(path_value: str) -> Path | None:
    normalized = path_value.strip()
    if normalized in {"", "none", "None", "N/A"}:
        return None
    return Path(normalized)


def _load_env_entries(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key == "":
            continue
        entries[key] = value
    return entries


def _load_artifact_state(name: str, path_value: str) -> ArtifactState:
    artifact_path = _optional_path(path_value)
    if artifact_path is None:
        return ArtifactState(name=name, path="none", present=False, status="missing", entries={})
    if not artifact_path.is_file():
        return ArtifactState(name=name, path=str(artifact_path), present=False, status="missing", entries={})
    entries = _load_env_entries(artifact_path)
    status = entries.get("status", "unknown")
    return ArtifactState(
        name=name,
        path=str(artifact_path),
        present=True,
        status=status,
        entries=entries,
    )


def _safe_int(value: object, *, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return fallback
        try:
            return int(text)
        except ValueError:
            return fallback
    return fallback


def _default_target_secret_counts() -> dict[str, int]:
    return {
        "total": 0,
        "ready": 0,
        "missingSecret": 0,
        "missingKeys": 0,
        "verifyError": 0,
    }


def _load_target_secret_report(path_value: str) -> tuple[bool, str, dict[str, int], list[DoctorIssue]]:
    report_path = _optional_path(path_value)
    if report_path is None:
        return False, "none", _default_target_secret_counts(), []
    if not report_path.is_file():
        return False, str(report_path), _default_target_secret_counts(), []

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"target secret report must be a JSON object: {report_path}")
    counts_raw = payload.get("counts")
    if not isinstance(counts_raw, dict):
        raise ValueError(f"target secret report is missing object field 'counts': {report_path}")

    counts = _default_target_secret_counts()
    for key in counts:
        counts[key] = _safe_int(counts_raw.get(key), fallback=0)
    return True, str(report_path), counts, []


def _append_issue(
    issues: list[DoctorIssue],
    *,
    severity: IssueSeverity,
    code: str,
    message: str,
) -> None:
    issues.append(DoctorIssue(severity=severity, code=code, message=message))


def _summarize_state_health(issues: list[DoctorIssue], state: ArtifactState) -> None:
    if not state.present:
        _append_issue(
            issues,
            severity="failure",
            code=f"missing-{state.name}-state",
            message=f"required artifact state for {state.name} is missing: {state.path}",
        )
        return

    status = state.status.strip()
    if status.startswith("failed"):
        _append_issue(
            issues,
            severity="failure",
            code=f"{state.name}-failed",
            message=f"{state.name} reported failure status '{status}'",
        )
        return

    if status in {"warn-and-skip", "success-with-warnings"}:
        _append_issue(
            issues,
            severity="warning",
            code=f"{state.name}-warnings",
            message=f"{state.name} reported warning status '{status}'",
        )

    if status in {"missing", "unknown"}:
        _append_issue(
            issues,
            severity="warning",
            code=f"{state.name}-unknown-status",
            message=f"{state.name} did not report a canonical status value",
        )


def _split_csv(csv_value: str) -> list[str]:
    values: list[str] = []
    for raw in csv_value.split(","):
        normalized = raw.strip()
        if normalized == "" or normalized in values:
            continue
        values.append(normalized)
    return values


def _render_report(args: argparse.Namespace) -> tuple[dict[str, object], dict[str, int]]:
    runtime_identity_state = _load_artifact_state("runtimeIdentityReconcile", args.runtime_identity_state)
    runtime_credentials_state = _load_artifact_state("runtimeCredentialsEsoReconcile", args.runtime_credentials_state)
    argocd_repo_state = _load_artifact_state("argocdRepoCredentialsReconcile", args.argocd_state)

    target_secret_present, target_secret_path, target_secret_counts, _target_secret_issues = _load_target_secret_report(
        args.target_secret_report
    )

    issues: list[DoctorIssue] = []
    refresh_status = args.refresh_status.strip()
    if refresh_status not in {"success", "skipped"}:
        _append_issue(
            issues,
            severity="failure",
            code="doctor-refresh-failed",
            message=f"runtime identity doctor refresh did not complete successfully: {refresh_status}",
        )

    _summarize_state_health(issues, runtime_identity_state)
    _summarize_state_health(issues, runtime_credentials_state)
    _summarize_state_health(issues, argocd_repo_state)

    if target_secret_present:
        if target_secret_counts["verifyError"] > 0:
            _append_issue(
                issues,
                severity="failure",
                code="target-secret-verify-errors",
                message=(
                    "runtime target-secret diagnostics contain verify-error checks "
                    f"({target_secret_counts['verifyError']})"
                ),
            )
        if target_secret_counts["missingSecret"] > 0:
            _append_issue(
                issues,
                severity="warning",
                code="target-secret-missing-secret",
                message=(
                    "runtime target-secret diagnostics contain missing target secret checks "
                    f"({target_secret_counts['missingSecret']})"
                ),
            )
        if target_secret_counts["missingKeys"] > 0:
            _append_issue(
                issues,
                severity="warning",
                code="target-secret-missing-keys",
                message=(
                    "runtime target-secret diagnostics contain missing key checks "
                    f"({target_secret_counts['missingKeys']})"
                ),
            )
    elif runtime_credentials_state.present and runtime_credentials_state.entries.get("tooling_mode", "") == "execute":
        _append_issue(
            issues,
            severity="warning",
            code="missing-target-secret-report",
            message="runtime target-secret diagnostics report is missing in execute mode",
        )

    contract_eso_expected = max(0, args.contract_eso_expected)
    contract_eso_enabled = max(0, args.contract_eso_enabled)
    contract_keycloak_expected = max(0, args.contract_keycloak_expected)
    contract_keycloak_enabled = max(0, args.contract_keycloak_enabled)

    if contract_eso_enabled > contract_eso_expected:
        _append_issue(
            issues,
            severity="failure",
            code="contract-eso-count-invalid",
            message=(
                "contract diagnostics reported enabled ESO contracts greater than expected count "
                f"({contract_eso_enabled}>{contract_eso_expected})"
            ),
        )
    if contract_keycloak_enabled > contract_keycloak_expected:
        _append_issue(
            issues,
            severity="failure",
            code="contract-keycloak-count-invalid",
            message=(
                "contract diagnostics reported enabled Keycloak realms greater than expected count "
                f"({contract_keycloak_enabled}>{contract_keycloak_expected})"
            ),
        )

    if runtime_identity_state.present:
        checked_realms = _safe_int(runtime_identity_state.entries.get("keycloak_realm_check_count"), fallback=-1)
        expected_keycloak_contracts = _safe_int(
            runtime_identity_state.entries.get("keycloak_expected_contract_count"),
            fallback=-1,
        )
        if checked_realms >= 0 and checked_realms != contract_keycloak_enabled:
            _append_issue(
                issues,
                severity="warning",
                code="keycloak-realm-check-count-mismatch",
                message=(
                    "runtime identity reconcile checked realm count does not match enabled contract realm count "
                    f"({checked_realms}!={contract_keycloak_enabled})"
                ),
            )
        if expected_keycloak_contracts >= 0 and expected_keycloak_contracts != contract_keycloak_enabled:
            _append_issue(
                issues,
                severity="warning",
                code="keycloak-expected-contract-count-mismatch",
                message=(
                    "runtime identity reconcile expected contract count does not match enabled contract realm count "
                    f"({expected_keycloak_contracts}!={contract_keycloak_enabled})"
                ),
            )

    failure_count = sum(1 for issue in issues if issue.severity == "failure")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status: DoctorStatus = "success"
    if failure_count > 0:
        status = "failed"
    elif warning_count > 0:
        status = "success-with-warnings"

    report = {
        "kind": DOCTOR_REPORT_KIND,
        "schemaVersion": DOCTOR_REPORT_SCHEMA_VERSION,
        "generatedAtUtc": _utc_now(),
        "execution": {
            "profile": args.profile,
            "stack": args.stack,
            "toolingMode": args.tooling_mode,
            "refreshStatus": refresh_status,
        },
        "summary": {
            "status": status,
            "issueCount": len(issues),
            "failureCount": failure_count,
            "warningCount": warning_count,
        },
        "contract": {
            "eso": {
                "expectedCount": contract_eso_expected,
                "enabledCount": contract_eso_enabled,
                "enabledContracts": _split_csv(args.contract_eso_enabled_contracts),
            },
            "keycloak": {
                "expectedRealmCount": contract_keycloak_expected,
                "enabledRealmCount": contract_keycloak_enabled,
                "enabledRealms": _split_csv(args.contract_keycloak_enabled_realms),
            },
        },
        "artifacts": {
            "runtimeIdentityReconcile": runtime_identity_state.to_dict(),
            "runtimeCredentialsEsoReconcile": runtime_credentials_state.to_dict(),
            "argocdRepoCredentialsReconcile": argocd_repo_state.to_dict(),
            "targetSecretCheckReport": {
                "path": target_secret_path,
                "present": target_secret_present,
                "counts": target_secret_counts,
            },
        },
        "issues": [issue.to_dict() for issue in issues],
    }

    summary_metrics = {
        "status": status,
        "issueCount": len(issues),
        "failureCount": failure_count,
        "warningCount": warning_count,
        "targetTotal": target_secret_counts["total"],
        "targetReady": target_secret_counts["ready"],
        "targetMissingSecret": target_secret_counts["missingSecret"],
        "targetMissingKeys": target_secret_counts["missingKeys"],
        "targetVerifyError": target_secret_counts["verifyError"],
    }
    return report, summary_metrics


def cmd_render_report(args: argparse.Namespace) -> int:
    report, summary = _render_report(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "\t".join(
            [
                str(summary["status"]),
                str(summary["issueCount"]),
                str(summary["failureCount"]),
                str(summary["warningCount"]),
                str(summary["targetTotal"]),
                str(summary["targetReady"]),
                str(summary["targetMissingSecret"]),
                str(summary["targetMissingKeys"]),
                str(summary["targetVerifyError"]),
            ]
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render-report")
    render.add_argument("--output", required=True)
    render.add_argument("--profile", required=True)
    render.add_argument("--stack", required=True)
    render.add_argument("--tooling-mode", required=True)
    render.add_argument("--refresh-status", required=True)
    render.add_argument("--runtime-identity-state", default="none")
    render.add_argument("--runtime-credentials-state", default="none")
    render.add_argument("--argocd-state", default="none")
    render.add_argument("--target-secret-report", default="none")
    render.add_argument("--contract-eso-expected", type=int, required=True)
    render.add_argument("--contract-eso-enabled", type=int, required=True)
    render.add_argument("--contract-keycloak-expected", type=int, required=True)
    render.add_argument("--contract-keycloak-enabled", type=int, required=True)
    render.add_argument("--contract-eso-enabled-contracts", default="")
    render.add_argument("--contract-keycloak-enabled-realms", default="")
    render.set_defaults(func=cmd_render_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
