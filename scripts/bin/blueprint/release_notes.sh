#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_release_notes"

usage() {
  cat <<'EOF'
Usage: release_notes.sh [--output PATH] [--tag TAG]

Generates template release notes from contract/governance metadata.
EOF
}

output_path="$ROOT_DIR/artifacts/releases/template_release_notes.md"
release_tag="${GITHUB_REF_NAME:-}"

while (($#)); do
  case "$1" in
  --help)
    usage
    exit 0
    ;;
  --output)
    shift
    output_path="$1"
    ;;
  --tag)
    shift
    release_tag="$1"
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
  shift
done

require_command python3

run_cmd "$ROOT_DIR/scripts/lib/blueprint/generate_release_notes.py" \
  --contract "$ROOT_DIR/blueprint/contract.yaml" \
  --decisions "$ROOT_DIR/AGENTS.decisions.md" \
  --backlog "$ROOT_DIR/AGENTS.backlog.md" \
  --output "$output_path" \
  --tag "${release_tag:-}"

log_info "release notes generated at $output_path"
