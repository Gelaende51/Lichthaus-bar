#!/bin/sh
# Removes what install.sh put into ~/.local/bin. Your bar's config stays.
set -eu
rm -f "$HOME/.local/bin/lichthaus-bar"
echo "Removed: $HOME/.local/bin/lichthaus-bar (remove the module from your bar's config)."
