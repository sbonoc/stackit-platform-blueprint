"""Endpoint-level smoke tests for the local cluster.

These tests replace inferred curl assertions in pr_context.md with deterministic,
repeatable pytest cases. The port-forward lifecycle is managed in setUpClass /
tearDownClass so each test class owns its own session and cleanup is guaranteed.

Extension pattern
-----------------
When a work item touches HTTP routes, add a test method here (or a new subclass
for a different service). The method must be a positive-path assertion — verify
that the right response code and shape come back for a valid request. The AGENTS.md
local smoke gate accepts `make test-smoke-all-local` output as evidence.

Environment variables (all optional)
-------------------------------------
SMOKE_BACKEND_BASE_URL          Base URL for the backend API port-forward.
                                Default: http://localhost:18080
SMOKE_BACKEND_HEALTH_PATH       Path for the canonical health endpoint.
                                Default: /health
SMOKE_BACKEND_AUTH_GATE_PATH    Path of a protected endpoint to probe for 401/403.
                                Leave unset to skip the auth-gate assertion.
SMOKE_PF_WAIT_TIMEOUT           Seconds to wait for port-forward readiness.
                                Default: 30
"""

from __future__ import annotations

import http.client
import os
import unittest
import urllib.parse
import urllib.request
from typing import ClassVar

from tests._shared.helpers import REPO_ROOT, run_make


_BACKEND_BASE_URL = os.environ.get("SMOKE_BACKEND_BASE_URL", "http://localhost:18080")
_HEALTH_PATH = os.environ.get("SMOKE_BACKEND_HEALTH_PATH", "/health")
_AUTH_GATE_PATH = os.environ.get("SMOKE_BACKEND_AUTH_GATE_PATH", "")
_PF_WAIT_TIMEOUT = os.environ.get("SMOKE_PF_WAIT_TIMEOUT", "30")

_PF_NAME = "smoke-backend"
_PF_ENV = {
    "PF_NAME": _PF_NAME,
    "PF_NAMESPACE": "apps",
    "PF_RESOURCE": "svc/backend-api",
    "PF_LOCAL_PORT": "18080",
    "PF_REMOTE_PORT": "8080",
    "PF_WAIT_TIMEOUT": _PF_WAIT_TIMEOUT,
}


def _http_get(path: str, *, timeout: int = 10) -> http.client.HTTPResponse:
    """Issue a plain HTTP GET and return the response object.

    The response body is read so the connection can be reused.
    """
    parsed = urllib.parse.urlparse(_BACKEND_BASE_URL)
    conn = http.client.HTTPConnection(
        parsed.hostname or "localhost",
        parsed.port or 18080,
        timeout=timeout,
    )
    conn.request("GET", path)
    response = conn.getresponse()
    response.read()  # consume body so connection drains cleanly
    return response


class BackendApiSmokeTests(unittest.TestCase):
    """Endpoint-level smoke assertions for the backend API service.

    Requires a running local cluster with the backend-api service deployed.
    Run via: make test-smoke-all-local

    To run in isolation against an already-provisioned cluster:
        pytest tests/e2e/test_smoke_endpoints.py -v
    """

    _port_forward_started: ClassVar[bool] = False

    @classmethod
    def setUpClass(cls) -> None:
        result = run_make("infra-port-forward-start", _PF_ENV)
        if result.returncode != 0:
            raise AssertionError(
                f"Port-forward start failed — is the cluster running and backend-api deployed?\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        cls._port_forward_started = True

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._port_forward_started:
            run_make("infra-port-forward-stop", {"PF_NAME": _PF_NAME, "PF_FORCE_KILL": "true"})
            cls._port_forward_started = False

    # ------------------------------------------------------------------
    # Canonical health check (every blueprint-conformant backend must have this)
    # ------------------------------------------------------------------

    def test_health_endpoint_returns_2xx(self) -> None:
        """GET /health must return 2xx — the canonical readiness signal.

        This is the positive-path assertion that replaces the inferred
        `curl http://localhost:18080/health` in pr_context.md evidence tables.
        """
        response = _http_get(_HEALTH_PATH)
        self.assertIn(
            response.status,
            range(200, 300),
            f"GET {_HEALTH_PATH} returned {response.status}; "
            f"expected 2xx — is the backend-api pod ready?",
        )

    # ------------------------------------------------------------------
    # Auth gate (optional — enabled when SMOKE_BACKEND_AUTH_GATE_PATH is set)
    # ------------------------------------------------------------------

    def test_protected_endpoint_rejects_unauthenticated_request(self) -> None:
        """Protected endpoints must return 401 or 403 for unauthenticated GET requests.

        Set SMOKE_BACKEND_AUTH_GATE_PATH to a protected route to enable this assertion.
        The test is skipped when the env var is not set so it does not create noise
        for work items that do not touch auth-gated routes.
        """
        if not _AUTH_GATE_PATH:
            self.skipTest(
                "SMOKE_BACKEND_AUTH_GATE_PATH not set; skipping auth-gate assertion"
            )
        response = _http_get(_AUTH_GATE_PATH)
        self.assertIn(
            response.status,
            (401, 403),
            f"GET {_AUTH_GATE_PATH} returned {response.status}; "
            f"expected 401 or 403 for an unauthenticated request",
        )
