#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_install_codex_skill"

usage() {
  cat <<'USAGE'
Usage: install_codex_skill.sh [--skill-name NAME] [--skills-dir PATH]

Install/sync a blueprint-bundled Codex skill into local Codex skills directory.

Environment variables:
  BLUEPRINT_CODEX_SKILL_NAME      Default: blueprint-consumer-upgrade
  BLUEPRINT_CODEX_SKILLS_DIR      Default: ${CODEX_HOME:-$HOME/.codex}/skills
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command cp
require_command mkdir
require_command mv
require_command rm
require_command mktemp

set_default_env BLUEPRINT_CODEX_SKILL_NAME "blueprint-consumer-upgrade"
set_default_env BLUEPRINT_CODEX_SKILLS_DIR "${CODEX_HOME:-$HOME/.codex}/skills"

skill_name="$BLUEPRINT_CODEX_SKILL_NAME"
skills_dir="$BLUEPRINT_CODEX_SKILLS_DIR"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --skill-name)
    [[ "$#" -ge 2 ]] || log_fatal "--skill-name requires a value"
    skill_name="$2"
    shift 2
    ;;
  --skills-dir)
    [[ "$#" -ge 2 ]] || log_fatal "--skills-dir requires a value"
    skills_dir="$2"
    shift 2
    ;;
  --help)
    usage
    exit 0
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
done

source_dir="$ROOT_DIR/.agents/skills/$skill_name"
target_dir="$skills_dir/$skill_name"

if [[ ! -d "$source_dir" ]]; then
  log_fatal "skill source not found: $source_dir"
fi
if [[ ! -f "$source_dir/SKILL.md" ]]; then
  log_fatal "skill source is missing SKILL.md: $source_dir"
fi

run_cmd mkdir -p "$skills_dir"

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

run_cmd cp -R "$source_dir" "$tmp_dir/$skill_name"
run_cmd rm -rf "$target_dir"
run_cmd mv "$tmp_dir/$skill_name" "$target_dir"

# Keep shell helpers executable for local operator convenience.
if [[ -d "$target_dir/scripts" ]]; then
  while IFS= read -r script_path; do
    run_cmd chmod +x "$script_path"
  done < <(find "$target_dir/scripts" -type f -name '*.sh' | LC_ALL=C sort)
fi

log_info "codex skill synchronized: $skill_name -> $target_dir"
log_metric "blueprint_codex_skill_sync_total" "1" "status=success skill=$skill_name"
