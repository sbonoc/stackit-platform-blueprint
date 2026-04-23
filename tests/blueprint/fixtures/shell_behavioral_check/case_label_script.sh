#!/usr/bin/env bash
# Fixture: script with case statement.
# Case labels like postcheck_status) and postcheck_report) look like function
# calls but must NOT be flagged as unresolved symbols.

handle_subcommand() {
    local cmd="$1"
    case "$cmd" in
        postcheck_status)
            echo "status"
            ;;
        postcheck_report)
            echo "report"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

handle_subcommand "$1"
