#!/bin/sh
# Install the Remoto Branding integration into a config folder.
#
#   install-branding.sh <repo-dir> <config-dir>
#
# 1. Copies the integration (replacing older copies).
# 2. New box: writes a starter configuration.yaml.
#    Existing box: appends `remoto_branding:` once, so the integration sets itself up.
set -e

SRC="${1:?usage: install-branding.sh <repo-dir> <config-dir>}"
CONFIG="${2:?usage: install-branding.sh <repo-dir> <config-dir>}"
CONF_FILE="$CONFIG/configuration.yaml"

mkdir -p "$CONFIG/custom_components"
rm -rf "$CONFIG/custom_components/remoto_branding"
cp -r "$SRC/custom_components/remoto_branding" "$CONFIG/custom_components/remoto_branding"

if [ ! -f "$CONF_FILE" ]; then
  cp "$SRC/deploy/client/configuration.yaml" "$CONF_FILE"
  [ -f "$CONFIG/automations.yaml" ] || echo "[]" > "$CONFIG/automations.yaml"
  touch "$CONFIG/scripts.yaml" "$CONFIG/scenes.yaml"
  echo "[remoto] new box: starter configuration written"
elif ! grep -q '^remoto_branding:' "$CONF_FILE"; then
  printf '\n# Added by Remoto\nremoto_branding:\n' >> "$CONF_FILE"
  echo "[remoto] existing box: enabled remoto_branding in configuration.yaml"
fi

echo "[remoto] branding $(grep '"version"' "$SRC/custom_components/remoto_branding/manifest.json" | tr -dc '0-9.') installed"
