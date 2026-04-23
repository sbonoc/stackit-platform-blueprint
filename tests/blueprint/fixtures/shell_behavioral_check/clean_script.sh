#!/usr/bin/env bash
# Positive-path fixture: function defined and called in same file.
set -euo pipefail

do_work() {
    echo "doing work"
}

do_work
