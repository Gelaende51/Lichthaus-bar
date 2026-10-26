#!/bin/sh
# Installs hauslicht-bar for the current user into ~/.local/bin (no root).
set -eu
src=$(cd "$(dirname "$0")" && pwd)
bin="$HOME/.local/bin"
command -v python3 >/dev/null 2>&1 || echo "warning: python3 not found" >&2
mkdir -p "$bin"
cp "$src/hauslicht-bar" "$bin/hauslicht-bar"
chmod 755 "$bin/hauslicht-bar"
echo "Installed: $bin/hauslicht-bar (add it to your bar, see README.md)."
case ":$PATH:" in *":$bin:"*) ;; *) echo "Note: $bin is not on PATH." ;; esac
