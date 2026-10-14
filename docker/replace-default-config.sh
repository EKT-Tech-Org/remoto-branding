#!/bin/sh
# Replaces `default_config:` with its items minus zeroconf, which announces the
# upstream product name on the LAN. Items the box already lists are not repeated.
# Runs once: afterwards there is no `default_config:` line left.
#
#   replace-default-config.sh <configuration.yaml> <item>...
set -e

CONF="$1"; shift
grep -q '^default_config:' "$CONF" || exit 0

cp "$CONF" "$CONF.before-remoto"
TMP="$CONF.remoto-tmp"
grep -v '^default_config:' "$CONF" > "$TMP" || true
printf '\n# Added by Remoto: default_config without zeroconf (original in configuration.yaml.before-remoto)\n' >> "$TMP"
for item in "$@"; do
  grep -q "^$item:" "$TMP" || printf '%s:\n' "$item" >> "$TMP"
done
# Write in place, so ownership and permissions stay as they were.
cat "$TMP" > "$CONF" && rm -f "$TMP"
echo "[remoto] replaced default_config (zeroconf off); backup: configuration.yaml.before-remoto"
