# Event Messaging Baseline

This contract is optional and additive. It standardizes async message envelopes and reliability primitives for generated consumers.

## Enablement
- Contract toggle: `EVENT_MESSAGING_BASELINE_ENABLED`
- Default: `false`
- Baseline mode (disabled): no behavior change

For existing generated repositories, upgrade first, then opt in with:
```bash
EVENT_MESSAGING_BASELINE_ENABLED=true make infra-validate
```

## Canonical Envelope
Use these field names in every published message envelope.

| Field | Required | Notes |
| --- | --- | --- |
| `event_id` | yes | UUIDv4 preferred |
| `event_type` | yes | Stable semantic event name |
| `event_version` | yes | Semantic version of payload contract |
| `occurred_at` | yes | RFC3339/ISO-8601 UTC timestamp |
| `producer_service` | yes | Stable producer identifier |
| `correlation_id` | yes | End-to-end request/workflow correlation |
| `causation_id` | yes | Previous event/request identifier |
| `traceparent` | yes | W3C trace context carrier |
| `tenant_id` | yes | Tenant context propagation key |
| `organization_id` | yes | Organization context key |
| `payload` | yes | Business payload |
| `metadata` | optional | Transport/runtime metadata |

## Versioning Policy
- Additive evolution is the default.
- Keep compatibility overlap windows for at least `2` releases.
- Breaking changes require dual-publish and dual-read windows.
- Keep deprecation windows explicit (minimum `2` releases).

Recommended rollout:
1. Publish new version in parallel (`vN` + `vN+1`).
2. Consumers dual-read both versions.
3. Observe full overlap window.
4. Stop publishing old version.
5. Remove old consumer paths after the deprecation window.

## Reliability Contract
Use the following primitives as a baseline contract.

### Outbox
- Persist event records transactionally with domain write operations.
- Keep `event_id`, `event_type`, `event_version`, `payload`, `occurred_at`, and dispatch state columns.

### Inbox
- Persist consumed `event_id` and consumer identifier.
- Acknowledge only after successful idempotent processing.

### Idempotency
- Canonical deduplication key: `event_id + consumer_name`.
- Replays must not produce duplicate side effects.

### Retries and DLQ
- Use exponential backoff + jitter.
- Dead-letter queue naming pattern: `<event_type>.dlq`.
- Keep replay procedures documented and auditable.

## Scaffolding Hooks
The contract defines scaffold template hooks for SQL primitives:
- `scripts/templates/consumer/scaffold/messaging/sql/outbox.sql.tmpl`
- `scripts/templates/consumer/scaffold/messaging/sql/inbox.sql.tmpl`
- `scripts/templates/consumer/scaffold/messaging/sql/idempotency_keys.sql.tmpl`

## Reference Implementation Paths
### Python / FastAPI (producer)
```python
message = {
    "event_id": str(uuid4()),
    "event_type": "catalog.item.created",
    "event_version": "1.0.0",
    "occurred_at": datetime.now(timezone.utc).isoformat(),
    "producer_service": "catalog-api",
    "correlation_id": correlation_id,
    "causation_id": request_id,
    "traceparent": traceparent,
    "tenant_id": tenant_id,
    "organization_id": organization_id,
    "payload": payload,
    "metadata": {"content_type": "application/json"},
}
```

### JS/TS runtime (consumer)
```ts
const dedupeKey = `${message.event_id}:${consumerName}`;
const alreadyProcessed = await inboxStore.has(dedupeKey);
if (alreadyProcessed) return;

await handleBusinessPayload(message.payload);
await inboxStore.markProcessed(dedupeKey, message.occurred_at);
```
