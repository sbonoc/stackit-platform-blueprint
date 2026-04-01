#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/async_message_contracts.sh"

start_script_metric_trap "test_async_message_contracts_consumer"

async_message_contracts_run_lane consumer
