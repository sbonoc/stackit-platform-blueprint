#!/usr/bin/env bash
set -euo pipefail

DOCS_SITE_DIR="${DOCS_SITE_DIR:-$ROOT_DIR/docs}"

docs_require_workspace() {
  require_command pnpm
  if [[ ! -d "$DOCS_SITE_DIR" ]]; then
    log_fatal "docs site directory not found: $DOCS_SITE_DIR"
  fi
  if [[ ! -f "$DOCS_SITE_DIR/package.json" ]]; then
    log_fatal "docs site package.json not found: $DOCS_SITE_DIR/package.json"
  fi
  if [[ ! -f "$DOCS_SITE_DIR/docusaurus.config.js" ]]; then
    log_fatal "docusaurus config not found: $DOCS_SITE_DIR/docusaurus.config.js"
  fi
  if [[ ! -f "$DOCS_SITE_DIR/sidebars.js" ]]; then
    log_fatal "docusaurus sidebars not found: $DOCS_SITE_DIR/sidebars.js"
  fi
}

_docs_assert_pnpm_version() {
  local required_version actual_version
  # Extract the semver from e.g. "pnpm@10.32.1" — strip the "pnpm@" prefix.
  required_version="$(python3 -c "import json,sys; d=json.load(open('$DOCS_SITE_DIR/package.json')); print(d.get('packageManager','').lstrip('pnpm@'))")"
  actual_version="$(pnpm --version)"
  if [[ -n "$required_version" && "$actual_version" != "$required_version" ]]; then
    log_fatal "pnpm version mismatch: docs/package.json requires pnpm@${required_version} but active pnpm is ${actual_version}. Update the local pnpm installation or the CI action's corepack prepare pin."
  fi
}

docs_pnpm_install() {
  docs_require_workspace
  _docs_assert_pnpm_version
  run_cmd pnpm --dir "$DOCS_SITE_DIR" install --frozen-lockfile
}

docs_pnpm_build() {
  docs_require_workspace
  run_cmd pnpm --dir "$DOCS_SITE_DIR" run build
}

docs_pnpm_start() {
  docs_require_workspace
  run_cmd pnpm --dir "$DOCS_SITE_DIR" run start
}
