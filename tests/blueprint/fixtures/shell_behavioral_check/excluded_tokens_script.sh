#!/usr/bin/env bash
# Fixture: script calling tar, pnpm, and all 13 blueprint runtime functions.
# Every token here must appear in _EXCLUDED_TOKENS and produce zero findings.

setup_app() {
    tar -czf archive.tar.gz ./dist
    pnpm install

    blueprint_require_runtime_env
    blueprint_sanitize_init_placeholder_defaults
    ensure_file_from_template "src.tmpl" "dst"
    ensure_file_from_rendered_template "src.tmpl" "dst"
    postgres_init_env
    object_storage_init_env
    rabbitmq_seed_env_defaults
    public_endpoints_seed_env_defaults
    identity_aware_proxy_seed_env_defaults
    keycloak_seed_env_defaults
    render_optional_module_values_file "module"
    apply_optional_module_secret_from_literals "module"
    delete_optional_module_secret "module"
}

setup_app
