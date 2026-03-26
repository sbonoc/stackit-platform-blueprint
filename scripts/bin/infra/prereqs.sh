#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_prereqs"

usage() {
  cat <<'USAGE'
Usage: prereqs.sh

Verifies local prerequisites and optionally auto-installs missing tools.

Environment variables:
  PREREQS_AUTO_INSTALL           true|false (default: false)
  PREREQS_INSTALL_OPTIONAL       true|false (default: false)
  PREREQS_REQUIRE_STACKIT_TOOLS  true|false (default: false)

Canonical required tools:
  bash git make python3 pre-commit shellcheck

STACKIT/operator tools (optional by default):
  terraform kubectl helm docker kind uv gh jq pnpm
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

normalize_bool() {
  local value="${1:-false}"
  case "$value" in
  1 | true | TRUE | True | yes | YES | on | ON)
    echo "true"
    ;;
  *)
    echo "false"
    ;;
  esac
}

set_default_env PREREQS_AUTO_INSTALL "false"
set_default_env PREREQS_INSTALL_OPTIONAL "false"
set_default_env PREREQS_REQUIRE_STACKIT_TOOLS "false"

PREREQS_AUTO_INSTALL="$(normalize_bool "$PREREQS_AUTO_INSTALL")"
PREREQS_INSTALL_OPTIONAL="$(normalize_bool "$PREREQS_INSTALL_OPTIONAL")"
PREREQS_REQUIRE_STACKIT_TOOLS="$(normalize_bool "$PREREQS_REQUIRE_STACKIT_TOOLS")"

bool_to_metric() {
  if [[ "$1" == "true" ]]; then
    echo "1"
    return 0
  fi
  echo "0"
}

detect_platform() {
  case "$(uname -s)" in
  Darwin)
    echo "darwin"
    ;;
  Linux)
    echo "linux"
    ;;
  *)
    echo "unknown"
    ;;
  esac
}

install_with_brew() {
  local formula="$1"
  if ! command -v brew >/dev/null 2>&1; then
    log_warn "brew not found; cannot auto-install $formula"
    return 1
  fi
  run_cmd brew install "$formula"
}

install_with_brew_cask() {
  local cask="$1"
  if ! command -v brew >/dev/null 2>&1; then
    log_warn "brew not found; cannot auto-install cask $cask"
    return 1
  fi
  run_cmd brew install --cask "$cask"
}

install_with_apt() {
  local package="$1"
  if ! command -v apt-get >/dev/null 2>&1; then
    log_warn "apt-get not found; cannot auto-install $package"
    return 1
  fi

  if [[ "$(id -u)" -eq 0 ]]; then
    run_cmd apt-get update
    run_cmd apt-get install -y "$package"
    return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    run_cmd sudo apt-get update
    run_cmd sudo apt-get install -y "$package"
    return 0
  fi

  log_warn "sudo not available; cannot auto-install $package"
  return 1
}

install_pre_commit() {
  if command -v pre-commit >/dev/null 2>&1; then
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    log_warn "python3 not found; cannot auto-install pre-commit"
    return 1
  fi
  run_cmd python3 -m pip install --user pre-commit
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  if ! command -v curl >/dev/null 2>&1; then
    log_warn "curl not found; cannot auto-install uv"
    return 1
  fi
  # Official uv installer is the most portable way across Linux/macOS.
  run_cmd sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
}

install_tool() {
  local tool="$1"
  local platform="$2"

  case "$tool" in
  pre-commit)
    install_pre_commit
    return $?
    ;;
  uv)
    install_uv
    return $?
    ;;
  esac

  if [[ "$platform" == "darwin" ]]; then
    case "$tool" in
    python3)
      install_with_brew "python"
      ;;
    shellcheck | kubectl | helm | kind | gh | jq | pnpm)
      install_with_brew "$tool"
      ;;
    terraform)
      if command -v brew >/dev/null 2>&1; then
        run_cmd brew tap hashicorp/tap
        run_cmd brew install hashicorp/tap/terraform
      else
        log_warn "brew not found; cannot auto-install terraform"
        return 1
      fi
      ;;
    docker)
      install_with_brew_cask "docker"
      ;;
    *)
      log_warn "no darwin auto-install strategy for tool=$tool"
      return 1
      ;;
    esac
    return $?
  fi

  if [[ "$platform" == "linux" ]]; then
    case "$tool" in
    python3)
      install_with_apt "python3"
      ;;
    shellcheck)
      install_with_apt "shellcheck"
      ;;
    jq)
      install_with_apt "jq"
      ;;
    docker)
      install_with_apt "docker.io"
      ;;
    pnpm)
      if command -v npm >/dev/null 2>&1; then
        run_cmd npm install -g pnpm
      else
        log_warn "npm not found; cannot auto-install pnpm"
        return 1
      fi
      ;;
    *)
      log_warn "no linux auto-install strategy for tool=$tool"
      return 1
      ;;
    esac
    return $?
  fi

  log_warn "unsupported platform for auto-install: $platform"
  return 1
}

check_or_install() {
  local tool="$1"
  local platform="$2"
  local bucket="$3"
  if command -v "$tool" >/dev/null 2>&1; then
    log_info "found prerequisite: $tool"
    return 0
  fi

  log_warn "missing prerequisite: $tool"
  if [[ "$PREREQS_AUTO_INSTALL" == "true" ]]; then
    if install_tool "$tool" "$platform"; then
      if command -v "$tool" >/dev/null 2>&1; then
        log_info "installed prerequisite: $tool"
        return 0
      fi
    fi
    log_warn "auto-install attempted but still missing: $tool"
  fi

  if [[ "$bucket" == "required" ]]; then
    missing_required+=("$tool")
  else
    missing_optional+=("$tool")
  fi
}

platform="$(detect_platform)"
required_tools=(bash git make python3 pre-commit shellcheck)
stackit_tools=(terraform kubectl helm docker kind uv gh jq pnpm)
missing_required=()
missing_optional=()

for tool in "${required_tools[@]}"; do
  check_or_install "$tool" "$platform" "required"
done

for tool in "${stackit_tools[@]}"; do
  if [[ "$PREREQS_REQUIRE_STACKIT_TOOLS" == "true" ]]; then
    check_or_install "$tool" "$platform" "required"
  elif [[ "$PREREQS_INSTALL_OPTIONAL" == "true" || "$PREREQS_AUTO_INSTALL" == "true" ]]; then
    check_or_install "$tool" "$platform" "optional"
  else
    if command -v "$tool" >/dev/null 2>&1; then
      log_info "found optional STACKIT tool: $tool"
    else
      missing_optional+=("$tool")
    fi
  fi
done

log_metric "infra_prereqs_missing_required_count" "${#missing_required[@]}"
log_metric "infra_prereqs_missing_optional_count" "${#missing_optional[@]}"
log_metric "infra_prereqs_auto_install_enabled" "$(bool_to_metric "$PREREQS_AUTO_INSTALL")"
log_metric "infra_prereqs_require_stackit_tools_enabled" "$(bool_to_metric "$PREREQS_REQUIRE_STACKIT_TOOLS")"

state_file="$(
  write_state_file "infra_prereqs" \
    "platform=$platform" \
    "auto_install=$PREREQS_AUTO_INSTALL" \
    "install_optional=$PREREQS_INSTALL_OPTIONAL" \
    "require_stackit_tools=$PREREQS_REQUIRE_STACKIT_TOOLS" \
    "missing_required=$(IFS=,; echo "${missing_required[*]-}")" \
    "missing_optional=$(IFS=,; echo "${missing_optional[*]-}")" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra prereqs state written to $state_file"
log_info "infra prereqs completed platform=$platform required_missing=${#missing_required[@]} optional_missing=${#missing_optional[@]}"

if [[ "${#missing_optional[@]}" -gt 0 ]]; then
  log_warn "optional STACKIT tools missing: $(IFS=,; echo "${missing_optional[*]-}")"
fi

if [[ "${#missing_required[@]}" -gt 0 ]]; then
  log_fatal "missing required prerequisites: $(IFS=,; echo "${missing_required[*]-}")"
fi

log_info "infra prerequisites check passed"
