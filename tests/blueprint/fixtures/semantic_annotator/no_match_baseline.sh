#!/usr/bin/env bash
# Baseline: large structural content, no specific pattern

set -euo pipefail

_setup() {
    echo "setup"
}

_teardown() {
    echo "teardown"
}

_setup
_teardown
