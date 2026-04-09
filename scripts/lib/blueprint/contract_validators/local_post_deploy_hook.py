from __future__ import annotations

from pathlib import Path

from scripts.lib.blueprint.contract_schema import BlueprintContract
from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers


def _mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def validate_local_post_deploy_hook_contract(
    repo_root: Path,
    contract: BlueprintContract,
    helpers: ContractValidationHelpers,
) -> list[str]:
    errors: list[str] = []
    spec_raw = helpers.mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("local_post_deploy_hook_contract")
    if raw_contract_section is None:
        errors.append("spec.local_post_deploy_hook_contract is required")
        return errors
    contract_section = helpers.mapping_or_error(
        raw_contract_section,
        "spec.local_post_deploy_hook_contract",
        errors,
    )
    contract_enabled = helpers.is_optional_contract_enabled(spec_raw, contract_section)

    enabled_by_default = helpers.bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.local_post_deploy_hook_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default is not False:
        errors.append("spec.local_post_deploy_hook_contract.enabled_by_default must be false")

    enable_flag = helpers.string_or_error(
        contract_section.get("enable_flag"),
        "spec.local_post_deploy_hook_contract.enable_flag",
        errors,
    )
    command_env_var = helpers.string_or_error(
        contract_section.get("command_env_var"),
        "spec.local_post_deploy_hook_contract.command_env_var",
        errors,
    )
    strict_mode_env_var = helpers.string_or_error(
        contract_section.get("strict_mode_env_var"),
        "spec.local_post_deploy_hook_contract.strict_mode_env_var",
        errors,
    )
    invocation_target = helpers.string_or_error(
        contract_section.get("invocation_target"),
        "spec.local_post_deploy_hook_contract.invocation_target",
        errors,
    )
    invocation_script = helpers.string_or_error(
        contract_section.get("invocation_script"),
        "spec.local_post_deploy_hook_contract.invocation_script",
        errors,
    )
    consumer_target = ""
    raw_consumer_target = contract_section.get("consumer_target")
    if contract_enabled:
        consumer_target = helpers.string_or_error(
            raw_consumer_target,
            "spec.local_post_deploy_hook_contract.consumer_target",
            errors,
        )
    elif isinstance(raw_consumer_target, str):
        consumer_target = raw_consumer_target
    state_artifact_path = helpers.string_or_error(
        contract_section.get("state_artifact_path"),
        "spec.local_post_deploy_hook_contract.state_artifact_path",
        errors,
    )

    run_profiles = helpers.list_of_str_or_error(
        contract_section.get("run_profiles"),
        "spec.local_post_deploy_hook_contract.run_profiles",
        errors,
    )
    required_paths = helpers.list_of_str_or_error(
        contract_section.get("required_paths_when_enabled"),
        "spec.local_post_deploy_hook_contract.required_paths_when_enabled",
        errors,
    )
    docs_paths = helpers.list_of_str_or_error(
        contract_section.get("docs_paths"),
        "spec.local_post_deploy_hook_contract.docs_paths",
        errors,
    )

    if not required_paths:
        errors.append("spec.local_post_deploy_hook_contract.required_paths_when_enabled must not be empty")
    if not docs_paths:
        errors.append("spec.local_post_deploy_hook_contract.docs_paths must not be empty")
    for docs_path in docs_paths:
        if not (repo_root / docs_path).is_file():
            errors.append(f"missing local post-deploy hook docs path: {docs_path}")

    supported_profiles = helpers.list_of_str_or_error(
        helpers.mapping_or_error(spec_raw.get("profiles"), "spec.profiles", errors).get("supported"),
        "spec.profiles.supported",
        errors,
    )
    if not run_profiles:
        errors.append("spec.local_post_deploy_hook_contract.run_profiles must not be empty")
    else:
        missing_required_profiles = sorted({"local-lite", "local-full"} - set(run_profiles))
        if missing_required_profiles:
            errors.append(
                "spec.local_post_deploy_hook_contract.run_profiles missing required local profiles: "
                + ", ".join(missing_required_profiles)
            )
        unsupported_profiles = sorted(profile for profile in run_profiles if profile not in set(supported_profiles))
        if unsupported_profiles:
            errors.append(
                "spec.local_post_deploy_hook_contract.run_profiles references unsupported profiles: "
                + ", ".join(unsupported_profiles)
            )

    make_targets = helpers.make_targets(repo_root)
    if invocation_target and invocation_target not in make_targets:
        errors.append(
            "spec.local_post_deploy_hook_contract.invocation_target references missing make target: "
            f"{invocation_target}"
        )
    if contract_enabled and consumer_target and consumer_target not in make_targets:
        errors.append(
            "spec.local_post_deploy_hook_contract.consumer_target references missing make target: "
            f"{consumer_target}"
        )

    if invocation_script and not (repo_root / invocation_script).is_file():
        errors.append(f"missing local post-deploy hook invocation script: {invocation_script}")
    if state_artifact_path and not state_artifact_path.endswith(".env"):
        errors.append("spec.local_post_deploy_hook_contract.state_artifact_path must end with .env")

    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict):
        for key, env_name in (
            ("enable_flag", enable_flag),
            ("command_env_var", command_env_var),
            ("strict_mode_env_var", strict_mode_env_var),
        ):
            if not env_name:
                continue
            if env_name not in toggles_raw:
                errors.append(
                    f"spec.local_post_deploy_hook_contract.{key} must reference an existing toggle: {env_name}"
                )

        strict_toggle = _mapping(toggles_raw.get(strict_mode_env_var))
        if strict_toggle:
            if strict_toggle.get("type") != "boolean":
                errors.append(
                    "spec.local_post_deploy_hook_contract.strict_mode_env_var must reference a boolean toggle"
                )
            if strict_toggle.get("default") is not False:
                errors.append(
                    "spec.local_post_deploy_hook_contract.strict_mode_env_var default must be false (best-effort)"
                )

        command_toggle = _mapping(toggles_raw.get(command_env_var))
        if command_toggle:
            if command_toggle.get("type") != "string":
                errors.append("spec.local_post_deploy_hook_contract.command_env_var must reference a string toggle")
            command_default = str(command_toggle.get("default", "")).strip()
            if not command_default:
                errors.append("spec.local_post_deploy_hook_contract.command_env_var default must not be empty")
            if consumer_target and consumer_target not in command_default:
                errors.append(
                    "spec.local_post_deploy_hook_contract.command_env_var default must invoke consumer target "
                    f"{consumer_target}"
                )

        enabled_toggle = _mapping(toggles_raw.get(enable_flag))
        if enabled_toggle:
            if enabled_toggle.get("type") != "boolean":
                errors.append("spec.local_post_deploy_hook_contract.enable_flag must reference a boolean toggle")
            if enabled_toggle.get("default") is not False:
                errors.append("spec.local_post_deploy_hook_contract.enable_flag default must be false (opt-in)")

    if invocation_script:
        invocation_script_path = repo_root / invocation_script
        if invocation_script_path.is_file():
            script_content = invocation_script_path.read_text(encoding="utf-8")
            for marker in ("local_post_deploy_hook_run", "LOCAL_POST_DEPLOY_HOOK_"):
                if marker not in script_content:
                    errors.append(
                        "local post-deploy hook invocation script is missing required marker "
                        f"{marker}: {invocation_script}"
                    )

    platform_make_path = repo_root / "make/platform.mk"
    if contract_enabled and platform_make_path.is_file() and consumer_target:
        platform_make_content = platform_make_path.read_text(encoding="utf-8")
        if f"{consumer_target}:" not in platform_make_content:
            errors.append(f"make/platform.mk missing consumer hook target definition: {consumer_target}")

    if not contract_enabled:
        return errors

    errors.extend(helpers.validate_required_paths(repo_root, required_paths))
    return errors
