#!/usr/bin/env bash
# Fixture: script with multi-line array initialization.
# Bare-words inside array initializers must NOT be flagged as unresolved symbols.

configure_modules() {
    local modules=(
        observability
        postgres
        rabbitmq
    )
    local -a actions=(
        deploy
        validate
    )
    declare -a extras=(
        cleanup
        provision
    )
    echo "modules: ${modules[*]}"
}

configure_modules
