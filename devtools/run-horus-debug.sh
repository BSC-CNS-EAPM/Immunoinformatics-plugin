#!/usr/bin/env bash
set -euo pipefail

# Cluster environment
if command -v ml >/dev/null 2>&1; then
    ml Horus

    # Cleanup env variables that may interfere
    unset HORUS_DEV_PLUGINS_FOLDERS
fi

# Explicitly set the plugins directory and the env file
export HORUS_PLUGINS_DIR="HORUS_PLUGINS_DIR"
export ENV_FILE=".env"

# Prefer cluster executable if available
if command -v Horus >/dev/null 2>&1; then
    exec Horus -s -d --password horus_debug -dp
fi

# Fallback to local executable (ubuntu)
if command -v horus >/dev/null 2>&1; then
    exec horus -s -d --password horus_debug -dp
fi

# On macOS, use the App executable
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ -f "/Applications/Horus.app/Contents/MacOS/Horus" ]]; then
        exec "/Applications/Horus.app/Contents/MacOS/Horus" -s -d --password horus_debug -dp
    fi
fi

echo "Horus executable not found"
exit 1
