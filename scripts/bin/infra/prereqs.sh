#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
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

Canonical required Python modules:
  pytest

STACKIT/operator tools (optional by default):
  terraform kubectl helm docker kind uv gh jq pnpm kustomize nc
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

LOCAL_BIN="${HOME}/.local/bin"
export PATH="${LOCAL_BIN}:${PATH}"

set_default_env PREREQS_AUTO_INSTALL "false"
set_default_env PREREQS_INSTALL_OPTIONAL "false"
set_default_env PREREQS_REQUIRE_STACKIT_TOOLS "false"

PREREQS_AUTO_INSTALL="$(shell_normalize_bool_truefalse "$PREREQS_AUTO_INSTALL")"
PREREQS_INSTALL_OPTIONAL="$(shell_normalize_bool_truefalse "$PREREQS_INSTALL_OPTIONAL")"
PREREQS_REQUIRE_STACKIT_TOOLS="$(shell_normalize_bool_truefalse "$PREREQS_REQUIRE_STACKIT_TOOLS")"

bool_to_metric() {
  shell_normalize_bool_10 "$1"
}

download_file() {
  local url="$1"
  local out="$2"
  require_command curl
  run_cmd curl -fsSL --retry 3 --retry-delay 2 "$url" -o "$out"
}

ensure_local_bin() {
  mkdir -p "$LOCAL_BIN"
}

install_with_brew() {
  local formula="$1"
  if ! shell_has_cmd brew; then
    log_warn "brew not found; cannot auto-install $formula"
    return 1
  fi
  run_cmd brew install "$formula"
}

install_with_brew_cask() {
  local cask="$1"
  if ! shell_has_cmd brew; then
    log_warn "brew not found; cannot auto-install cask $cask"
    return 1
  fi
  run_cmd brew install --cask "$cask"
}

install_with_apt() {
  local package="$1"
  if ! shell_has_cmd apt-get; then
    log_warn "apt-get not found; cannot auto-install $package"
    return 1
  fi
  if [[ "$(id -u)" -eq 0 ]]; then
    run_cmd apt-get update
    run_cmd apt-get install -y "$package"
    return 0
  fi
  if shell_has_cmd sudo; then
    run_cmd sudo apt-get update
    run_cmd sudo apt-get install -y "$package"
    return 0
  fi
  log_warn "sudo not available; cannot auto-install $package"
  return 1
}

install_pre_commit() {
  if shell_has_cmd pre-commit; then
    return 0
  fi
  if ! shell_has_cmd python3; then
    log_warn "python3 not found; cannot auto-install pre-commit"
    return 1
  fi
  run_cmd python3 -m pip install --user pre-commit
}

install_uv() {
  if shell_has_cmd uv; then
    return 0
  fi
  require_command curl
  run_cmd sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
}

install_kubectl_linux() {
  local version tmp
  version="$(curl -fsSL https://dl.k8s.io/release/stable.txt)"
  tmp="$(mktemp)"
  ensure_local_bin
  download_file "https://dl.k8s.io/release/${version}/bin/linux/${ARCH}/kubectl" "$tmp"
  chmod +x "$tmp"
  install -m 0755 "$tmp" "$LOCAL_BIN/kubectl"
  rm -f "$tmp"
}

install_kind_linux() {
  local version tmp
  version="$(curl -fsSL https://api.github.com/repos/kubernetes-sigs/kind/releases/latest | sed -n 's/.*"tag_name": "\(v[^"]*\)".*/\1/p' | head -n 1)"
  [[ -n "$version" ]] || return 1
  tmp="$(mktemp)"
  ensure_local_bin
  download_file "https://kind.sigs.k8s.io/dl/${version}/kind-linux-${ARCH}" "$tmp"
  chmod +x "$tmp"
  install -m 0755 "$tmp" "$LOCAL_BIN/kind"
  rm -f "$tmp"
}

install_helm_linux() {
  local version tarball tmp_dir
  version="$(curl -fsSL https://api.github.com/repos/helm/helm/releases/latest | sed -n 's/.*"tag_name": "\(v[^"]*\)".*/\1/p' | head -n 1)"
  [[ -n "$version" ]] || return 1
  tarball="$(mktemp)"
  tmp_dir="$(mktemp -d)"
  ensure_local_bin
  download_file "https://get.helm.sh/helm-${version}-linux-${ARCH}.tar.gz" "$tarball"
  tar -xzf "$tarball" -C "$tmp_dir"
  install -m 0755 "$tmp_dir/linux-${ARCH}/helm" "$LOCAL_BIN/helm"
  rm -rf "$tmp_dir" "$tarball"
}

install_terraform_linux() {
  local version zipball tmp_dir
  version="${TERRAFORM_VERSION:-1.12.2}"
  zipball="$(mktemp)"
  tmp_dir="$(mktemp -d)"
  ensure_local_bin
  download_file "https://releases.hashicorp.com/terraform/${version}/terraform_${version}_linux_${ARCH}.zip" "$zipball"
  python3 - <<'PY' "$zipball" "$tmp_dir"
import pathlib
import sys
import zipfile

archive = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(archive) as zf:
    zf.extractall(destination)
PY
  install -m 0755 "$tmp_dir/terraform" "$LOCAL_BIN/terraform"
  rm -rf "$tmp_dir" "$zipball"
}

install_kustomize_linux() {
  local version tarball tmp_dir
  version="${KUSTOMIZE_VERSION:-v5.7.1}"
  tarball="$(mktemp)"
  tmp_dir="$(mktemp -d)"
  ensure_local_bin
  download_file "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${version}/kustomize_${version#v}_linux_${ARCH}.tar.gz" "$tarball"
  tar -xzf "$tarball" -C "$tmp_dir"
  install -m 0755 "$tmp_dir/kustomize" "$LOCAL_BIN/kustomize"
  rm -rf "$tmp_dir" "$tarball"
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
    shellcheck | kubectl | helm | kind | gh | jq | pnpm | kustomize)
      install_with_brew "$tool"
      ;;
    terraform)
      if shell_has_cmd brew; then
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
    nc)
      install_with_brew "netcat"
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
    nc)
      install_with_apt "netcat-openbsd"
      ;;
    pnpm)
      if shell_has_cmd npm; then
        run_cmd npm install -g pnpm
      else
        log_warn "npm not found; cannot auto-install pnpm"
        return 1
      fi
      ;;
    kubectl)
      install_kubectl_linux
      ;;
    helm)
      install_helm_linux
      ;;
    kind)
      install_kind_linux
      ;;
    terraform)
      install_terraform_linux
      ;;
    kustomize)
      install_kustomize_linux
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
  if shell_has_cmd "$tool"; then
    log_info "found prerequisite: $tool"
    return 0
  fi

  log_warn "missing prerequisite: $tool"
  if [[ "$PREREQS_AUTO_INSTALL" == "true" ]]; then
    if install_tool "$tool" "$platform"; then
      if shell_has_cmd "$tool"; then
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

python_module_available() {
  local module="$1"
  python3 - "$module" <<'PY'
import importlib.util
import sys

sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)
PY
}

install_python_module() {
  local module="$1"
  if ! python3 -m pip --version >/dev/null 2>&1; then
    run_cmd python3 -m ensurepip --upgrade
  fi
  run_cmd python3 -m pip install --user "$module"
}

check_or_install_python_module() {
  local module="$1"
  local bucket="$2"
  local label="python-module:${module}"

  if ! shell_has_cmd python3; then
    log_warn "cannot verify required python module because python3 is missing: $module"
    if [[ "$bucket" == "required" ]]; then
      missing_required+=("$label")
    else
      missing_optional+=("$label")
    fi
    return 1
  fi

  if python_module_available "$module"; then
    log_info "found required python module: $module"
    return 0
  fi

  log_warn "missing required python module: $module"
  if [[ "$PREREQS_AUTO_INSTALL" == "true" ]]; then
    if install_python_module "$module" && python_module_available "$module"; then
      log_info "installed required python module: $module"
      return 0
    fi
    log_warn "auto-install attempted but still missing required python module: $module"
  fi

  if [[ "$bucket" == "required" ]]; then
    missing_required+=("$label")
  else
    missing_optional+=("$label")
  fi
  return 1
}

platform="$(shell_detect_platform)"
ARCH="$(shell_detect_arch)"
required_tools=(bash git make python3 pre-commit shellcheck)
stackit_tools=(terraform kubectl helm docker kind uv gh jq pnpm kustomize nc)
missing_required=()
missing_optional=()

for tool in "${required_tools[@]}"; do
  check_or_install "$tool" "$platform" "required"
done

check_or_install_python_module "pytest" "required"

for tool in "${stackit_tools[@]}"; do
  if [[ "$PREREQS_REQUIRE_STACKIT_TOOLS" == "true" ]]; then
    check_or_install "$tool" "$platform" "required"
  elif [[ "$PREREQS_INSTALL_OPTIONAL" == "true" ]]; then
    check_or_install "$tool" "$platform" "optional"
  else
    if shell_has_cmd "$tool"; then
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
    "arch=$ARCH" \
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
