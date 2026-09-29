#!/usr/bin/env bash
# Cloud sessions start from a fresh container: install the editing toolchain.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then exit 0; fi
"$CLAUDE_PROJECT_DIR/setup.sh"
