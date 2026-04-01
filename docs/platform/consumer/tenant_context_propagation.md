# Tenant Context Propagation

This optional contract standardizes tenant and organization context across identity, HTTP APIs, asynchronous events, and observability.

## Enablement
- Contract toggle: `TENANT_CONTEXT_PROPAGATION_ENABLED`
- Default: `false`

Enablement for existing generated repositories:
```bash
TENANT_CONTEXT_PROPAGATION_ENABLED=true make infra-validate
```

## Identity Claims
Canonical claim names:
- `tenant_id`
- `organization_id`
- `user_id`

Optional claim:
- `tenant_role`

Baseline rule: user-initiated requests must include tenant and organization context.

## HTTP API Propagation
Required header names:
- `X-Tenant-ID`
- `X-Organization-ID`
- `X-Correlation-ID`

Recommended behavior:
- Reject missing required tenant context with HTTP `400`.
- Preserve correlation IDs across upstream/downstream calls.

## Async Event Propagation
Required envelope fields for tenant-aware events:
- `tenant_id`
- `organization_id`
- `correlation_id`
- `causation_id`

System-originated events may allow empty tenant context when explicitly marked as system events.

## Observability and Audit
Log fields:
- `tenant_id`
- `organization_id`
- `correlation_id`
- `trace_id`

Trace attributes:
- `tenant.id`
- `organization.id`
- `correlation.id`

Audit fields:
- `tenant_id`
- `organization_id`
- `actor_id`
- `action`
- `outcome`

## Reference Snippets
### Python / FastAPI
```python
tenant_id = request.headers.get("X-Tenant-ID")
organization_id = request.headers.get("X-Organization-ID")
correlation_id = request.headers.get("X-Correlation-ID")

if not tenant_id or not organization_id:
    raise HTTPException(status_code=400, detail="missing tenant context")
```

### JS/TS runtime
```ts
const tenantId = req.headers["x-tenant-id"] as string | undefined;
const organizationId = req.headers["x-organization-id"] as string | undefined;
const correlationId = req.headers["x-correlation-id"] as string | undefined;

if (!tenantId || !organizationId) {
  throw new Error("missing tenant context");
}
```
