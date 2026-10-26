#!/bin/sh
# Removes what install.sh put into ~/.local/bin. Your bar's config stays.
set -eu
rm -f "$HOME/.local/bin/hauslicht-bar"
echo "Removed: $HOME/.local/bin/hauslicht-bar (remove the module from your bar's config)."
