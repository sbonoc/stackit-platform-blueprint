#!/usr/bin/env bash
set -euo pipefail

SCRIPT_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${ROOT_DIR:-$(cd "$SCRIPT_LIB_DIR/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/lib/quality/semver.sh"
