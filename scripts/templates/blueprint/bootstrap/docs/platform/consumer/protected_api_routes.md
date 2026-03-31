# Protected API Routes

Use this pattern when a public host must expose a bearer-token API for an SPA or direct client.

## Recommended Pattern
- Keep the shared `Gateway` in the edge-owned `network` namespace.
- Create the protected API `HTTPRoute` in the same namespace as the backend workload, usually `apps`.
- Attach an Envoy Gateway `SecurityPolicy` to that `HTTPRoute` in the same namespace.
- Keep backend authorization mandatory even after JWT validation at the edge.

## Ownership Boundary
- `public-endpoints` owns the shared edge baseline and the dedicated `platform-edge-*` Argo CD project for Envoy Gateway controller and shared `Gateway` resources.
- Application delivery owns protected API `HTTPRoute` and `SecurityPolicy` resources in app namespaces through the main `platform-*` Argo CD project.
- `identity-aware-proxy` is not part of this bearer-token path. It is the browser-login path for protected touchpoints.

## Example Resources
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: backend-api
  namespace: apps
spec:
  parentRefs:
    - name: public-endpoints
      namespace: network
      sectionName: http
  hostnames:
    - api.example.com
  rules:
    - backendRefs:
        - name: backend
          port: 8080
---
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: backend-api-jwt
  namespace: apps
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      name: backend-api
  jwt:
    providers:
      - name: keycloak
        issuer: https://auth.example.invalid/realms/iap
        audiences:
          - platform-api
        remoteJWKS:
          uri: https://auth.example.invalid/realms/iap/protocol/openid-connect/certs
```

## Working Rules
- Keep the `SecurityPolicy` in the same namespace as the protected API `HTTPRoute`.
- Do not attach JWT policy to the shared `Gateway` in `network`; keep auth policy closest to the route it protects.
- Prefer a dedicated API host such as `api.<base-domain>` instead of mixing browser-cookie and bearer-token flows on the same route.
- Use the route layer for authentication and coarse claim checks, then keep fine-grained authorization in backend code.
- Only expose a protected API publicly when SSR/BFF internal calls are not the better fit.
