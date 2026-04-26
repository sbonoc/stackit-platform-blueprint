#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_prune_codex_skills"

usage() {
  cat <<'USAGE'
Usage: prune_codex_skills.sh [--skills-dir PATH]

Remove stale blueprint-* skills from the local Codex skills directory.

A skill is considered stale when it is installed under the skills directory
but no longer present in .agents/skills/ or the consumer template fallback
path within this repository.

Environment variables:
  BLUEPRINT_CODEX_SKILLS_DIR      Default: ${CODEX_HOME:-$HOME/.codex}/skills
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env BLUEPRINT_CODEX_SKILLS_DIR "${CODEX_HOME:-$HOME/.codex}/skills"

skills_dir="$BLUEPRINT_CODEX_SKILLS_DIR"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
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

# ---------------------------------------------------------------------------
# Derive the canonical set of blueprint skill names from the repo sources,
# mirroring the resolution order used by install_codex_skill.sh.
# ---------------------------------------------------------------------------
declare -A known_skills

_index_skills_in_dir() {
  local base_dir="$1"
  [[ -d "$base_dir" ]] || return 0
  while IFS= read -r skill_dir; do
    local name
    name="$(basename "$skill_dir")"
    known_skills["$name"]=1
  done < <(find "$base_dir" -maxdepth 1 -mindepth 1 -type d -name "blueprint-*" | LC_ALL=C sort)
}

_index_skills_in_dir "$ROOT_DIR/.agents/skills"
_index_skills_in_dir "$ROOT_DIR/scripts/templates/consumer/init/.agents/skills"

if [[ "${#known_skills[@]}" -eq 0 ]]; then
  log_info "prune-codex-skills: no blueprint skills found in repo sources — nothing to prune against"
  log_metric "blueprint_codex_skill_prune_total" "1" "status=skip"
  exit 0
fi

# ---------------------------------------------------------------------------
# Scan installed skills and remove any that are no longer in the known set.
# ---------------------------------------------------------------------------
pruned=0

if [[ ! -d "$skills_dir" ]]; then
  log_info "prune-codex-skills: skills directory does not exist — nothing to prune"
  log_metric "blueprint_codex_skill_prune_total" "1" "status=skip"
  exit 0
fi

while IFS= read -r installed_dir; do
  installed_name="$(basename "$installed_dir")"
  if [[ -z "${known_skills[$installed_name]+_}" ]]; then
    log_info "prune-codex-skills: removing stale skill: $installed_name"
    run_cmd rm -rf "$installed_dir"
    pruned=$((pruned + 1))
  fi
done < <(find "$skills_dir" -maxdepth 1 -mindepth 1 -type d -name "blueprint-*" | LC_ALL=C sort)

if [[ "$pruned" -gt 0 ]]; then
  log_info "prune-codex-skills: pruned ${pruned} stale skill(s)"
else
  log_info "prune-codex-skills: no stale skills found"
fi

log_metric "blueprint_codex_skill_prune_total" "1" "status=success pruned=${pruned}"
