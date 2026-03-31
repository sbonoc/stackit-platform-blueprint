#!/usr/bin/env python3
"""Runtime identity contract helpers.

This module centralizes the Keycloak + ESO runtime identity surface so scripts,
docs, and generated manifests consume one canonical contract file.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_yaml_subset  # noqa: E402


DEFAULT_CONTRACT_PATH = Path("blueprint/runtime_identity_contract.yaml")


@dataclass(frozen=True)
class RuntimeEnvDefault:
    name: str
    default: str


@dataclass(frozen=True)
class EsoDataMapping:
    secret_key: str
    source_property: str


@dataclass(frozen=True)
class EsoSecretContract:
    contract_id: str
    module_id: str
    namespace: str
    external_secret_name: str
    target_secret_name: str
    data_mappings: list[EsoDataMapping]

    @property
    def target_secret_keys(self) -> list[str]:
        return [item.secret_key for item in self.data_mappings]


@dataclass(frozen=True)
class KeycloakRealmContract:
    realm_id: str
    module_id: str
    realm_env: str
    default_realm_name: str
    client_display_name: str
    client_id_env: str
    client_secret_env: str
    role_names: list[str]
    admin_username_env: str
    admin_password_env: str
    admin_role: str

    def resolved_realm_name(self) -> str:
        value = os.environ.get(self.realm_env, "").strip()
        return value if value else self.default_realm_name


@dataclass(frozen=True)
class RuntimeIdentityContract:
    runtime_env_defaults: list[RuntimeEnvDefault]
    eso_source_secret_key: str
    eso_store_kind: str
    eso_store_name: str
    eso_contracts: list[EsoSecretContract]
    keycloak_namespace: str
    keycloak_helm_release_env: str
    keycloak_admin_secret_name: str
    keycloak_optional_module_toggle_env: str
    keycloak_realms: list[KeycloakRealmContract]

    def keycloak_realm_by_id(self, realm_id: str) -> KeycloakRealmContract:
        for realm in self.keycloak_realms:
            if realm.realm_id == realm_id:
                return realm
        available = ", ".join(realm.realm_id for realm in self.keycloak_realms) or "none"
        raise ValueError(f"unknown keycloak realm_id={realm_id}; available={available}")


def _as_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a mapping")
    return value


def _as_list(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _as_str(value: object, path: str) -> str:
    if value is None:
        return ""
    if isinstance(value, (bool, int, float)):
        return str(value)
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")
    return value


def _required_str(mapping: dict[str, object], key: str, path: str) -> str:
    value = _as_str(mapping.get(key), f"{path}.{key}").strip()
    if not value:
        raise ValueError(f"{path}.{key} is required")
    return value


def _optional_str(mapping: dict[str, object], key: str, path: str) -> str:
    return _as_str(mapping.get(key), f"{path}.{key}").strip()


def _as_list_of_str(value: object, path: str) -> list[str]:
    return [_as_str(item, f"{path}[{idx}]").strip() for idx, item in enumerate(_as_list(value, path))]


def _parse_runtime_env_defaults(raw_items: list[object], path: str) -> list[RuntimeEnvDefault]:
    defaults: list[RuntimeEnvDefault] = []
    for idx, item in enumerate(raw_items):
        entry = _as_mapping(item, f"{path}[{idx}]")
        defaults.append(
            RuntimeEnvDefault(
                name=_required_str(entry, "name", f"{path}[{idx}]"),
                default=_required_str(entry, "default", f"{path}[{idx}]"),
            )
        )
    return defaults


def _parse_eso_contracts(raw_items: list[object], path: str) -> list[EsoSecretContract]:
    contracts: list[EsoSecretContract] = []
    for idx, item in enumerate(raw_items):
        item_path = f"{path}[{idx}]"
        entry = _as_mapping(item, item_path)
        mappings: list[EsoDataMapping] = []
        for mapping_index, raw_mapping in enumerate(_as_list(entry.get("data"), f"{item_path}.data")):
            mapping_path = f"{item_path}.data[{mapping_index}]"
            mapping = _as_mapping(raw_mapping, mapping_path)
            mappings.append(
                EsoDataMapping(
                    secret_key=_required_str(mapping, "secret_key", mapping_path),
                    source_property=_required_str(mapping, "source_property", mapping_path),
                )
            )
        if not mappings:
            raise ValueError(f"{item_path}.data must define at least one mapping")
        contracts.append(
            EsoSecretContract(
                contract_id=_required_str(entry, "id", item_path),
                module_id=_optional_str(entry, "module_id", item_path),
                namespace=_required_str(entry, "namespace", item_path),
                external_secret_name=_required_str(entry, "external_secret_name", item_path),
                target_secret_name=_required_str(entry, "target_secret_name", item_path),
                data_mappings=mappings,
            )
        )
    return contracts


def _parse_keycloak_realms(raw_items: list[object], path: str) -> list[KeycloakRealmContract]:
    realms: list[KeycloakRealmContract] = []
    for idx, item in enumerate(raw_items):
        item_path = f"{path}[{idx}]"
        entry = _as_mapping(item, item_path)
        realms.append(
            KeycloakRealmContract(
                realm_id=_required_str(entry, "id", item_path),
                module_id=_required_str(entry, "module_id", item_path),
                realm_env=_required_str(entry, "realm_env", item_path),
                default_realm_name=_required_str(entry, "default_realm_name", item_path),
                client_display_name=_required_str(entry, "client_display_name", item_path),
                client_id_env=_required_str(entry, "client_id_env", item_path),
                client_secret_env=_required_str(entry, "client_secret_env", item_path),
                role_names=_as_list_of_str(entry.get("role_names", []), f"{item_path}.role_names"),
                admin_username_env=_optional_str(entry, "admin_username_env", item_path),
                admin_password_env=_optional_str(entry, "admin_password_env", item_path),
                admin_role=_optional_str(entry, "admin_role", item_path),
            )
        )
    return realms


def load_runtime_identity_contract(path: Path) -> RuntimeIdentityContract:
    raw = load_yaml_subset(path)
    spec = _as_mapping(raw.get("spec"), "spec")

    runtime_defaults_raw = _as_list(spec.get("runtime_env_defaults", []), "spec.runtime_env_defaults")
    eso_raw = _as_mapping(spec.get("eso"), "spec.eso")
    keycloak_raw = _as_mapping(spec.get("keycloak"), "spec.keycloak")

    return RuntimeIdentityContract(
        runtime_env_defaults=_parse_runtime_env_defaults(runtime_defaults_raw, "spec.runtime_env_defaults"),
        eso_source_secret_key=_required_str(eso_raw, "source_secret_key", "spec.eso"),
        eso_store_kind=_required_str(eso_raw, "store_kind", "spec.eso"),
        eso_store_name=_required_str(eso_raw, "store_name", "spec.eso"),
        eso_contracts=_parse_eso_contracts(_as_list(eso_raw.get("contracts"), "spec.eso.contracts"), "spec.eso.contracts"),
        keycloak_namespace=_required_str(keycloak_raw, "namespace", "spec.keycloak"),
        keycloak_helm_release_env=_required_str(keycloak_raw, "helm_release_env", "spec.keycloak"),
        keycloak_admin_secret_name=_required_str(keycloak_raw, "admin_secret_name", "spec.keycloak"),
        keycloak_optional_module_toggle_env=_required_str(
            keycloak_raw,
            "optional_module_reconciliation_toggle_env",
            "spec.keycloak",
        ),
        keycloak_realms=_parse_keycloak_realms(
            _as_list(keycloak_raw.get("realms"), "spec.keycloak.realms"),
            "spec.keycloak.realms",
        ),
    )


def resolve_contract_path(repo_root: Path, contract_path: Path) -> Path:
    if contract_path.is_absolute():
        return contract_path
    return repo_root / contract_path


def _render_external_secret_doc(
    contract: RuntimeIdentityContract,
    secret_contract: EsoSecretContract,
) -> str:
    lines: list[str] = [
        "apiVersion: external-secrets.io/v1beta1",
        "kind: ExternalSecret",
        "metadata:",
        f"  name: {secret_contract.external_secret_name}",
        f"  namespace: {secret_contract.namespace}",
        "spec:",
        "  refreshInterval: 1m",
        "  secretStoreRef:",
        f"    kind: {contract.eso_store_kind}",
        f"    name: {contract.eso_store_name}",
        "  target:",
        f"    name: {secret_contract.target_secret_name}",
        "    creationPolicy: Owner",
        "    template:",
        "      engineVersion: v2",
        "      metadata:",
        "        labels:",
        "          app.kubernetes.io/part-of: platform-blueprint",
        f"          app.kubernetes.io/component: {secret_contract.contract_id}",
        "  data:",
    ]
    for mapping in secret_contract.data_mappings:
        lines.extend(
            [
                f"    - secretKey: {mapping.secret_key}",
                "      remoteRef:",
                f"        key: {contract.eso_source_secret_key}",
                f"        property: {mapping.source_property}",
            ]
        )
    return "\n".join(lines)


def render_eso_external_secrets_manifest(contract: RuntimeIdentityContract) -> str:
    docs = [_render_external_secret_doc(contract, item) for item in contract.eso_contracts]
    return "\n---\n".join(docs).rstrip() + "\n"


def iter_runtime_env_defaults(contract: RuntimeIdentityContract) -> Iterable[tuple[str, str]]:
    for item in contract.runtime_env_defaults:
        yield item.name, item.default


def iter_eso_contract_rows(contract: RuntimeIdentityContract) -> Iterable[tuple[str, str, str, str, str, str]]:
    for item in contract.eso_contracts:
        yield (
            item.contract_id,
            item.module_id,
            item.namespace,
            item.external_secret_name,
            item.target_secret_name,
            ",".join(item.target_secret_keys),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve relative paths.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Runtime identity contract path.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "runtime-env-defaults",
        help="Print runtime env defaults as tab-separated name/value rows.",
    )
    subparsers.add_parser(
        "eso-contracts",
        help="Print ESO secret contracts as tab-separated rows.",
    )

    keycloak_parser = subparsers.add_parser(
        "keycloak-realm",
        help="Print key/value contract fields for one Keycloak realm id.",
    )
    keycloak_parser.add_argument("--realm-id", required=True)

    render_parser = subparsers.add_parser(
        "render-eso-manifest",
        help="Render ExternalSecret manifests from the runtime identity contract.",
    )
    render_parser.add_argument("--output", type=Path, required=True)
    render_parser.add_argument("--check", action="store_true")

    return parser.parse_args()


def _emit_keycloak_realm(contract: RuntimeIdentityContract, realm_id: str) -> int:
    realm = contract.keycloak_realm_by_id(realm_id)
    items = {
        "realm_id": realm.realm_id,
        "module_id": realm.module_id,
        "realm_env": realm.realm_env,
        "default_realm_name": realm.default_realm_name,
        "resolved_realm_name": realm.resolved_realm_name(),
        "client_display_name": realm.client_display_name,
        "client_id_env": realm.client_id_env,
        "client_secret_env": realm.client_secret_env,
        "role_names_csv": ",".join(realm.role_names),
        "admin_username_env": realm.admin_username_env,
        "admin_password_env": realm.admin_password_env,
        "admin_role": realm.admin_role,
    }
    for key, value in items.items():
        print(f"{key}={value}")
    return 0


def _emit_runtime_env_defaults(contract: RuntimeIdentityContract) -> int:
    for name, value in iter_runtime_env_defaults(contract):
        print(f"{name}\t{value}")
    return 0


def _emit_eso_contracts(contract: RuntimeIdentityContract) -> int:
    for row in iter_eso_contract_rows(contract):
        print("\t".join(row))
    return 0


def _render_manifest(contract: RuntimeIdentityContract, output_path: Path, check: bool, repo_root: Path) -> int:
    rendered = render_eso_external_secrets_manifest(contract)
    if check:
        if not output_path.exists():
            print(f"missing generated manifest: {display_repo_path(repo_root, output_path)}", file=sys.stderr)
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            print(
                "runtime identity manifest out of date: "
                f"{display_repo_path(repo_root, output_path)}\n"
                "Run: python3 scripts/lib/infra/runtime_identity_contract.py render-eso-manifest --output "
                f"{display_repo_path(repo_root, output_path)}",
                file=sys.stderr,
            )
            return 1
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"rendered runtime identity manifest: {display_repo_path(repo_root, output_path)}")
    return 0


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    contract_path = resolve_contract_path(repo_root, args.contract)
    contract = load_runtime_identity_contract(contract_path)

    if args.command == "runtime-env-defaults":
        return _emit_runtime_env_defaults(contract)
    if args.command == "eso-contracts":
        return _emit_eso_contracts(contract)
    if args.command == "keycloak-realm":
        return _emit_keycloak_realm(contract, args.realm_id)
    if args.command == "render-eso-manifest":
        output_path = resolve_contract_path(repo_root, args.output)
        return _render_manifest(contract, output_path, bool(args.check), repo_root)
    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
