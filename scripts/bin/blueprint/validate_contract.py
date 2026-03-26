#!/usr/bin/env python3
"""Validate repository conformance against blueprint/contract.yaml."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import (  # noqa: E402
    BlueprintContract,
    load_blueprint_contract,
)


def _resolve_repo_root() -> Path:
    return REPO_ROOT


def _normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_semver(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value.strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _makefile_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    root_makefile = repo_root / "Makefile"
    if root_makefile.is_file():
        paths.append(root_makefile)

    make_dir = repo_root / "make"
    if make_dir.is_dir():
        paths.extend(sorted(path for path in make_dir.rglob("*.mk") if path.is_file()))

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def _make_targets(repo_root: Path) -> set[str]:
    makefiles = _makefile_paths(repo_root)
    if not makefiles:
        return set()
    targets: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    for makefile in makefiles:
        for line in makefile.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            target = match.group(1)
            if target == ".PHONY":
                continue
            targets.add(target)
    return targets


def _validate_required_files(repo_root: Path, required_files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in required_files:
        if not (repo_root / relative_path).is_file():
            errors.append(f"missing file: {relative_path}")
    return errors


def _validate_required_paths(repo_root: Path, required_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in required_paths:
        if not (repo_root / relative_path).exists():
            errors.append(f"missing path: {relative_path}")
    return errors


def _validate_template_bootstrap_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    template = contract.repository.template_bootstrap

    if template.model != "github-template":
        errors.append("repository.template_bootstrap.model must be github-template")

    template_version = template.template_version
    if not template_version:
        errors.append("repository.template_bootstrap.template_version is required")
    template_version_tuple = _parse_semver(template_version)
    if template_version and not template_version_tuple:
        errors.append("repository.template_bootstrap.template_version must be semver (MAJOR.MINOR.PATCH)")

    minimum_supported_upgrade_from = template.minimum_supported_upgrade_from
    if not minimum_supported_upgrade_from:
        errors.append("repository.template_bootstrap.minimum_supported_upgrade_from is required")
    minimum_supported_upgrade_from_tuple = _parse_semver(minimum_supported_upgrade_from)
    if minimum_supported_upgrade_from and not minimum_supported_upgrade_from_tuple:
        errors.append(
            "repository.template_bootstrap.minimum_supported_upgrade_from must be semver (MAJOR.MINOR.PATCH)"
        )
    if template_version_tuple and minimum_supported_upgrade_from_tuple:
        if minimum_supported_upgrade_from_tuple > template_version_tuple:
            errors.append(
                "repository.template_bootstrap.minimum_supported_upgrade_from cannot be greater than template_version"
            )

    init_command = template.init_command
    if not init_command:
        errors.append("repository.template_bootstrap.init_command is required")
    upgrade_command = template.upgrade_command
    if not upgrade_command:
        errors.append("repository.template_bootstrap.upgrade_command is required")

    targets = _make_targets(repo_root)
    for command_key, command_value in (
        ("init_command", init_command),
        ("upgrade_command", upgrade_command),
    ):
        if not command_value:
            continue
        if not command_value.startswith("make "):
            errors.append(f"repository.template_bootstrap.{command_key} must be a make target command")
            continue
        make_target = command_value.split(maxsplit=1)[1].strip()
        if not make_target:
            errors.append(f"repository.template_bootstrap.{command_key} must include a make target")
            continue
        if make_target not in targets:
            errors.append(
                f"repository.template_bootstrap.{command_key} references missing make target: {make_target}"
            )

    required_inputs = template.required_inputs
    if not required_inputs:
        errors.append("repository.template_bootstrap.required_inputs must define at least one variable")
    else:
        for variable in required_inputs:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable):
                errors.append(
                    f"repository.template_bootstrap.required_inputs contains invalid variable name: {variable}"
                )

    example_env_file = template.example_env_file
    if not example_env_file:
        errors.append("repository.template_bootstrap.example_env_file is required")
        return errors

    example_path = repo_root / example_env_file
    if not example_path.is_file():
        errors.append(f"missing template bootstrap example env file: {example_env_file}")
        return errors

    example_content = example_path.read_text(encoding="utf-8")
    for variable in required_inputs:
        if f"{variable}=" not in example_content:
            errors.append(
                "template bootstrap example env missing required input variable " f"declaration: {variable}"
            )
    return errors


def _resolve_branch_name() -> str:
    explicit = os.environ.get("BLUEPRINT_BRANCH_NAME", "").strip()
    if explicit:
        return explicit

    for env_name in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=_resolve_repo_root(),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""

    if result.returncode != 0:
        return ""

    branch_name = result.stdout.strip()
    if not branch_name or branch_name == "HEAD":
        return ""
    return branch_name


def _validate_branch_naming_contract(contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    default_branch = contract.repository.default_branch
    if not default_branch:
        errors.append("repository.default_branch is required")

    branch_naming = contract.repository.branch_naming
    if branch_naming.model != "github-flow":
        errors.append("repository.branch_naming.model must be github-flow")

    prefixes = branch_naming.purpose_prefixes
    if not prefixes:
        errors.append("repository.branch_naming.purpose_prefixes must define at least one prefix")
        return errors

    seen_prefixes: set[str] = set()
    for prefix in prefixes:
        if prefix in seen_prefixes:
            errors.append(f"duplicate branch purpose prefix: {prefix}")
            continue
        seen_prefixes.add(prefix)

        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*/", prefix):
            errors.append(
                f"invalid branch purpose prefix format: {prefix} (expected lowercase kebab-case with trailing '/')"
            )

    required_flow_prefixes = {"feature/", "fix/", "chore/", "docs/"}
    missing_required = sorted(required_flow_prefixes - seen_prefixes)
    if missing_required:
        errors.append("missing required github-flow purpose prefixes: " + ", ".join(missing_required))

    branch_name = _resolve_branch_name()
    if not branch_name or (default_branch and branch_name == default_branch):
        return errors

    matching_prefixes = [prefix for prefix in prefixes if branch_name.startswith(prefix)]
    if not matching_prefixes:
        errors.append(
            f"branch '{branch_name}' must start with one of configured purpose prefixes: {', '.join(prefixes)}"
        )
        return errors

    matched_prefix = matching_prefixes[0]
    if branch_name == matched_prefix:
        errors.append(
            f"branch '{branch_name}' must include a descriptive suffix after prefix '{matched_prefix}'"
        )
    return errors


def _validate_make_contract(repo_root: Path, required_targets: list[str], required_namespaces: list[str]) -> list[str]:
    errors: list[str] = []
    targets = _make_targets(repo_root)
    if not targets:
        return ["Makefile not found or no targets discovered"]

    for required in required_targets:
        if required not in targets:
            errors.append(f"missing make target: {required}")

    for namespace in required_namespaces:
        if not any(target.startswith(namespace) for target in targets):
            errors.append(f"missing make namespace: {namespace}")

    makefile_text = "\n".join(path.read_text(encoding="utf-8") for path in _makefile_paths(repo_root))
    if not re.search(r"^help:.*##", makefile_text, flags=re.MULTILINE):
        errors.append("Makefile help target must include a ## self-documenting description")

    return errors


def _validate_make_ownership_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    ownership = contract.make_contract.ownership

    root_loader_file = ownership.root_loader_file
    blueprint_generated_file = ownership.blueprint_generated_file
    platform_editable_file = ownership.platform_editable_file
    platform_editable_include_dir = ownership.platform_editable_include_dir
    platform_seed_mode = ownership.platform_seed_mode

    if not root_loader_file:
        errors.append("make_contract.ownership.root_loader_file is required")
    if not blueprint_generated_file:
        errors.append("make_contract.ownership.blueprint_generated_file is required")
    if not platform_editable_file:
        errors.append("make_contract.ownership.platform_editable_file is required")
    if not platform_editable_include_dir:
        errors.append("make_contract.ownership.platform_editable_include_dir is required")
    if platform_seed_mode != "create_if_missing":
        errors.append("make_contract.ownership.platform_seed_mode must be create_if_missing")

    root_loader_path = repo_root / root_loader_file if root_loader_file else None
    if root_loader_path and not root_loader_path.is_file():
        errors.append(f"missing make root loader file: {root_loader_file}")

    blueprint_generated_path = repo_root / blueprint_generated_file if blueprint_generated_file else None
    if blueprint_generated_path and not blueprint_generated_path.is_file():
        errors.append(f"missing blueprint generated make file: {blueprint_generated_file}")

    platform_editable_path = repo_root / platform_editable_file if platform_editable_file else None
    if platform_editable_path and not platform_editable_path.is_file():
        errors.append(f"missing platform editable make file: {platform_editable_file}")

    platform_editable_include_path = repo_root / platform_editable_include_dir if platform_editable_include_dir else None
    if platform_editable_include_path and not platform_editable_include_path.is_dir():
        errors.append(f"missing platform editable make include dir: {platform_editable_include_dir}")

    if root_loader_path and root_loader_path.is_file():
        loader_text = root_loader_path.read_text(encoding="utf-8")
        if "include $(BLUEPRINT_MAKEFILE)" not in loader_text:
            errors.append(
                "root Makefile loader must include blueprint generated make include: include $(BLUEPRINT_MAKEFILE)"
            )
        if "-include $(PLATFORM_MAKEFILE)" not in loader_text:
            errors.append(
                "root Makefile loader must include platform editable make include: -include $(PLATFORM_MAKEFILE)"
            )
        if "-include $(wildcard $(PLATFORM_MAKEFILES_DIR)/*.mk)" not in loader_text:
            errors.append(
                "root Makefile loader must include platform include-dir wildcard: "
                "-include $(wildcard $(PLATFORM_MAKEFILES_DIR)/*.mk)"
            )

    return errors


def _validate_optional_target_materialization_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    materialization = contract.make_contract.optional_target_materialization

    if materialization.mode != "conditional":
        errors.append("make_contract.optional_target_materialization.mode must be conditional")

    source_template = materialization.source_template
    if not source_template:
        errors.append("make_contract.optional_target_materialization.source_template is required")
    elif not (repo_root / source_template).is_file():
        errors.append("missing optional-target materialization template: " f"{source_template}")

    output_file = materialization.output_file
    if not output_file:
        errors.append("make_contract.optional_target_materialization.output_file is required")
    elif not (repo_root / output_file).is_file():
        errors.append("missing optional-target materialization output file: " f"{output_file}")

    materialization_command = materialization.materialization_command
    if not materialization_command:
        errors.append("make_contract.optional_target_materialization.materialization_command is required")
    elif not materialization_command.startswith("make "):
        errors.append("make_contract.optional_target_materialization.materialization_command must start with 'make '")
    else:
        target = materialization_command.split(maxsplit=1)[1].strip()
        if not target:
            errors.append(
                "make_contract.optional_target_materialization.materialization_command must include a make target"
            )
        elif target not in _make_targets(repo_root):
            errors.append(
                "make_contract.optional_target_materialization.materialization_command references missing make target: "
                f"{target}"
            )

    return errors


def _validate_shell_scripts(repo_root: Path, globs: list[str]) -> list[str]:
    errors: list[str] = []
    discovered: list[Path] = []
    for glob in globs:
        discovered.extend(sorted(repo_root.glob(glob)))
    discovered = sorted({path for path in discovered if path.is_file()})
    if not discovered:
        return ["no shell scripts discovered from configured shell globs"]

    shebang = "#!/usr/bin/env bash"
    for path in discovered:
        relative = path.relative_to(repo_root).as_posix()
        if relative.startswith("scripts/bin/") and path.stat().st_mode & 0o111 == 0:
            errors.append(f"script not executable: {path.relative_to(repo_root)}")
        first_line = path.read_text(encoding="utf-8").splitlines()
        if not first_line or first_line[0].strip() != shebang:
            errors.append(f"invalid/missing shebang: {path.relative_to(repo_root)}")
    return errors


def _validate_script_ownership_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    blueprint_roots = contract.script_contract.blueprint_managed_roots
    platform_roots = contract.script_contract.platform_editable_roots
    if not blueprint_roots:
        errors.append("script_contract.blueprint_managed_roots must define at least one root")
    if not platform_roots:
        errors.append("script_contract.platform_editable_roots must define at least one root")

    overlap = sorted(set(blueprint_roots) & set(platform_roots))
    if overlap:
        errors.append("script_contract roots overlap between blueprint/platform: " + ", ".join(overlap))

    for root in blueprint_roots + platform_roots:
        if not root.endswith("/"):
            errors.append(f"script_contract root must end with '/': {root}")
            continue
        path = repo_root / root
        if not path.is_dir():
            errors.append(f"missing script_contract root directory: {root}")

    for root in platform_roots:
        if not root.startswith("scripts/bin/platform/") and not root.startswith("scripts/lib/platform/"):
            errors.append(
                "script_contract.platform_editable_roots must be under scripts/bin/platform or scripts/lib/platform: "
                f"{root}"
            )

    return errors


def _validate_mermaid_docs(repo_root: Path, mermaid_files: list[str]) -> list[str]:
    errors: list[str] = []
    for relative_path in mermaid_files:
        path = repo_root / relative_path
        if not path.is_file():
            errors.append(f"missing mermaid markdown file: {relative_path}")
            continue
        if "```mermaid" not in path.read_text(encoding="utf-8"):
            errors.append(f"mermaid block missing in: {relative_path}")
    return errors


def _expand_optional_module_path(path_value: str) -> list[str]:
    if "${ENV}" not in path_value:
        return [path_value]
    return [path_value.replace("${ENV}", env) for env in ("local", "dev", "stage", "prod")]


def _is_optional_module_enabled(contract: BlueprintContract, module_name: str) -> bool:
    module = contract.optional_modules.modules.get(module_name)
    if not module:
        return False

    enable_flag = module.enable_flag
    enabled_by_default = module.enabled_by_default
    if not enable_flag:
        return enabled_by_default

    env_value = os.environ.get(enable_flag)
    if env_value is None:
        return enabled_by_default
    return _normalize_bool(env_value)


def _validate_optional_module_paths(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []

    for module_name, module in contract.optional_modules.modules.items():
        for key, value in module.paths.items():
            is_conditionally_required = (
                module.scaffolding_mode == "conditional" and key in set(module.paths_required_when_enabled)
            )
            module_enabled = _is_optional_module_enabled(contract, module_name)
            if is_conditionally_required and not module_enabled:
                continue

            for expanded in _expand_optional_module_path(value):
                path = repo_root / expanded
                if key == "helm_path" and expanded.endswith("/observability"):
                    if not path.is_dir():
                        errors.append(f"missing module path for module={module_name} key={key}: {expanded}")
                    continue
                if not path.exists():
                    errors.append(f"missing module path for module={module_name} key={key}: {expanded}")
    return errors


def _validate_optional_module_make_targets(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    targets = _make_targets(repo_root)

    for module_name, module in contract.optional_modules.modules.items():
        make_targets = module.make_targets
        if not make_targets:
            errors.append(f"missing optional module make_targets list: {module_name}")
            continue

        if module.make_targets_mode != "conditional":
            errors.append(f"optional module make_targets_mode must be conditional for module={module_name}")

        module_enabled = _is_optional_module_enabled(contract, module_name)
        for make_target in make_targets:
            target_exists = make_target in targets
            if module_enabled and not target_exists:
                errors.append(f"missing optional-module make target for enabled module={module_name}: {make_target}")
            if not module_enabled and target_exists:
                errors.append(
                    "optional-module make target must not be materialized when module disabled "
                    f"module={module_name}: {make_target}"
                )

    return errors


def _module_wrapper_template_name(make_target: str) -> str:
    target = make_target.removeprefix("infra-")
    return target.replace("-", "_")


def _validate_module_wrapper_skeleton_templates(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    templates_root = repo_root / "scripts/templates/infra/module_wrappers"
    if not templates_root.is_dir():
        return ["missing optional-module wrapper template root: scripts/templates/infra/module_wrappers"]

    for module_name, module in contract.optional_modules.modules.items():
        module_dir = templates_root / module_name
        if not module_dir.is_dir():
            errors.append(
                "missing optional-module wrapper template directory for module="
                f"{module_name}: {module_dir.relative_to(repo_root).as_posix()}"
            )
            continue
        for make_target in module.make_targets:
            template_name = _module_wrapper_template_name(make_target)
            template_path = module_dir / f"{template_name}.sh.tmpl"
            if not template_path.is_file():
                errors.append(
                    "missing optional-module wrapper skeleton template for module="
                    f"{module_name} target={make_target}: {template_path.relative_to(repo_root).as_posix()}"
                )
    return errors


def _validate_airflow_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    if not _is_optional_module_enabled(contract, "workflows"):
        return errors

    layout = contract.architecture.airflow_dag_layout

    if layout.shared_bootstrap_file:
        path = repo_root / layout.shared_bootstrap_file
        if not path.is_file():
            errors.append(f"missing airflow shared bootstrap file: {layout.shared_bootstrap_file}")

    forbid_pattern = layout.forbid_dag_entrypoints_under
    if forbid_pattern == "apps/**":
        apps_root = repo_root / "apps"
        if apps_root.is_dir():
            dag_files = sorted(apps_root.rglob("*dag*.py"))
            if dag_files:
                first = dag_files[0].relative_to(repo_root)
                errors.append(f"dag entrypoint forbidden under apps/** (found: {first})")

    airflow_ignore = repo_root / "dags/.airflowignore"
    if layout.airflowignore_must_restrict_parser_scope and not airflow_ignore.is_file():
        errors.append("missing airflow parser scope file: dags/.airflowignore")
    elif airflow_ignore.is_file() and forbid_pattern and forbid_pattern not in airflow_ignore.read_text(encoding="utf-8"):
        errors.append(f"dags/.airflowignore must include parser-scope rule: {forbid_pattern}")

    return errors


def _validate_docs_edit_link(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    if not contract.docs_contract.edit_link_enabled:
        return errors

    docusaurus_config = repo_root / "docs/docusaurus.config.js"
    if not docusaurus_config.is_file():
        return ["missing docs config file: docs/docusaurus.config.js"]

    content = docusaurus_config.read_text(encoding="utf-8")
    if "editUrl" not in content:
        errors.append("docs edit_link_enabled=true requires editUrl in docs/docusaurus.config.js")
    return errors


def _validate_platform_docs_seed_contract(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    platform_docs = contract.docs_contract.platform_docs

    platform_root = platform_docs.root
    if not platform_root:
        errors.append("docs_contract.platform_docs.root is required")
    elif not (repo_root / platform_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.root directory: {platform_root}")

    if platform_docs.seed_mode != "create_if_missing":
        errors.append("docs_contract.platform_docs.seed_mode must be create_if_missing")

    if platform_docs.bootstrap_command != "make blueprint-bootstrap":
        errors.append("docs_contract.platform_docs.bootstrap_command must be make blueprint-bootstrap")
    elif "blueprint-bootstrap" not in _make_targets(repo_root):
        errors.append("docs_contract.platform_docs.bootstrap_command references missing make target: blueprint-bootstrap")

    template_root = platform_docs.template_root
    if not template_root:
        errors.append("docs_contract.platform_docs.template_root is required")
    elif not (repo_root / template_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.template_root directory: {template_root}")

    required_seed_files = platform_docs.required_seed_files
    if not required_seed_files:
        errors.append("docs_contract.platform_docs.required_seed_files must define at least one file")
        return errors

    for relative_path in required_seed_files:
        target_path = repo_root / relative_path
        if not target_path.is_file():
            errors.append(f"missing platform docs seed file: {relative_path}")
            continue
        if not target_path.read_text(encoding="utf-8").strip():
            errors.append(f"platform docs seed file is empty: {relative_path}")

        if platform_root and not relative_path.startswith(f"{platform_root}/"):
            errors.append(
                "platform docs seed file must be under configured root " f"{platform_root}: {relative_path}"
            )
            continue

        if not template_root or not platform_root:
            continue
        suffix = relative_path.removeprefix(f"{platform_root}/")
        template_path = repo_root / template_root / suffix
        if not template_path.is_file():
            errors.append(
                "missing platform docs seed template file for "
                f"{relative_path}: {(Path(template_root) / suffix).as_posix()}"
            )
            continue
        template_lines = template_path.read_text(encoding="utf-8").splitlines()
        first_nonempty = next((line.strip() for line in template_lines if line.strip()), "")
        if not first_nonempty.startswith("# "):
            errors.append(
                "platform docs seed template must start with a markdown heading: "
                f"{(Path(template_root) / suffix).as_posix()}"
            )

    return errors


def _validate_bootstrap_template_sync(repo_root: Path) -> list[str]:
    errors: list[str] = []

    # These files are materialized by blueprint-bootstrap/infra-bootstrap from
    # static templates and must stay byte-for-byte synchronized to keep generated
    # repositories stable.
    template_sync_contract = (
        (
            repo_root / "scripts/templates/blueprint/bootstrap",
            (
                "Makefile",
                ".editorconfig",
                ".gitignore",
                ".dockerignore",
                ".pre-commit-config.yaml",
                "blueprint/repo.init.example.env",
                "docs/README.md",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/template_release_policy.md",
                "docs/blueprint/governance/ownership_matrix.md",
            ),
        ),
        (
            repo_root / "scripts/templates/infra/bootstrap",
            (
                "tests/infra/modules/observability/README.md",
                "infra/local/crossplane/kustomization.yaml",
                "infra/local/crossplane/namespace.yaml",
                "infra/local/helm/observability/grafana.values.yaml",
                "infra/local/helm/observability/otel-collector.values.yaml",
                "infra/gitops/argocd/base/kustomization.yaml",
                "infra/gitops/argocd/base/namespace.yaml",
            ),
        ),
    )

    for template_root, synced_files in template_sync_contract:
        for rel_path in synced_files:
            target_path = repo_root / rel_path
            template_path = template_root / rel_path
            template_rel = template_path.relative_to(repo_root).as_posix()
            if not target_path.is_file():
                errors.append(f"missing bootstrap target file for template sync: {rel_path}")
                continue
            if not template_path.is_file():
                errors.append(f"missing bootstrap template file: {template_rel}")
                continue
            if target_path.read_text(encoding="utf-8") != template_path.read_text(encoding="utf-8"):
                errors.append("bootstrap template drift detected for " f"{rel_path}; sync with {template_rel}")
    return errors


def parse_args() -> argparse.Namespace:
    repo_root = _resolve_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract-path",
        default=str(repo_root / "blueprint/contract.yaml"),
        help="Path to blueprint contract YAML.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = _resolve_repo_root()
    contract_path = Path(args.contract_path).resolve()

    try:
        contract = load_blueprint_contract(contract_path)
        required_files = contract.repository.required_files
        required_paths = contract.structure.required_paths
        required_diagrams = contract.docs_contract.required_diagrams
        required_targets = contract.make_contract.required_targets
        required_namespaces = contract.make_contract.required_namespaces
        if not required_files:
            raise ValueError("required_files list is empty")
        if not required_paths:
            raise ValueError("required_paths list is empty")
        if not required_targets:
            raise ValueError("required_targets list is empty")
        if not required_namespaces:
            raise ValueError("required_namespaces list is empty")
    except ValueError as exc:
        print(f"[infra-validate] contract error: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(_validate_required_files(repo_root, required_files))
    errors.extend(_validate_required_paths(repo_root, required_paths))
    errors.extend(_validate_template_bootstrap_contract(repo_root, contract))
    errors.extend(_validate_branch_naming_contract(contract))
    errors.extend(_validate_make_contract(repo_root, required_targets, required_namespaces))
    errors.extend(_validate_make_ownership_contract(repo_root, contract))
    errors.extend(_validate_optional_target_materialization_contract(repo_root, contract))
    errors.extend(_validate_script_ownership_contract(repo_root, contract))
    errors.extend(_validate_shell_scripts(repo_root, ["scripts/bin/**/*.sh", "scripts/lib/**/*.sh"]))
    errors.extend(_validate_mermaid_docs(repo_root, required_diagrams))
    errors.extend(_validate_optional_module_paths(repo_root, contract))
    errors.extend(_validate_optional_module_make_targets(repo_root, contract))
    errors.extend(_validate_module_wrapper_skeleton_templates(repo_root, contract))
    errors.extend(_validate_airflow_contract(repo_root, contract))
    errors.extend(_validate_docs_edit_link(repo_root, contract))
    errors.extend(_validate_platform_docs_seed_contract(repo_root, contract))
    errors.extend(_validate_bootstrap_template_sync(repo_root))

    if errors:
        for error in errors:
            print(f"[infra-validate] error: {error}", file=sys.stderr)
        print(f"[infra-validate] failed with {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print("[infra-validate] contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
