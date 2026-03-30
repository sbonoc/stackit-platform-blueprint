#!/usr/bin/env python3
"""CLI helpers for shell runtime access to blueprint contract fields."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def _normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _prepare_contract(contract_path: Path):
    resolved_contract_path = contract_path.resolve()
    repo_root = resolved_contract_path.parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: PLC0415

    return repo_root, load_blueprint_contract(resolved_contract_path)


def command_runtime_lines(contract_path: Path) -> int:
    _, contract = _prepare_contract(contract_path)
    repository = contract.repository

    print(f"repo_mode={repository.repo_mode}")
    print(f"mode_from={repository.consumer_init.mode_from}")
    print(f"mode_to={repository.consumer_init.mode_to}")
    print(f"defaults_env_file={repository.template_bootstrap.defaults_env_file}")
    print(f"secrets_example_env_file={repository.template_bootstrap.secrets_example_env_file}")
    print(f"secrets_env_file={repository.template_bootstrap.secrets_env_file}")
    print(f"force_env_var={repository.template_bootstrap.force_env_var}")
    for variable in repository.template_bootstrap.required_inputs:
        print(f"required_input={variable}")
    for path in repository.consumer_seeded_paths:
        print(f"consumer_seeded={path}")
    for path in repository.init_managed_paths:
        print(f"init_managed={path}")
    return 0


def command_required_env_vars(contract_path: Path) -> int:
    repo_root, contract = _prepare_contract(contract_path)
    required: list[str] = []
    seen: set[str] = set()

    for variable in contract.repository.template_bootstrap.required_inputs:
        if variable in seen:
            continue
        seen.add(variable)
        required.append(variable)

    from scripts.lib.blueprint.contract_schema import load_module_contract  # noqa: PLC0415

    for module in contract.optional_modules.modules.values():
        flag_raw = os.environ.get(module.enable_flag)
        enabled = module.enabled_by_default if flag_raw is None else _normalize_bool(flag_raw)
        if not enabled:
            continue
        module_contract = load_module_contract(repo_root / module.paths["contract_path"], repo_root)
        for variable in module_contract.required_env:
            if variable in seen:
                continue
            seen.add(variable)
            required.append(variable)

    for variable in required:
        print(variable)
    return 0


def command_module_defaults(contract_path: Path) -> int:
    _, contract = _prepare_contract(contract_path)
    for module_id, module in contract.optional_modules.modules.items():
        print(f"{module_id}={str(module.enabled_by_default).lower()}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_contract_path_arg(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument(
            "--contract-path",
            required=True,
            type=Path,
            help="Path to blueprint/contract.yaml",
        )

    runtime_lines = subparsers.add_parser("runtime-lines", help="Emit key-value runtime lines for shell sourcing.")
    _add_contract_path_arg(runtime_lines)

    required_env = subparsers.add_parser(
        "required-env-vars",
        help="Emit required runtime environment variables based on enabled module flags.",
    )
    _add_contract_path_arg(required_env)

    module_defaults = subparsers.add_parser(
        "module-defaults",
        help="Emit optional-module enabled_by_default values as module_id=true|false lines.",
    )
    _add_contract_path_arg(module_defaults)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "runtime-lines":
        return command_runtime_lines(args.contract_path)
    if args.command == "required-env-vars":
        return command_required_env_vars(args.contract_path)
    if args.command == "module-defaults":
        return command_module_defaults(args.contract_path)

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
