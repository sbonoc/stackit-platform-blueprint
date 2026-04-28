# ADR-20260428 — Newline-primary delimiter for RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS

- **Status:** proposed
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

Adopt **newline-primary delimiter** for `parse_literal_pairs()`:

1. If the input string contains one or more `\n` characters → split on newlines (primary format, supports any value content).
2. If the input string contains no `\n` characters → split on commas (legacy format, safe only when values contain no commas).

This is detected with a single bash conditional:
```bash
if [[ "$literals" != *$'\n'* ]]; then
  literals="${literals//,/$'\n'}"
fi
while IFS= read -r pair; do
  ...
done <<< "$literals"
```

Recommended format in documentation and new consumer code:
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS=$'username=local-user\nNUXT_OIDC_TOKEN_KEY=data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE='
```

Legacy format (comma-separated, backward-compatible when values have no commas):
```bash
export RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS='username=local-user,password=simple-pass'
```

## Alternatives Considered

### Option B — Newline-only strict

Reject comma-separated input entirely, require all consumers to migrate to newline format.

**Rejected because:** The consumer workaround already uses newline format; forcing a
strict break would require a migration window and break consumers who haven't yet applied
the workaround but whose values happen to have no commas (they would need to convert but
their current setup works fine).

### Option C — Escape mechanism (`\,`)

Add a backslash-escape rule: `\,` within a value is treated as a literal comma, not a delimiter.

**Rejected because:** Escape mechanisms require consumers to audit and re-escape all
existing values, and the bash `IFS` split does not natively support escape sequences.
Newline-primary is simpler, unambiguous, and already adopted by the consumer workaround.

## Consequences

- **Positive:** Consumers using newline-separated format (the workaround) require no
  changes and become the canonical path. Values containing commas (data URIs, connection
  strings, JWTs) are handled correctly.
- **Positive:** Existing consumers using comma-separated format with values that contain
  no commas continue to work without any migration.
- **Negative:** If a consumer passes a newline character as part of a value using the
  legacy comma format, it would be misinterpreted as a pair delimiter. This is
  theoretical — newlines cannot appear in bash `export VAR=...` values without explicit
  `$'...'` quoting.
- **Operational:** Documentation must explicitly state that the comma-separated format
  is legacy and restricted to values without commas.
