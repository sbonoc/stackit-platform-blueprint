# Traceability Matrix

## Requirement-to-Delivery Mapping

| Requirement | Design | Implementation | Test | Docs | Operational |
|---|---|---|---|---|---|
| REQ-001 (kustomization-ref check before delete) | ADR § Decision #203; architecture.md § Context A | `upgrade_consumer.py`: `_is_kustomization_referenced`, wired in `_classify_entries` | `test_upgrade_consumer.py`: T-001, T-002, T-104 | ADR flowchart | apply artifact `consumer_kustomization_ref_count` |
| REQ-002 (classify as consumer-kustomization-ref / skip) | ADR § Decision #203 | `_classify_entries`: new branch after `_is_consumer_owned_workload` | T-002, T-104; AC-001, AC-002 | ADR flowchart | apply artifact entry ownership field |
| REQ-003 (preserve existing delete behavior) | ADR § Consequences | `_classify_entries`: unchanged for non-referenced files | T-103 (AC-003) | — | — |
| REQ-004 (scan .tf merged content for duplicates) | ADR § Decision #204 | `upgrade_consumer.py`: `_tf_deduplicate_blocks`, wired in apply loop | T-006, T-007, T-008, T-105 | ADR flowchart | apply artifact `tf_dedup_count` |
| REQ-005 (auto-deduplicate byte-identical blocks) | ADR § Decision #204 | `_tf_deduplicate_blocks`: remove all but first occurrence | T-006, T-007, T-103 (AC-004) | — | apply artifact `deduplication_log` |
| REQ-006 (conflict artifact for non-identical duplicates) | ADR § Decision #204 | apply loop: emit conflict artifact when non-identical | T-008, T-105 (AC-005) | — | conflict artifact file |
| NFR-SEC-001 (yaml.safe_load only) | architecture.md § Non-Functional | `_is_kustomization_referenced`: `yaml.safe_load` | T-001 (validates no exec path) | — | — |
| NFR-OBS-001 (dedup log in apply artifact) | architecture.md § Non-Functional | apply loop: `deduplication_log` array in artifact | T-012, T-013 | — | apply artifact JSON |
| NFR-REL-001 (malformed kustomization.yaml → False + warning) | architecture.md § Reliability | `_is_kustomization_referenced`: try/except → False + stderr | T-001 (AC-006) | — | stderr log line |
| NFR-OPS-001 (apply artifact counters) | architecture.md § Non-Functional | apply artifact JSON: `consumer_kustomization_ref_count`, `tf_dedup_count` | T-011, T-012, T-013 | — | apply artifact JSON |
| AC-001 (patches ref → skip) | ADR § Decision #203 | `_is_kustomization_referenced` + `_classify_entries` | T-102, T-104 | — | — |
| AC-002 (resources ref → skip) | ADR § Decision #203 | `_is_kustomization_referenced` + `_classify_entries` | T-101, T-104 | — | — |
| AC-003 (no ref → delete unchanged) | ADR § Consequences | `_classify_entries`: fall-through to existing branch | T-103 | — | — |
| AC-004 (byte-identical dedup → merged-deduped) | ADR § Decision #204 | `_tf_deduplicate_blocks` + apply loop | T-006, T-007, T-103, T-105 | — | — |
| AC-005 (non-identical → conflict artifact) | ADR § Decision #204 | apply loop: conflict artifact path | T-008, T-105 | — | conflict artifact |
| AC-006 (malformed kustomization.yaml → False + warning) | ADR § Decision #203; NFR-REL-001 | `_is_kustomization_referenced`: try/except | T-001 | — | stderr |

## Evidence Paths (to be populated at Verify phase)

| Gate | Evidence path | Status |
|---|---|---|
| Pytest unit suite | `pytest tests/blueprint/test_upgrade_consumer.py` output | pending |
| quality-hooks-fast | `make quality-hooks-fast` output | pending |
| infra-validate | `make infra-validate` output | pending |
| blueprint-template-smoke | `make blueprint-template-smoke` output | pending |
| docs-build / docs-smoke | `make docs-build && make docs-smoke` output | pending |
| quality-hardening-review | `make quality-hardening-review` output | pending |
