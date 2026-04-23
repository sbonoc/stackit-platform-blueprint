#!/usr/bin/env bash
# Negative-path fixture: call site present but function definition was dropped
# by a 3-way merge. setup_environment is called but never defined.
set -euo pipefail

setup_environment
