#!/usr/bin/env bash
# Source: same functions, restructured body — no pattern match

set -euo pipefail

_setup() {
    echo "setup v2"
    echo "extra step"
}

_teardown() {
    echo "teardown v2"
}

_setup
_teardown
