#!/usr/bin/env bash
# Fixture: script with heredoc body.
# Words inside the heredoc (Run, Usage, DESCRIPTION) look like function-call
# tokens but must NOT be flagged as unresolved symbols.

show_usage() {
    cat <<'EOF'
Run this script to manage things.

Usage: script.sh [options]

DESCRIPTION: performs the requested operation and exits.
EOF
}

show_usage
