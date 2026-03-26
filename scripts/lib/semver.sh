#!/usr/bin/env bash
set -euo pipefail

is_semver() {
  local value="$1"
  [[ "$value" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

compare_semver_component() {
  local lhs="$1"
  local rhs="$2"
  local index="$3"
  local lhs_component rhs_component
  IFS='.' read -r -a lhs_parts <<<"$lhs"
  IFS='.' read -r -a rhs_parts <<<"$rhs"
  lhs_component="${lhs_parts[$index]}"
  rhs_component="${rhs_parts[$index]}"
  if ((lhs_component > rhs_component)); then
    echo 1
  elif ((lhs_component < rhs_component)); then
    echo -1
  else
    echo 0
  fi
}

classify_semver_drift() {
  local current="$1"
  local baseline="$2"

  if ! is_semver "$current" || ! is_semver "$baseline"; then
    echo "non-semver"
    return 0
  fi

  local major_cmp minor_cmp patch_cmp
  major_cmp="$(compare_semver_component "$current" "$baseline" 0)"
  minor_cmp="$(compare_semver_component "$current" "$baseline" 1)"
  patch_cmp="$(compare_semver_component "$current" "$baseline" 2)"

  if [[ "$major_cmp" != "0" ]]; then
    echo "major"
    return 0
  fi
  if [[ "$minor_cmp" != "0" ]]; then
    echo "minor"
    return 0
  fi
  if [[ "$patch_cmp" != "0" ]]; then
    echo "patch"
    return 0
  fi
  echo "same"
}
