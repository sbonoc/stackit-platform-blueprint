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
    log_fatal \
      "pnpm version mismatch: docs/package.json requires pnpm@${required_version} but active pnpm is ${actual_version}." \
      "Align all three version sources to pnpm@${required_version}:" \
      "(1) docs/package.json#packageManager -- canonical pin enforced here;" \
      "(2) root package.json#packageManager -- auto-activated by corepack when pnpm install runs from repo root;" \
      "(3) CI corepack prepare pin -- set in your CI workflow corepack prepare step."
  fi
}

docs_pnpm_install() {
  docs_require_workspace
  _docs_assert_pnpm_version
  # The docs site is intentionally outside the frontend workspace package globs.
  # Force standalone install so CI clean runners do not skip docs dependencies.
  # --ignore-scripts: pnpm@11 requires interactive approval for packages that run
  # post-install build scripts (e.g. core-js). These polyfill-compilation scripts
  # are not needed at install time — Webpack/Docusaurus bundles the polyfills at
  # build time. Ignoring them avoids the interactive prompt in CI and local runs.
  run_cmd pnpm --dir "$DOCS_SITE_DIR" --ignore-workspace install --frozen-lockfile --ignore-scripts
}

docs_pnpm_build() {
  docs_require_workspace
  run_cmd pnpm --dir "$DOCS_SITE_DIR" --ignore-workspace run build
}

docs_pnpm_start() {
  docs_require_workspace
  run_cmd pnpm --dir "$DOCS_SITE_DIR" --ignore-workspace run start
}
