#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_resolve.sh [--dry-run] [--accept-source ALL] [--accept-target ALL] [--interactive]

Apply blueprint upgrade conflict resolutions from artifacts/blueprint/upgrade_triage.json.

Environment variables:
  INTERACTIVE    Set to true to prompt for each human_required row.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3

exec uv run python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_consumer_resolve.py" "$@"
