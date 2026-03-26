#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "infra_help_reference"

usage() {
  cat <<'USAGE'
Usage: help_reference.sh [MAKEFILE...]

Prints full Make target and variable reference from Makefiles.
If no files are provided, defaults to the repository Makefile.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

makefiles=("$@")
if [[ "${#makefiles[@]}" -eq 0 ]]; then
  makefiles=("$ROOT_DIR/Makefile")
fi

resolved_makefiles=()
for makefile in "${makefiles[@]}"; do
  if [[ "$makefile" != /* ]]; then
    makefile="$ROOT_DIR/$makefile"
  fi
  if [[ ! -f "$makefile" ]]; then
    log_fatal "makefile not found: $makefile"
  fi
  resolved_makefiles+=("$makefile")
done

printf 'Usage: make <target>\n\n'
printf 'Targets\n'
awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-44s %s\n", $1, $2}' "${resolved_makefiles[@]}"

printf '\nVariables (?= defaults)\n'
awk '
  /^[A-Z0-9_]+[[:space:]]*\?=/ {
    name=$1
    sub(/[[:space:]]*\?=.*/, "", name)
    value=$0
    sub(/^[A-Z0-9_]+[[:space:]]*\?=[[:space:]]*/, "", value)
    if (!(name in seen)) {
      order[++count] = name
    }
    seen[name] = value
  }
  END {
    if (count == 0) {
      print "  (none)"
      exit
    }
    for (i = 1; i <= count; i++) {
      name = order[i]
      printf "  %s=%s\n", name, seen[name]
    }
  }
' "${resolved_makefiles[@]}"
