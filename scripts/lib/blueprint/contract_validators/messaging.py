from __future__ import annotations

from pathlib import Path

from scripts.lib.blueprint.contract_schema import BlueprintContract
from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers


def validate_event_messaging_contract(
    repo_root: Path,
    contract: BlueprintContract,
    helpers: ContractValidationHelpers,
) -> list[str]:
    errors: list[str] = []
    spec_raw = helpers.mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("event_messaging_contract")
    if raw_contract_section is None:
        errors.append("spec.event_messaging_contract is required")
        return errors
    contract_section = helpers.mapping_or_error(
        raw_contract_section,
        "spec.event_messaging_contract",
        errors,
    )

    enabled_by_default = helpers.bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.event_messaging_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default:
        errors.append("spec.event_messaging_contract.enabled_by_default must be false")

    enable_flag = helpers.string_or_error(
        contract_section.get("enable_flag"),
        "spec.event_messaging_contract.enable_flag",
        errors,
    )
    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict) and enable_flag and enable_flag not in toggles_raw:
        errors.append(
            "spec.event_messaging_contract.enable_flag must reference an existing toggle: "
            f"{enable_flag}"
        )

    envelope = helpers.mapping_or_error(
        contract_section.get("envelope"),
        "spec.event_messaging_contract.envelope",
        errors,
    )
    required_fields = helpers.list_of_str_or_error(
        envelope.get("required_fields"),
        "spec.event_messaging_contract.envelope.required_fields",
        errors,
    )
    expected_required_fields = {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "producer_service",
        "correlation_id",
        "causation_id",
        "traceparent",
        "tenant_id",
        "organization_id",
        "payload",
    }
    missing_required_fields = sorted(expected_required_fields - set(required_fields))
    if missing_required_fields:
        errors.append(
            "spec.event_messaging_contract.envelope.required_fields missing canonical fields: "
            + ", ".join(missing_required_fields)
        )
    optional_fields = helpers.list_of_str_or_error(
        envelope.get("optional_fields"),
        "spec.event_messaging_contract.envelope.optional_fields",
        errors,
    )
    if "metadata" not in optional_fields:
        errors.append("spec.event_messaging_contract.envelope.optional_fields must include metadata")

    versioning = helpers.mapping_or_error(
        contract_section.get("versioning_policy"),
        "spec.event_messaging_contract.versioning_policy",
        errors,
    )
    helpers.bool_or_error(
        versioning.get("additive_evolution_default"),
        "spec.event_messaging_contract.versioning_policy.additive_evolution_default",
        errors,
    )
    deprecation_window = helpers.int_or_error(
        versioning.get("deprecation_window_releases"),
        "spec.event_messaging_contract.versioning_policy.deprecation_window_releases",
        errors,
    )
    if deprecation_window is not None and deprecation_window < 1:
        errors.append("spec.event_messaging_contract.versioning_policy.deprecation_window_releases must be >= 1")
    overlap_window = helpers.int_or_error(
        versioning.get("overlap_window_releases"),
        "spec.event_messaging_contract.versioning_policy.overlap_window_releases",
        errors,
    )
    if overlap_window is not None and overlap_window < 1:
        errors.append("spec.event_messaging_contract.versioning_policy.overlap_window_releases must be >= 1")
    helpers.bool_or_error(
        versioning.get("dual_publish_required_for_breaking"),
        "spec.event_messaging_contract.versioning_policy.dual_publish_required_for_breaking",
        errors,
    )
    helpers.bool_or_error(
        versioning.get("dual_read_required_for_breaking"),
        "spec.event_messaging_contract.versioning_policy.dual_read_required_for_breaking",
        errors,
    )

    reliability = helpers.mapping_or_error(
        contract_section.get("reliability"),
        "spec.event_messaging_contract.reliability",
        errors,
    )
    outbox = helpers.mapping_or_error(
        reliability.get("outbox"),
        "spec.event_messaging_contract.reliability.outbox",
        errors,
    )
    helpers.bool_or_error(
        outbox.get("contract_required"),
        "spec.event_messaging_contract.reliability.outbox.contract_required",
        errors,
    )
    inbox = helpers.mapping_or_error(
        reliability.get("inbox"),
        "spec.event_messaging_contract.reliability.inbox",
        errors,
    )
    helpers.bool_or_error(
        inbox.get("contract_required"),
        "spec.event_messaging_contract.reliability.inbox.contract_required",
        errors,
    )
    idempotency = helpers.mapping_or_error(
        reliability.get("idempotency"),
        "spec.event_messaging_contract.reliability.idempotency",
        errors,
    )
    helpers.bool_or_error(
        idempotency.get("contract_required"),
        "spec.event_messaging_contract.reliability.idempotency.contract_required",
        errors,
    )
    idempotency_key_fields = helpers.list_of_str_or_error(
        idempotency.get("key_fields"),
        "spec.event_messaging_contract.reliability.idempotency.key_fields",
        errors,
    )
    for required_key in ("event_id", "consumer_name"):
        if required_key not in idempotency_key_fields:
            errors.append(
                "spec.event_messaging_contract.reliability.idempotency.key_fields must include "
                f"{required_key}"
            )

    retry = helpers.mapping_or_error(
        reliability.get("retry"),
        "spec.event_messaging_contract.reliability.retry",
        errors,
    )
    retry_strategy = helpers.string_or_error(
        retry.get("strategy"),
        "spec.event_messaging_contract.reliability.retry.strategy",
        errors,
    )
    if retry_strategy != "exponential-backoff-with-jitter":
        errors.append(
            "spec.event_messaging_contract.reliability.retry.strategy must be exponential-backoff-with-jitter"
        )

    dead_letter_queue = helpers.mapping_or_error(
        reliability.get("dead_letter_queue"),
        "spec.event_messaging_contract.reliability.dead_letter_queue",
        errors,
    )
    helpers.string_or_error(
        dead_letter_queue.get("naming_pattern"),
        "spec.event_messaging_contract.reliability.dead_letter_queue.naming_pattern",
        errors,
    )
    helpers.bool_or_error(
        dead_letter_queue.get("replay_contract_required"),
        "spec.event_messaging_contract.reliability.dead_letter_queue.replay_contract_required",
        errors,
    )

    scaffolding_hooks = helpers.mapping_or_error(
        contract_section.get("scaffolding_hooks"),
        "spec.event_messaging_contract.scaffolding_hooks",
        errors,
    )
    for path_key in (
        "producer_contract_dir",
        "consumer_contract_dir",
        "outbox_template_path",
        "inbox_template_path",
        "idempotency_template_path",
    ):
        path_value = helpers.string_or_error(
            scaffolding_hooks.get(path_key),
            f"spec.event_messaging_contract.scaffolding_hooks.{path_key}",
            errors,
        )
        if not path_value:
            continue
        if not (repo_root / path_value).exists():
            errors.append(f"missing event messaging scaffolding hook path: {path_value}")

    docs_path = repo_root / "docs/platform/consumer/event_messaging_baseline.md"
    if docs_path.is_file():
        docs_content = docs_path.read_text(encoding="utf-8")
        if "Python / FastAPI" not in docs_content:
            errors.append("docs/platform/consumer/event_messaging_baseline.md must include Python / FastAPI guidance")
        if "JS/TS runtime" not in docs_content:
            errors.append("docs/platform/consumer/event_messaging_baseline.md must include JS/TS runtime guidance")

    return errors
