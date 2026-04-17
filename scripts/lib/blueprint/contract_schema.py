#!/usr/bin/env python3
"""Schema-driven loaders for blueprint and module contract YAML files.

This module intentionally avoids external YAML dependencies so bootstrap
validation can run with only the Python stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class BranchNamingContract:
    model: str
    purpose_prefixes: list[str]


@dataclass(frozen=True)
class TemplateBootstrapContract:
    model: str
    template_version: str
    init_command: str
    defaults_env_file: str
    secrets_example_env_file: str
    secrets_env_file: str
    force_env_var: str
    required_inputs: list[str]


@dataclass(frozen=True)
class ConsumerInitContract:
    template_root: str
    mode_from: str
    mode_to: str
    prune_disabled_optional_scaffolding: bool
    source_artifact_prune_globs_on_init: list[str]


@dataclass(frozen=True)
class RepositoryOwnershipPathClasses:
    source_only: list[str]
    consumer_seeded: list[str]
    init_managed: list[str]
    conditional_scaffold: list[str]


@dataclass(frozen=True)
class RepositoryContract:
    repo_mode: str
    allowed_repo_modes: list[str]
    default_branch: str
    branch_naming: BranchNamingContract
    template_bootstrap: TemplateBootstrapContract
    required_files: list[str]
    ownership_path_classes: RepositoryOwnershipPathClasses
    consumer_init: ConsumerInitContract

    @property
    def source_only_paths(self) -> list[str]:
        return self.ownership_path_classes.source_only

    @property
    def consumer_seeded_paths(self) -> list[str]:
        return self.ownership_path_classes.consumer_seeded

    @property
    def init_managed_paths(self) -> list[str]:
        return self.ownership_path_classes.init_managed

    @property
    def conditional_scaffold_paths(self) -> list[str]:
        return self.ownership_path_classes.conditional_scaffold


@dataclass(frozen=True)
class StructureContract:
    required_paths: list[str]


@dataclass(frozen=True)
class ScriptContract:
    blueprint_managed_roots: list[str]
    platform_editable_roots: list[str]


@dataclass(frozen=True)
class MakeOwnershipContract:
    root_loader_file: str
    blueprint_generated_file: str
    platform_editable_file: str
    platform_editable_include_dir: str
    platform_seed_mode: str


@dataclass(frozen=True)
class OptionalTargetMaterializationContract:
    mode: str
    source_template: str
    output_file: str
    materialization_command: str


@dataclass(frozen=True)
class MakeContract:
    required_namespaces: list[str]
    required_targets: list[str]
    ownership: MakeOwnershipContract
    optional_target_materialization: OptionalTargetMaterializationContract


@dataclass(frozen=True)
class PlatformDocsContract:
    root: str
    seed_mode: str
    bootstrap_command: str
    template_root: str
    required_seed_files: list[str]


@dataclass(frozen=True)
class BlueprintDocsContract:
    root: str
    sync_policy: str
    template_sync_allowlist: list[str]


@dataclass(frozen=True)
class DocsContract:
    required_diagrams: list[str]
    edit_link_enabled: bool
    blueprint_docs: BlueprintDocsContract
    platform_docs: PlatformDocsContract


@dataclass(frozen=True)
class AirflowLayoutContract:
    dag_entrypoints_root: str
    shared_bootstrap_file: str
    forbid_dag_entrypoints_under: str
    airflowignore_must_restrict_parser_scope: bool


@dataclass(frozen=True)
class ArchitectureContract:
    airflow_dag_layout: AirflowLayoutContract


@dataclass(frozen=True)
class OptionalModuleContract:
    module_id: str
    enabled_by_default: bool
    enable_flag: str
    scaffolding_mode: str
    paths_required_when_enabled: list[str]
    make_targets_mode: str
    make_targets: list[str]
    paths: dict[str, str]


@dataclass(frozen=True)
class OptionalModulesContract:
    modules: dict[str, OptionalModuleContract]


@dataclass(frozen=True)
class BlueprintContract:
    repository: RepositoryContract
    structure: StructureContract
    script_contract: ScriptContract
    docs_contract: DocsContract
    make_contract: MakeContract
    architecture: ArchitectureContract
    optional_modules: OptionalModulesContract
    raw: dict[str, Any]


@dataclass(frozen=True)
class ModuleContract:
    module_id: str
    purpose: str
    enabled_by_default: bool
    enable_flag: str
    make_targets: dict[str, str]
    required_env: list[str]
    outputs: list[str]
    contract_path: str


@dataclass(frozen=True)
class _YamlToken:
    indent: int
    content: str
    line_no: int


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = [item.strip() for item in inner.split(",")]
        return [_strip_quotes(item) for item in items]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return _strip_quotes(value)


def _looks_like_mapping_entry(value: str) -> bool:
    if not value:
        return False
    if value[0] in {"'", '"'}:
        return False
    return bool(re.match(r"^[A-Za-z0-9_.$/{}/-]+\s*:", value))


def _tokenize_yaml(text: str) -> list[_YamlToken]:
    tokens: list[_YamlToken] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        tokens.append(_YamlToken(indent=indent, content=stripped, line_no=idx))
    return tokens


def _parse_mapping(tokens: list[_YamlToken], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    i = index
    while i < len(tokens):
        token = tokens[i]
        if token.indent < indent:
            break
        if token.indent > indent:
            raise ValueError(f"unexpected indentation at line {token.line_no}")
        if token.content.startswith("- "):
            break
        key, sep, remainder = token.content.partition(":")
        if not sep:
            raise ValueError(f"invalid mapping entry at line {token.line_no}: {token.content}")
        map_key = key.strip()
        raw_remainder = remainder.strip()
        i += 1
        if raw_remainder:
            result[map_key] = _parse_scalar(raw_remainder)
            continue
        if i < len(tokens) and tokens[i].indent > token.indent:
            child_indent = tokens[i].indent
            child_value, i = _parse_node(tokens, i, child_indent)
            result[map_key] = child_value
        else:
            result[map_key] = None
    return result, i


def _parse_list(tokens: list[_YamlToken], index: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    i = index
    while i < len(tokens):
        token = tokens[i]
        if token.indent < indent:
            break
        if token.indent != indent or not token.content.startswith("- "):
            break
        body = token.content[2:].strip()
        i += 1
        if not body:
            if i < len(tokens) and tokens[i].indent > token.indent:
                nested_indent = tokens[i].indent
                nested_value, i = _parse_node(tokens, i, nested_indent)
                items.append(nested_value)
            else:
                items.append(None)
            continue

        if _looks_like_mapping_entry(body):
            key, _, rem = body.partition(":")
            item_map: dict[str, Any] = {}
            key = key.strip()
            rem = rem.strip()
            if rem:
                item_map[key] = _parse_scalar(rem)
            else:
                if i < len(tokens) and tokens[i].indent > token.indent:
                    nested_indent = tokens[i].indent
                    nested_value, i = _parse_node(tokens, i, nested_indent)
                    item_map[key] = nested_value
                else:
                    item_map[key] = None

            if i < len(tokens) and tokens[i].indent > token.indent:
                nested_indent = tokens[i].indent
                continuation, i = _parse_node(tokens, i, nested_indent)
                if isinstance(continuation, dict):
                    item_map.update(continuation)
                else:
                    raise ValueError(
                        f"list mapping continuation must be a mapping at line {tokens[i-1].line_no}"
                    )
            items.append(item_map)
            continue

        items.append(_parse_scalar(body))
    return items, i


def _parse_node(tokens: list[_YamlToken], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(tokens):
        raise ValueError("unexpected end of YAML input")
    token = tokens[index]
    if token.indent != indent:
        raise ValueError(f"unexpected indentation at line {token.line_no}")
    if token.content.startswith("- "):
        return _parse_list(tokens, index, indent)
    return _parse_mapping(tokens, index, indent)


def parse_yaml_subset(text: str) -> dict[str, Any]:
    tokens = _tokenize_yaml(text)
    if not tokens:
        return {}
    parsed, next_index = _parse_node(tokens, 0, tokens[0].indent)
    if next_index != len(tokens):
        line_no = tokens[next_index].line_no
        raise ValueError(f"failed to parse YAML completely; stopped before line {line_no}")
    if not isinstance(parsed, dict):
        raise ValueError("root YAML document must be a mapping")
    return parsed


def load_yaml_subset(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"contract not found: {path}")
    return parse_yaml_subset(path.read_text(encoding="utf-8"))


def _as_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a mapping")
    return value


def _as_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be a list")
    return value


def _as_str(value: Any, path: str) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return str(value)
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")
    return value


def _as_bool(value: Any, path: str, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    raise ValueError(f"{path} must be a boolean")


def _as_list_of_str(value: Any, path: str) -> list[str]:
    return [_as_str(item, f"{path}[{idx}]") for idx, item in enumerate(_as_list(value, path))]


def _optional_str_map(mapping: dict[str, Any], keys: list[str], prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in keys:
        raw_value = mapping.get(key)
        if raw_value is None:
            continue
        values[key] = _as_str(raw_value, f"{prefix}.{key}")
    return values


def load_blueprint_contract(path: Path) -> BlueprintContract:
    raw = load_yaml_subset(path)
    spec = _as_mapping(raw.get("spec"), "spec")

    repository_raw = _as_mapping(spec.get("repository"), "spec.repository")
    branch_raw = _as_mapping(repository_raw.get("branch_naming"), "spec.repository.branch_naming")
    template_raw = _as_mapping(repository_raw.get("template_bootstrap"), "spec.repository.template_bootstrap")
    consumer_init_raw = _as_mapping(repository_raw.get("consumer_init"), "spec.repository.consumer_init")
    ownership_classes_raw = _as_mapping(
        repository_raw.get("ownership_path_classes"),
        "spec.repository.ownership_path_classes",
    )

    repository = RepositoryContract(
        repo_mode=_as_str(repository_raw.get("repo_mode"), "spec.repository.repo_mode"),
        allowed_repo_modes=_as_list_of_str(
            repository_raw.get("allowed_repo_modes", []),
            "spec.repository.allowed_repo_modes",
        ),
        default_branch=_as_str(repository_raw.get("default_branch"), "spec.repository.default_branch"),
        branch_naming=BranchNamingContract(
            model=_as_str(branch_raw.get("model"), "spec.repository.branch_naming.model"),
            purpose_prefixes=_as_list_of_str(
                branch_raw.get("purpose_prefixes", []),
                "spec.repository.branch_naming.purpose_prefixes",
            ),
        ),
        template_bootstrap=TemplateBootstrapContract(
            model=_as_str(template_raw.get("model"), "spec.repository.template_bootstrap.model"),
            template_version=_as_str(
                template_raw.get("template_version"),
                "spec.repository.template_bootstrap.template_version",
            ),
            init_command=_as_str(template_raw.get("init_command"), "spec.repository.template_bootstrap.init_command"),
            defaults_env_file=_as_str(
                template_raw.get("defaults_env_file"),
                "spec.repository.template_bootstrap.defaults_env_file",
            ),
            secrets_example_env_file=_as_str(
                template_raw.get("secrets_example_env_file"),
                "spec.repository.template_bootstrap.secrets_example_env_file",
            ),
            secrets_env_file=_as_str(
                template_raw.get("secrets_env_file"),
                "spec.repository.template_bootstrap.secrets_env_file",
            ),
            force_env_var=_as_str(
                template_raw.get("force_env_var"),
                "spec.repository.template_bootstrap.force_env_var",
            ),
            required_inputs=_as_list_of_str(
                template_raw.get("required_inputs", []),
                "spec.repository.template_bootstrap.required_inputs",
            ),
        ),
        required_files=_as_list_of_str(repository_raw.get("required_files", []), "spec.repository.required_files"),
        ownership_path_classes=RepositoryOwnershipPathClasses(
            source_only=_as_list_of_str(
                ownership_classes_raw.get("source_only", []),
                "spec.repository.ownership_path_classes.source_only",
            ),
            consumer_seeded=_as_list_of_str(
                ownership_classes_raw.get("consumer_seeded", []),
                "spec.repository.ownership_path_classes.consumer_seeded",
            ),
            init_managed=_as_list_of_str(
                ownership_classes_raw.get("init_managed", []),
                "spec.repository.ownership_path_classes.init_managed",
            ),
            conditional_scaffold=_as_list_of_str(
                ownership_classes_raw.get("conditional_scaffold", []),
                "spec.repository.ownership_path_classes.conditional_scaffold",
            ),
        ),
        consumer_init=ConsumerInitContract(
            template_root=_as_str(
                consumer_init_raw.get("template_root"),
                "spec.repository.consumer_init.template_root",
            ),
            mode_from=_as_str(
                consumer_init_raw.get("mode_from"),
                "spec.repository.consumer_init.mode_from",
            ),
            mode_to=_as_str(
                consumer_init_raw.get("mode_to"),
                "spec.repository.consumer_init.mode_to",
            ),
            prune_disabled_optional_scaffolding=_as_bool(
                consumer_init_raw.get("prune_disabled_optional_scaffolding"),
                "spec.repository.consumer_init.prune_disabled_optional_scaffolding",
                default=False,
            ),
            source_artifact_prune_globs_on_init=_as_list_of_str(
                consumer_init_raw.get("source_artifact_prune_globs_on_init", []),
                "spec.repository.consumer_init.source_artifact_prune_globs_on_init",
            ),
        ),
    )

    structure_raw = _as_mapping(spec.get("structure"), "spec.structure")
    structure = StructureContract(
        required_paths=_as_list_of_str(structure_raw.get("required_paths", []), "spec.structure.required_paths")
    )

    script_raw = _as_mapping(spec.get("script_contract"), "spec.script_contract")
    script_contract = ScriptContract(
        blueprint_managed_roots=_as_list_of_str(
            script_raw.get("blueprint_managed_roots", []),
            "spec.script_contract.blueprint_managed_roots",
        ),
        platform_editable_roots=_as_list_of_str(
            script_raw.get("platform_editable_roots", []),
            "spec.script_contract.platform_editable_roots",
        ),
    )

    docs_raw = _as_mapping(spec.get("docs_contract"), "spec.docs_contract")
    blueprint_docs_raw = _as_mapping(docs_raw.get("blueprint_docs"), "spec.docs_contract.blueprint_docs")
    platform_docs_raw = _as_mapping(docs_raw.get("platform_docs"), "spec.docs_contract.platform_docs")
    docs_contract = DocsContract(
        required_diagrams=_as_list_of_str(
            docs_raw.get("required_diagrams", []),
            "spec.docs_contract.required_diagrams",
        ),
        edit_link_enabled=_as_bool(
            docs_raw.get("edit_link_enabled"),
            "spec.docs_contract.edit_link_enabled",
            default=False,
        ),
        blueprint_docs=BlueprintDocsContract(
            root=_as_str(blueprint_docs_raw.get("root"), "spec.docs_contract.blueprint_docs.root"),
            sync_policy=_as_str(
                blueprint_docs_raw.get("sync_policy"),
                "spec.docs_contract.blueprint_docs.sync_policy",
            ),
            template_sync_allowlist=_as_list_of_str(
                blueprint_docs_raw.get("template_sync_allowlist", []),
                "spec.docs_contract.blueprint_docs.template_sync_allowlist",
            ),
        ),
        platform_docs=PlatformDocsContract(
            root=_as_str(platform_docs_raw.get("root"), "spec.docs_contract.platform_docs.root"),
            seed_mode=_as_str(platform_docs_raw.get("seed_mode"), "spec.docs_contract.platform_docs.seed_mode"),
            bootstrap_command=_as_str(
                platform_docs_raw.get("bootstrap_command"),
                "spec.docs_contract.platform_docs.bootstrap_command",
            ),
            template_root=_as_str(
                platform_docs_raw.get("template_root"),
                "spec.docs_contract.platform_docs.template_root",
            ),
            required_seed_files=_as_list_of_str(
                platform_docs_raw.get("required_seed_files", []),
                "spec.docs_contract.platform_docs.required_seed_files",
            ),
        ),
    )

    make_raw = _as_mapping(spec.get("make_contract"), "spec.make_contract")
    ownership_raw = _as_mapping(make_raw.get("ownership"), "spec.make_contract.ownership")
    materialization_raw = _as_mapping(
        make_raw.get("optional_target_materialization"),
        "spec.make_contract.optional_target_materialization",
    )
    make_contract = MakeContract(
        required_namespaces=_as_list_of_str(
            make_raw.get("required_namespaces", []),
            "spec.make_contract.required_namespaces",
        ),
        required_targets=_as_list_of_str(
            make_raw.get("required_targets", []),
            "spec.make_contract.required_targets",
        ),
        ownership=MakeOwnershipContract(
            root_loader_file=_as_str(
                ownership_raw.get("root_loader_file"),
                "spec.make_contract.ownership.root_loader_file",
            ),
            blueprint_generated_file=_as_str(
                ownership_raw.get("blueprint_generated_file"),
                "spec.make_contract.ownership.blueprint_generated_file",
            ),
            platform_editable_file=_as_str(
                ownership_raw.get("platform_editable_file"),
                "spec.make_contract.ownership.platform_editable_file",
            ),
            platform_editable_include_dir=_as_str(
                ownership_raw.get("platform_editable_include_dir"),
                "spec.make_contract.ownership.platform_editable_include_dir",
            ),
            platform_seed_mode=_as_str(
                ownership_raw.get("platform_seed_mode"),
                "spec.make_contract.ownership.platform_seed_mode",
            ),
        ),
        optional_target_materialization=OptionalTargetMaterializationContract(
            mode=_as_str(
                materialization_raw.get("mode"),
                "spec.make_contract.optional_target_materialization.mode",
            ),
            source_template=_as_str(
                materialization_raw.get("source_template"),
                "spec.make_contract.optional_target_materialization.source_template",
            ),
            output_file=_as_str(
                materialization_raw.get("output_file"),
                "spec.make_contract.optional_target_materialization.output_file",
            ),
            materialization_command=_as_str(
                materialization_raw.get("materialization_command"),
                "spec.make_contract.optional_target_materialization.materialization_command",
            ),
        ),
    )

    architecture_raw = _as_mapping(spec.get("architecture"), "spec.architecture")
    airflow_raw = _as_mapping(architecture_raw.get("airflow_dag_layout"), "spec.architecture.airflow_dag_layout")
    architecture = ArchitectureContract(
        airflow_dag_layout=AirflowLayoutContract(
            dag_entrypoints_root=_as_str(
                airflow_raw.get("dag_entrypoints_root"),
                "spec.architecture.airflow_dag_layout.dag_entrypoints_root",
            ),
            shared_bootstrap_file=_as_str(
                airflow_raw.get("shared_bootstrap_file"),
                "spec.architecture.airflow_dag_layout.shared_bootstrap_file",
            ),
            forbid_dag_entrypoints_under=_as_str(
                airflow_raw.get("forbid_dag_entrypoints_under"),
                "spec.architecture.airflow_dag_layout.forbid_dag_entrypoints_under",
            ),
            airflowignore_must_restrict_parser_scope=_as_bool(
                airflow_raw.get("airflowignore_must_restrict_parser_scope"),
                "spec.architecture.airflow_dag_layout.airflowignore_must_restrict_parser_scope",
                default=False,
            ),
        )
    )

    optional_raw = _as_mapping(spec.get("optional_modules"), "spec.optional_modules")
    modules_raw = _as_mapping(optional_raw.get("modules"), "spec.optional_modules.modules")
    modules: dict[str, OptionalModuleContract] = {}
    for module_id, module_value in modules_raw.items():
        module_map = _as_mapping(module_value, f"spec.optional_modules.modules.{module_id}")
        paths = _optional_str_map(
            module_map,
            [
                "contract_path",
                "dags_path",
                "terraform_path",
                "helm_path",
                "gitops_path",
                "docs_path",
                "tests_path",
            ],
            f"spec.optional_modules.modules.{module_id}",
        )
        modules[module_id] = OptionalModuleContract(
            module_id=module_id,
            enabled_by_default=_as_bool(
                module_map.get("enabled_by_default"),
                f"spec.optional_modules.modules.{module_id}.enabled_by_default",
                default=False,
            ),
            enable_flag=_as_str(
                module_map.get("enable_flag"),
                f"spec.optional_modules.modules.{module_id}.enable_flag",
            ),
            scaffolding_mode=_as_str(
                module_map.get("scaffolding_mode"),
                f"spec.optional_modules.modules.{module_id}.scaffolding_mode",
            ),
            paths_required_when_enabled=_as_list_of_str(
                module_map.get("paths_required_when_enabled", []),
                f"spec.optional_modules.modules.{module_id}.paths_required_when_enabled",
            ),
            make_targets_mode=_as_str(
                module_map.get("make_targets_mode"),
                f"spec.optional_modules.modules.{module_id}.make_targets_mode",
            ),
            make_targets=_as_list_of_str(
                module_map.get("make_targets", []),
                f"spec.optional_modules.modules.{module_id}.make_targets",
            ),
            paths=paths,
        )

    return BlueprintContract(
        repository=repository,
        structure=structure,
        script_contract=script_contract,
        docs_contract=docs_contract,
        make_contract=make_contract,
        architecture=architecture,
        optional_modules=OptionalModulesContract(modules=modules),
        raw=raw,
    )


def load_module_contract(path: Path, repo_root: Path) -> ModuleContract:
    raw = load_yaml_subset(path)
    spec = _as_mapping(raw.get("spec"), f"{path}:spec")
    inputs = _as_mapping(spec.get("inputs"), f"{path}:spec.inputs")
    outputs = _as_mapping(spec.get("outputs"), f"{path}:spec.outputs")
    make_targets_raw = _as_mapping(spec.get("make_targets"), f"{path}:spec.make_targets")

    make_targets: dict[str, str] = {}
    for key, value in make_targets_raw.items():
        make_targets[_as_str(key, f"{path}:spec.make_targets.key")] = _as_str(
            value,
            f"{path}:spec.make_targets.{key}",
        )

    resolved_path = path.resolve()
    resolved_repo_root = repo_root.resolve()
    try:
        contract_path = resolved_path.relative_to(resolved_repo_root).as_posix()
    except ValueError:
        contract_path = path.relative_to(repo_root).as_posix()

    return ModuleContract(
        module_id=_as_str(spec.get("module_id"), f"{path}:spec.module_id"),
        purpose=_as_str(spec.get("purpose"), f"{path}:spec.purpose"),
        enabled_by_default=_as_bool(spec.get("enabled_by_default"), f"{path}:spec.enabled_by_default", default=False),
        enable_flag=_as_str(spec.get("enable_flag"), f"{path}:spec.enable_flag"),
        make_targets=make_targets,
        required_env=_as_list_of_str(inputs.get("required_env", []), f"{path}:spec.inputs.required_env"),
        outputs=_as_list_of_str(outputs.get("produced", []), f"{path}:spec.outputs.produced"),
        contract_path=contract_path,
    )
