#!/usr/bin/env python3
"""Generate optional-module wrapper skeleton templates from module contracts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_module_contract  # noqa: E402


def _script_basename_from_make_target(make_target: str) -> str:
    target = make_target
    if target.startswith("infra-"):
        target = target.removeprefix("infra-")
    return target.replace("-", "_")


def _render_template(module_id: str, enable_flag: str, action_key: str, make_target: str) -> str:
    script_basename = _script_basename_from_make_target(make_target)
    action_label = action_key.replace("_", " ").replace("-", " ").strip()
    if not action_label:
        action_label = script_basename.replace("_", " ")

    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "ROOT_DIR=\"$(cd \"$SCRIPT_DIR/../../..\" && pwd)\"\n"
        "source \"$ROOT_DIR/scripts/lib/bootstrap.sh\"\n"
        "source \"$ROOT_DIR/scripts/lib/infra/state.sh\"\n"
        "\n"
        f"start_script_metric_trap \"infra_{script_basename}\"\n"
        "\n"
        "# Generated wrapper skeleton from blueprint/modules/*/module.contract.yaml.\n"
        "# Copy into scripts/bin/infra/ and replace placeholders with module-specific implementation.\n"
        "\n"
        f"if ! is_module_enabled {module_id}; then\n"
        f"  log_info \"{enable_flag}=false; skipping {module_id} {action_label}\"\n"
        "  exit 0\n"
        "fi\n"
        "\n"
        "set_state_namespace infra\n"
        "\n"
        "readonly MODULE_WRAPPER_STUB_EXIT_CODE=64\n"
        "\n"
        "# Explicit stub: template consumers must replace this block with module-specific logic.\n"
        "log_metric \"optional_module_wrapper_stub_invocation\" \"1\" "
        f"\"module={module_id} action={action_key} target={make_target}\"\n"
        "state_file=\"$(\n"
        f"  write_state_file \"{module_id}_{action_key}\" \\\n"
        "    \"status=not_implemented\" \\\n"
        f"    \"module={module_id}\" \\\n"
        f"    \"action={action_key}\" \\\n"
        f"    \"target={make_target}\" \\\n"
        "    \"timestamp_utc=$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")\"\n"
        ")\"\n"
        f"log_error \"module wrapper not implemented: module={module_id} action={action_key} target={make_target}\"\n"
        f"log_error \"copy this skeleton into scripts/bin/infra/{script_basename}.sh and replace the stub implementation\"\n"
        f"log_info \"{module_id} {action_label} stub state written to $state_file\"\n"
        "exit \"$MODULE_WRAPPER_STUB_EXIT_CODE\"\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--modules-dir",
        default="blueprint/modules",
        help="Directory containing module.contract.yaml files.",
    )
    parser.add_argument(
        "--output-root",
        default="scripts/templates/infra/module_wrappers",
        help="Output directory for generated skeleton templates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    modules_dir = repo_root / args.modules_dir
    output_root = repo_root / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    module_contracts = sorted(modules_dir.glob("*/module.contract.yaml"))
    if not module_contracts:
        raise ValueError(f"no module contracts found under {modules_dir}")

    generated = 0
    for module_contract_path in module_contracts:
        module_contract = load_module_contract(module_contract_path, repo_root)
        module_out_dir = output_root / module_contract.module_id
        module_out_dir.mkdir(parents=True, exist_ok=True)

        for action_key, make_target in sorted(module_contract.make_targets.items()):
            script_basename = _script_basename_from_make_target(make_target)
            output_file = module_out_dir / f"{script_basename}.sh.tmpl"
            output_file.write_text(
                _render_template(
                    module_id=module_contract.module_id,
                    enable_flag=module_contract.enable_flag,
                    action_key=action_key,
                    make_target=make_target,
                ),
                encoding="utf-8",
            )
            generated += 1

    print(
        f"[blueprint-render-module-wrapper-skeletons] generated {generated} template file(s) under "
        f"{output_root.relative_to(repo_root).as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
