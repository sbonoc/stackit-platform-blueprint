# Endpoint Exposure Model

This guide explains how to expose mixed public and protected UI/API surfaces on top of the shared Gateway API baseline.

## Policy Matrix
| Route class | Example host | Client style | Edge pattern | Current blueprint baseline |
| --- | --- | --- | --- | --- |
| Public touchpoint | `www.<base-domain>` | Browser | Gateway -> touchpoints | Supported as a consumer-owned route attachment |
| Protected touchpoint | `app.<base-domain>` | Browser | Gateway -> `oauth2-proxy` -> touchpoints | Supported via `identity-aware-proxy` |
| Public API | `public-api.<base-domain>` | Browser/app/client | Gateway -> backend | Supported as a consumer-owned route attachment |
| Protected API | `api.<base-domain>` | SPA/direct API client | Gateway -> backend with JWT validation, then backend authz | Target pattern; route/JWT policy remains consumer-owned |
| Internal API | no public host | SSR/BFF only | Internal service-to-service call | Recommended when possible |

## Ownership
- `public-endpoints` owns the shared edge baseline: Envoy Gateway controller install, `GatewayClass`, shared `Gateway`, and the `network` namespace used for route attachment.
- `identity-aware-proxy` owns interactive browser authentication: `oauth2-proxy`, Keycloak OIDC wiring, and the protected browser `HTTPRoute`.
- Application delivery owns direct public/API route attachments and any future JWT route policy resources.
- Backend services still own application authorization. Passing edge auth is not enough on its own.

## Recommended Topology
```mermaid
flowchart LR
  Internet --> Gateway["Gateway API / Envoy Gateway"]
  Gateway --> PublicUI["Public UI route"]
  PublicUI --> TouchpointsPublic["touchpoints"]

  Gateway --> ProtectedUI["Protected UI route"]
  ProtectedUI --> IAP["oauth2-proxy"]
  IAP --> TouchpointsProtected["touchpoints"]

  Gateway --> PublicAPI["Public API route"]
  PublicAPI --> BackendPublic["backend"]

  Gateway --> ProtectedAPI["Protected API route"]
  ProtectedAPI --> BackendProtected["backend"]

  TouchpointsProtected --> InternalAPI["Internal SSR/BFF call"]
  InternalAPI --> BackendInternal["backend"]
```

## Working Rules
- Do not force every host through `identity-aware-proxy`. Keep anonymous routes anonymous when that is the intended product behavior.
- Prefer host-based separation over mixing browser-cookie and bearer-token flows on the same public route.
- Keep SSR/BFF backend calls internal when possible instead of exposing an unnecessary public API hop.
- Treat JWT validation for direct API clients as a separate route concern from browser login. The current blueprint baseline establishes the shared gateway and protected browser route first; API JWT policy remains a follow-on consumer/platform concern.
