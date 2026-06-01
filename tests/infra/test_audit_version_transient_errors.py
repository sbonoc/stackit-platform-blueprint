"""Tests for is_transient_registry_error in scripts/bin/infra/audit_version.sh.

These tests guard against transient registry failures being misclassified as
permanent "image not found" failures.  The root cause of the CI regression:
quay.io dropped TCP/TLS connections during a partial outage; docker manifest
inspect returned an error containing "EOF" rather than a recognisable HTTP
5xx code; is_transient_registry_error returned false; the check was emitted
as a failure (status=missing) instead of a warning (status=unavailable).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_VERSION_SH = REPO_ROOT / "scripts/bin/infra/audit_version.sh"

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

    def test_eof_pattern_broad_enough_to_cover_unexpected_eof(self) -> None:
        """The eof pattern must be broad enough to match 'unexpected eof' strings.
        Previously a separate *'unexpected eof'* line existed; the consolidated *'eof'*
        pattern subsumes it — verify the extracted pattern contains 'eof'."""
        patterns = self._patterns_in_script()
        # The broad *"eof"* pattern subsumes space-prefix, colon-prefix, and unexpected-eof
        # variants; any pattern containing 'eof' satisfies this requirement.
        assert any("eof" in p for p in patterns), (
            "is_transient_registry_error must cover 'eof' broadly enough to match "
            "'unexpected eof', bare 'EOF', and URL-context '...EOF' strings"
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

    def test_eof_bare_string_only_is_transient(self) -> None:
        """Codex P5: docker can return exactly 'EOF' with no URL or context prefix.
        The earlier *' eof'* pattern (space required) missed this case; the
        consolidated *'eof'* pattern covers it."""
        assert self._check("EOF"), (
            "Bare 'EOF' response (no space or colon prefix) must be classified as transient"
        )

    def test_eof_with_url_context_is_transient(self) -> None:
        """Go http-client wraps io.EOF as 'Get \"URL\": EOF' — the most common form."""
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
