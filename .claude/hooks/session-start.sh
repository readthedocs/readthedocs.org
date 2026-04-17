#!/bin/bash
#
# SessionStart hook for Claude Code on the web.
#
# Prepares the environment so pre-commit linting works:
#   - Initializes the `common/` git submodule (the pre-commit config,
#     vale config, and CI configs are symlinked into it).
#   - Installs pre-commit and docutils (docutils provides rst2html,
#     which vale needs to lint RST files).
#   - Pre-warms pre-commit hook environments so the first run is fast.
#
# Idempotent: safe to run repeatedly.

set -euo pipefail

# Only run in Claude Code on the web. Local sessions already have a
# developer-managed environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

echo "[session-start] Initializing git submodules (common/)..."
git submodule update --init --recursive common

echo "[session-start] Installing pre-commit and docutils..."
pip install --quiet --user pre-commit docutils

# Make sure user-installed scripts are on PATH for this session.
USER_BIN="$(python3 -c 'import site; print(site.getuserbase() + "/bin")')"
if [ -d "$USER_BIN" ]; then
  echo "export PATH=\"$USER_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  export PATH="$USER_BIN:$PATH"
fi

echo "[session-start] Pre-warming pre-commit hook environments..."
pre-commit install-hooks

echo "[session-start] Done."
