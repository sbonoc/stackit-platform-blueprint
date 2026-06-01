"""Tests for is_transient_registry_error in scripts/bin/infra/audit_version.sh.

These tests guard against transient registry failures being misclassified as
permanent "image not found" failures.  The root cause of the CI regression:
quay.io dropped TCP/TLS connections during a partial outage; docker manifest
inspect returned an error containing "EOF" rather than a recognisable HTTP
5xx code; is_transient_registry_error returned false; the check was emitted
as a failure (status=missing) instead of a warning (status=unavailable).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_VERSION_SH = REPO_ROOT / "scripts/bin/infra/audit_version.sh"

_FUNC_EXTRACT = """
is_transient_registry_error() {
  local error_text="$1"
  local lowered
  lowered="$(printf '%s' "$error_text" | tr '[:upper:]' '[:lower:]')"
"""

def _call_is_transient(error_text: str) -> bool:
    """Source just the function from audit_version.sh and invoke it with error_text."""
    script = f"""
set -euo pipefail
source_path="{AUDIT_VERSION_SH}"
# Extract and eval only the function definition; avoid sourcing the full script
# (which runs side-effectful code and requires additional dependencies).
func_body="$(awk '/^is_transient_registry_error\\(\\){{/,/^}}/' "$source_path")"
if [[ -z "$func_body" ]]; then
  # Fallback: the function may use a space before the brace
  func_body="$(awk '/^is_transient_registry_error\\(\\) {{/,/^}}/' "$source_path")"
fi
eval "$func_body"
if is_transient_registry_error {_q(error_text)}; then
  echo "TRANSIENT"
else
  echo "PERMANENT"
fi
"""
    # Build the script without shell quoting issues by passing via env
    invoke = f"""
set -euo pipefail
source "{AUDIT_VERSION_SH}" 2>/dev/null || true
# Re-define only the target function from the file to avoid running the audit
func_body=$(grep -A100 '^is_transient_registry_error()' "{AUDIT_VERSION_SH}" | awk 'NR==1{{p=1}} p{{print}} /^}}$/{{exit}}')
eval "$func_body"
if is_transient_registry_error "$INPUT_TEXT"; then
  echo "TRANSIENT"
else
  echo "PERMANENT"
fi
"""
    result = subprocess.run(
        ["bash", "-c", invoke],
        capture_output=True,
        text=True,
        env={"INPUT_TEXT": error_text, "PATH": "/usr/local/bin:/usr/bin:/bin"},
    )
    return result.stdout.strip() == "TRANSIENT"


def _is_transient(error_text: str) -> bool:
    """Evaluate is_transient_registry_error purely via bash pattern matching."""
    patterns_true = [
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",
        "context deadline exceeded",
        "client.timeout exceeded",
        "i/o timeout",
        "connection reset by peer",
        "tls handshake timeout",
        "too many requests",
        "429",
        " eof",
        ":eof",
        "unexpected eof",
        "connection timed out",
    ]
    lowered = error_text.lower()
    return any(p in lowered for p in patterns_true)


class TestIsTransientRegistryErrorPatterns:
    """Verify that is_transient_registry_error covers all expected transient patterns.

    These tests use the same logic as the bash function by reading the pattern
    list directly from the script file, ensuring the script and test stay in sync.
    """

    def _patterns_in_script(self) -> list[str]:
        content = AUDIT_VERSION_SH.read_text(encoding="utf-8")
        start = content.find("is_transient_registry_error()")
        end = content.find("\nreturn 1", start)
        func_body = content[start:end]
        patterns = []
        for line in func_body.splitlines():
            line = line.strip()
            if line.startswith('[[ "$lowered"') and '== *"' in line:
                pat = line.split('*"')[1].split('"')[0]
                patterns.append(pat)
        return patterns

    def test_function_exists_in_script(self) -> None:
        content = AUDIT_VERSION_SH.read_text(encoding="utf-8")
        assert "is_transient_registry_error()" in content

    def test_eof_pattern_covered(self) -> None:
        """EOF: docker emits this when registry drops TCP without HTTP response (quay.io outage)."""
        patterns = self._patterns_in_script()
        eof_patterns = [p for p in patterns if "eof" in p]
        assert eof_patterns, (
            "is_transient_registry_error must cover 'eof' — "
            "quay.io drops TCP silently during partial outages and docker emits EOF"
        )

    def test_unexpected_eof_pattern_covered(self) -> None:
        """Unexpected EOF: occurs when the registry sends partial headers then closes."""
        patterns = self._patterns_in_script()
        assert any("unexpected eof" in p for p in patterns), (
            "is_transient_registry_error must cover 'unexpected eof'"
        )

    def test_connection_timed_out_pattern_covered(self) -> None:
        """TCP-level connection timeout (distinct from TLS handshake timeout)."""
        patterns = self._patterns_in_script()
        assert any("connection timed out" in p for p in patterns), (
            "is_transient_registry_error must cover 'connection timed out'"
        )

    def test_existing_http_5xx_patterns_still_present(self) -> None:
        """Regression: existing HTTP 5xx patterns must not be accidentally removed."""
        patterns = self._patterns_in_script()
        for required in ("502 bad gateway", "503 service unavailable", "504 gateway timeout"):
            assert any(required in p for p in patterns), (
                f"is_transient_registry_error must still cover '{required}'"
            )

    def test_context_deadline_exceeded_still_present(self) -> None:
        patterns = self._patterns_in_script()
        assert any("context deadline exceeded" in p for p in patterns)

    def test_429_still_present(self) -> None:
        patterns = self._patterns_in_script()
        assert any("429" in p for p in patterns)


class TestTransientPatternSemantics:
    """Verify the pattern logic against representative docker error strings.

    Uses the same pattern logic as the bash function (extracted from the script)
    so these tests would fail if a pattern is removed or mis-typed.
    """

    def _patterns(self) -> list[str]:
        content = AUDIT_VERSION_SH.read_text(encoding="utf-8")
        start = content.find("is_transient_registry_error()")
        end = content.find("\nreturn 1", start)
        func_body = content[start:end]
        patterns = []
        for line in func_body.splitlines():
            line = line.strip()
            if line.startswith('[[ "$lowered"') and '== *"' in line:
                pat = line.split('*"')[1].split('"')[0]
                patterns.append(pat)
        return patterns

    def _check(self, error_text: str) -> bool:
        lowered = error_text.lower()
        return any(p in lowered for p in self._patterns())

    # --- EOF variants (the pattern that caused the CI regression) ---

    def test_eof_bare_is_transient(self) -> None:
        """docker manifest inspect returns 'EOF' on silent TCP drop from quay.io."""
        assert self._check('Error response from daemon: Get "https://quay.io/v2/": EOF')

    def test_eof_in_url_path_is_transient(self) -> None:
        assert self._check(
            'Error response from daemon: Get '
            '"https://quay.io/v2/oauth2-proxy/oauth2-proxy/manifests/v7.15.0": EOF'
        )

    def test_unexpected_eof_is_transient(self) -> None:
        assert self._check(
            'Error response from daemon: unexpected EOF'
        )

    def test_unexpected_eof_lowercase_is_transient(self) -> None:
        assert self._check("unexpected eof reading response body")

    # --- TCP timeout ---

    def test_connection_timed_out_is_transient(self) -> None:
        assert self._check(
            'Error response from daemon: dial tcp [::1]:443: connect: connection timed out'
        )

    # --- Pre-existing patterns still work ---

    def test_504_is_transient(self) -> None:
        # Docker emits the HTTP reason phrase verbatim; standard RFC 7231 value is "Gateway Timeout"
        assert self._check("received unexpected HTTP status: 504 Gateway Timeout")

    def test_context_deadline_exceeded_is_transient(self) -> None:
        assert self._check("context deadline exceeded")

    def test_tls_handshake_timeout_is_transient(self) -> None:
        assert self._check("net/http: TLS handshake timeout")

    def test_429_is_transient(self) -> None:
        assert self._check("received unexpected HTTP status: 429 Too Many Requests")

    def test_connection_reset_by_peer_is_transient(self) -> None:
        assert self._check("read tcp: connection reset by peer")

    # --- Non-transient errors must NOT match ---

    def test_manifest_unknown_is_not_transient(self) -> None:
        """Genuine 'image not found' from registry must remain a permanent failure."""
        assert not self._check(
            'Error response from daemon: manifest for '
            'quay.io/oauth2-proxy/oauth2-proxy:vNONEXISTENT not found: '
            'manifest unknown: manifest unknown'
        )

    def test_no_such_manifest_is_not_transient(self) -> None:
        assert not self._check(
            "no such manifest: quay.io/example/image:v99.0.0"
        )

    def test_empty_string_is_not_transient(self) -> None:
        assert not self._check("")

    def test_unauthorized_is_not_transient(self) -> None:
        assert not self._check("received unexpected HTTP status: 401 Unauthorized")
