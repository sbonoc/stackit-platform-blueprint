#!/usr/bin/env bash

_root_dir_abs_dir() {
  local dir="$1"
  (
    cd "$dir" >/dev/null 2>&1
    pwd
  )
}

_root_dir_has_markers() {
  local candidate="$1"
  [[ -d "$candidate" ]] || return 1
  [[ -f "$candidate/Makefile" ]] || return 1
  [[ -d "$candidate/scripts/lib" ]] || return 1
}

_root_dir_validate_candidate() {
  local raw_candidate="$1"
  [[ -n "$raw_candidate" ]] || return 1
  local candidate
  candidate="$(_root_dir_abs_dir "$raw_candidate")" || return 1
  _root_dir_has_markers "$candidate" || return 1
  printf '%s\n' "$candidate"
  return 0
}

_root_dir_from_git() {
  local start_dir="$1"
  command -v git >/dev/null 2>&1 || return 1
  git -C "$start_dir" rev-parse --show-toplevel 2>/dev/null
}

_root_dir_from_marker_walkup() {
  local start_dir="$1"
  local current
  current="$(_root_dir_abs_dir "$start_dir")" || return 1
  while true; do
    if _root_dir_has_markers "$current"; then
      printf '%s\n' "$current"
      return 0
    fi
    local parent
    parent="$(dirname "$current")"
    if [[ "$parent" == "$current" ]]; then
      break
    fi
    current="$parent"
  done
  return 1
}

resolve_root_dir() {
  local start_dir="${1:-$PWD}"
  local candidate

  if [[ -n "${ROOT_DIR:-}" ]]; then
    if candidate="$(_root_dir_validate_candidate "$ROOT_DIR")"; then
      printf '%s\n' "$candidate"
      return 0
    fi
    echo "ROOT_DIR is set but invalid (expected Makefile and scripts/lib): $ROOT_DIR" >&2
  fi

  if candidate="$(_root_dir_from_git "$start_dir")" && candidate="$(_root_dir_validate_candidate "$candidate")"; then
    printf '%s\n' "$candidate"
    return 0
  fi

  if candidate="$(_root_dir_from_marker_walkup "$start_dir")"; then
    printf '%s\n' "$candidate"
    return 0
  fi

  echo "unable to resolve repository root from start_dir=$start_dir" >&2
  echo "checked ROOT_DIR env, git root, and marker walk-up (Makefile + scripts/lib)" >&2
  return 1
}
