# ADR: Force-Taint `stackit_ske_kubeconfig` on Every Refresh Run

- **Status:** proposed
- **Issue:** [#394](https://github.com/sbonoc/stackit-platform-blueprint/issues/394)
- **Date:** 2026-07-08
- **Author:** bonos

## Context

`stackit_ske_kubeconfig` is a STACKIT Terraform provider resource that generates a
client-certificate kubeconfig with a TTL of approximately 1 hour (`notAfter = notBefore + 1h`).

The `infra-stackit-foundation-refresh-kubeconfig` make target runs
`stackit_foundation_apply.sh` followed by `stackit_foundation_fetch_kubeconfig.sh`.
Because no Terraform configuration changes between refresh runs, `terraform apply`
reports "No changes" and returns the existing — now expired — kubeconfig from state.

Any `kubectl` call made more than ~1 hour after the last successful refresh fails with:

```
error: You must be logged in to the server (Unauthorized)
```

The only recovery path prior to this fix is a manual
`terraform taint stackit_ske_kubeconfig.foundation[0]` followed by re-running the
refresh target. This recovery path is not documented and not operator-discoverable.

## Decision

In `stackit_foundation_fetch_kubeconfig.sh`, when `tooling_is_execution_enabled` is
true (i.e. `DRY_RUN=false`), force-taint `stackit_ske_kubeconfig.foundation[0]`
before `terraform apply` so that Terraform always destroys and recreates the resource,
regenerating the client certificate regardless of configuration drift.

The taint step is unconditionally skipped when `DRY_RUN=true` — dry-run mode MUST NOT
perform any mutating Terraform operations.

```
flowchart TD
    A[make infra-stackit-foundation-refresh-kubeconfig] --> B{DRY_RUN?}
    B -- false --> C[terraform taint stackit_ske_kubeconfig.foundation 0]
    C --> D[terraform apply]
    D --> E[terraform output ske_kubeconfig]
    E --> F[write kubeconfig to disk]
    B -- true --> G[skip taint]
    G --> H[write placeholder kubeconfig]
    F --> I[chmod 600]
    H --> I
```

## Considered Alternatives

**Option B — Expiry check after output:** Decode the certificate after `terraform output`
and taint + re-apply only when `notAfter` is within a threshold (e.g. 15 minutes). Rejected
because: (1) adds `openssl x509` / `date` parsing that can fail on non-standard cert formats;
(2) still requires a second apply round-trip on expiry; (3) adds complexity without correctness
benefit over Option A. Could be layered as a complementary guard in `make infra-smoke` (see
Deferred Proposals in spec.md).

**Option C — ServiceAccount token auth:** Replace the client-certificate kubeconfig with a
`ServiceAccount` token of configurable duration, eliminating the TTL coupling from the
Terraform resource lifecycle entirely. Not selected for this fix because it requires
STACKIT SKE SA-token provision to be stable and constitutes a separate scope change.
Tracked as a deferred proposal.

## Consequences

- `make infra-stackit-foundation-refresh-kubeconfig` always produces a non-expired kubeconfig
  in execute mode, regardless of elapsed time since the previous run.
- One additional Terraform API round-trip (taint call) is added per refresh. This is fast
  (the resource has no data) and is the intended usage pattern for ephemeral STACKIT resources.
- The fix follows the existing precedent in `stackit_foundation_apply.sh` where
  `stackit_postgresflex_instance.foundation[0]` is untainted before retry apply to reconcile
  transient state.
- Dry-run mode is unaffected — no Terraform mutations in dry-run.
