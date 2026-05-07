#!/usr/bin/env bash
# quality_gating.sh — path-gate and phase-gate helpers for quality hooks
# Requires: logging.sh and exec.sh sourced in calling environment

# Default gating set for infra checks (newline-separated)
_QG_INFRA_GATE_PATHS="infra/
blueprint/contract.yaml
scripts/lib/blueprint/
scripts/bin/blueprint/
scripts/templates/blueprint/
make/
apps/
pyproject.toml
requirements"  # prefix match for requirements*.txt

_quality_changed_paths() {
  # Union of merge-base diff and working-tree diff.
  # Returns 1 when git is unavailable or merge-base resolution fails (caller must fail-safe).
  local main_branch="${QUALITY_HOOKS_MAIN_BRANCH:-main}"
  local merge_base
  merge_base="$(git merge-base HEAD "$main_branch" 2>/dev/null)" || return 1
  {
    git diff --name-only "$merge_base" HEAD 2>/dev/null || true
    git diff --name-only 2>/dev/null || true
  } | sort -u
}

quality_paths_match_infra_gate() {
  # Returns 0 if any path in $1 (newline-separated) matches the gating set
  # $1: optional newline-separated path list; if empty string or absent, reads from git
  local paths="${1:-}"
  if [[ -z "$paths" ]]; then
    # FR-011 fail-safe: if git is unavailable or merge-base fails, run infra checks
    paths="$(_quality_changed_paths)" || return 0
  fi
  if [[ "${QUALITY_HOOKS_FORCE_FULL:-}" == "true" ]]; then
    return 0
  fi
  local path
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    local gate
    while IFS= read -r gate; do
      [[ -z "$gate" ]] && continue
      if [[ "$path" == "$gate"* ]]; then
        return 0
      fi
    done <<< "$_QG_INFRA_GATE_PATHS"
  done <<< "$paths"
  return 1
}

quality_spec_is_ready() {
  local spec_dir="${1:-}"
  if [[ -z "$spec_dir" || ! -f "$spec_dir/spec.md" ]]; then
    return 1
  fi
  grep -qE '^- SPEC_READY: true[[:space:]]*$' "$spec_dir/spec.md"
}
