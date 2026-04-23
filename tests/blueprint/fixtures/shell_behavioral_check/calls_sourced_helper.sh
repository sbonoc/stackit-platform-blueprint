#!/usr/bin/env bash
# Depth-1 source fixture: helper_function is defined in sourced_helper.sh
# and called here. Gate must resolve depth-1 source and pass.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/sourced_helper.sh"

helper_function
