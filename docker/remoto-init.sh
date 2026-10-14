#!/bin/sh
# Runs at every container start, before the main service.
# 1. Installs the bundled Remoto Branding integration (replacing older copies).
# 2. New box: writes a starter configuration.yaml.
#    Existing box: swaps `default_config:` for the same list minus zeroconf, and
#    appends `remoto_branding:` once, so the integration sets itself up.
set -e

SRC=/opt/remoto
CONFIG=/config
CONF_FILE="$CONFIG/configuration.yaml"

mkdir -p "$CONFIG/custom_components"
rm -rf "$CONFIG/custom_components/remoto_branding"
cp -r "$SRC/remoto_branding" "$CONFIG/custom_components/remoto_branding"

if [ ! -f "$CONF_FILE" ]; then
  cp "$SRC/configuration.yaml" "$CONF_FILE"
  [ -f "$CONFIG/automations.yaml" ] || echo "[]" > "$CONFIG/automations.yaml"
  touch "$CONFIG/scripts.yaml" "$CONFIG/scenes.yaml"
  echo "[remoto] new box: starter configuration written"
else
  # shellcheck disable=SC2046 # one word per item
  "$SRC/replace-default-config.sh" "$CONF_FILE" $(awk '/^# <<< default_config/{f=0} f&&/^[a-z0-9_]+:/{sub(":.*","");print} /^# >>> default_config/{f=1}' "$SRC/configuration.yaml")
  if ! grep -q '^remoto_branding:' "$CONF_FILE"; then
    printf '\n# Added by Remoto\nremoto_branding:\n' >> "$CONF_FILE"
    echo "[remoto] existing box: enabled remoto_branding in configuration.yaml"
  fi
fi

echo "[remoto] branding $(grep '"version"' "$SRC/remoto_branding/manifest.json" | tr -dc '0-9.') installed"
