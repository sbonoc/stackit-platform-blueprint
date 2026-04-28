# ADR-20260428 — Newline-only delimiter for RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS

- **Status:** approved
- **Work item:** 2026-04-28-issue-234-literal-pairs-newline-format
- **Date:** 2026-04-28

## Context

`RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` accepts a user-supplied list of `key=value`
pairs for seeding the `runtime-credentials-source` Kubernetes secret.
`parse_literal_pairs()` in `reconcile_eso_runtime_secrets.sh` split this input on commas
via `IFS=',' read -r -a raw_pairs`.

The default value for `NUXT_OIDC_TOKEN_KEY` is a data URI:
`data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE=`. This value contains a
literal comma between the media-type and the base64 payload. When the consumer concatenated
this value with others using `IFS=,`, the parser received three tokens instead of two:

```
username=local-user
NUXT_OIDC_TOKEN_KEY=data:;base64          ← split here
bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE=   ← no "=" → parse failure
```

`parse_literal_pairs()` returned 1, `record_reconcile_issue` recorded the error, and the
`runtime-credentials-source` secret was never created — leaving all ExternalSecrets
`NotReady` and blocking ArgoCD sync for all app namespaces.

The failure was silent when `RUNTIME_CREDENTIALS_REQUIRED=false` (the default), making it
hard to detect without inspecting reconcile artifacts.

## Decision

Adopt **newline-only delimiter** for `parse_literal_pairs()` — a clean breaking change:

- `RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS` MUST use newline-separated `key=value` pairs.
- Comma-separated input is rejected; `parse_literal_pairs()` returns 1 and emits `log_warn`.
- No backward-compatibility mode.

Implementation:
```bash
parse_literal_pairs() {
  local literals="$1"
  local pair key value
  [[ -n "$literals" ]] || return 0

  while IFS= read -r pair; do
    pair="$(trim_whitespace "$pair")"
    [[ -n "$pair" ]] || continue
    if [[ "$pair" != *=* ]]; then
      log_warn "parse_literal_pairs: invalid pair (missing '='): $pair"
      log_warn "parse_literal_pairs: expected format: key=value (one per line)"
      return 1
    fi
    key="$(trim_whitespace "${pair%%=*}")"
    value="${pair#*=}"
    if [[ -z "$key" || -z "$value" ]]; then
      log_warn "parse_literal_pairs: empty key or value in pair: $pair"
      return 1
    fi
    printf '%s\n' "$key=$value"
  done <<< "$literals"
}
```

Recommended consumer format (using bash `$'...'` quoting for literal newlines):
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS=$'username=local-user\nNUXT_OIDC_TOKEN_KEY=data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE='
```

Or using a multi-line assignment:
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS="username=local-user
NUXT_OIDC_TOKEN_KEY=data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE="
```

## Alternatives Considered

### Option A — Newline-primary with comma fallback

When input contains `\n`, split on newlines; otherwise split on commas.

**Rejected because:** The comma-separated format is inherently unsafe for any value
containing a comma. Keeping it as a fallback preserves the ambiguity and creates a
class of values that silently fail only when they happen to contain commas. A clean
break is architecturally unambiguous and eliminates the problem class permanently.
Consumers who have not migrated receive a visible `log_warn` diagnostic (FR-002)
rather than the current silent failure, which is strictly better for operability.

### Option C — Escape mechanism (`\,`)

Add a backslash-escape rule: `\,` within a value is treated as a literal comma.

**Rejected because:** Escape mechanisms require consumers to audit and re-escape all
existing values; the bash `IFS` split does not natively support escape sequences;
newline-only is simpler and unambiguous.

## Consequences

- **Positive:** No ambiguous delimiter detection. Values containing commas (data URIs,
  connection strings, JWTs, base64 payloads) are handled correctly by design.
- **Positive:** `log_warn` on parse failure ensures consumers who pass comma-separated
  input see an actionable diagnostic even when `RUNTIME_CREDENTIALS_REQUIRED=false`.
- **Breaking:** Consumers using comma-separated format must update their env var
  serializer to newline-separated. The consumer workaround already uses newline format.
- **Operational:** Documentation must explicitly state that comma-separated format is
  no longer accepted, with migration instructions and examples using `$'...'` quoting.
