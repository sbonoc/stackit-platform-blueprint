#!/usr/bin/env bash
# Syntax-error fixture: intentional bash syntax error (unclosed function body).
set -euo pipefail

broken_func() {
    echo "this function is never closed"

broken_func
