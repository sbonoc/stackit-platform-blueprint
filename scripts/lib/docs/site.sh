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

docs_pnpm_install() {
  docs_require_workspace
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
