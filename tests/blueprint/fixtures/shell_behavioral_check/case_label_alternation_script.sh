#!/usr/bin/env bash
# Fixture: script with case alternation labels (build|test style).
# Alternation tokens joined by "|" must NOT be flagged as unresolved symbols.

run_action() {
    local action="$1"
    case "$action" in
        build|test)
            echo "build or test"
            ;;
        deploy | verify)
            echo "deploy or verify"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

run_action "$1"
