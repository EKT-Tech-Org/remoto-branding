#!/usr/bin/env bash
# One-time setup of a client box (Linux with Docker). Run ON the client box, as root:
#
#   T=<TOKEN>; curl -fsSL -H "Authorization: Bearer $T" -H "Accept: application/vnd.github.raw" \
#     https://api.github.com/repos/EKT-Tech-Org/remoto-branding/contents/deploy/client/setup.sh \
#     | bash -s -- "$T" [release] [folder]
#
# <TOKEN>: GitHub fine-grained token, this repo only, Contents: read-only. Ask the office.
# release: default is the latest tested release (see update.sh)
# folder:  install folder, default /opt/remoto
#
# Existing box already running a container named "homeassistant"? Its config
# folder is detected, backed up and reused, so automations, devices and history
# stay. Another container name: put HA_CONTAINER=<name> in front of `bash`.
#
# Testing: REMOTO_SOURCE=<repo checkout> installs from that folder instead of
# downloading, and then [release] is required.
set -euo pipefail

TOKEN="${1:?usage: setup.sh <TOKEN> [release] [folder]}"
RELEASE="${2:-}"
DIR="${3:-/opt/remoto}"
OLD="${HA_CONTAINER:-homeassistant}"
API="https://api.github.com/repos/EKT-Tech-Org/remoto-branding"

for tool in docker curl tar; do
  command -v "$tool" >/dev/null || { echo "$tool is not installed"; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "The Docker Compose plugin is not installed"; exit 1; }

mkdir -p "$DIR"
if [ -n "${REMOTO_SOURCE:-}" ]; then
  cp "$REMOTO_SOURCE/deploy/client/update.sh" "$DIR/update.sh"
else
  # Fetched before anything is touched: a wrong token stops here.
  curl -fsSL -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.raw" \
    "$API/contents/deploy/client/update.sh" -o "$DIR/update.sh" \
    || { echo "✗ Download failed (wrong token or no network). Nothing was changed."; exit 1; }
fi
chmod +x "$DIR/update.sh"
CONFIG_DIR="$DIR/config"

if docker inspect "$OLD" >/dev/null 2>&1; then
  EXISTING="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' "$OLD")"
  [ -n "$EXISTING" ] || { echo "Container $OLD has no /config folder on this box; cannot keep its data. Stopping."; exit 1; }
  CONFIG_DIR="$EXISTING"
  echo "→ existing installation found, keeping its config: $CONFIG_DIR"
  # A box that is already Remoto is backed up by update.sh instead.
  if ! grep -q '^REMOTO_RELEASE=' "$DIR/.env" 2>/dev/null; then
    # Give it time to write its data; a short timeout kills it mid-save.
    docker stop -t 120 "$OLD" >/dev/null
    BACKUP="$DIR/backups/before-remoto-$(date +%Y%m%d%H%M%S).tgz"
    if ! { mkdir -p "$DIR/backups" && tar -C "$(dirname "$CONFIG_DIR")" -czf "$BACKUP" "$(basename "$CONFIG_DIR")"; }; then
      echo "✗ Backup failed, nothing was changed. Starting the old installation again."
      docker start "$OLD" >/dev/null
      rm -f "$BACKUP" 2>/dev/null || true
      exit 1
    fi
    echo "→ backup written: $BACKUP"
  fi
elif OTHER="$(docker ps --format '{{.Names}} {{.Image}}' | grep -i 'home-assistant' | head -1)" && [ -n "$OTHER" ]; then
  echo "✗ Found a running installation under another name: $OTHER"
  echo "  Run again with HA_CONTAINER=${OTHER%% *} in front of bash, so its data is kept."
  exit 1
fi

mkdir -p "$CONFIG_DIR"
(umask 077 && printf '%s' "$TOKEN" > "$DIR/.token")
touch "$DIR/.env"
grep -v -e '^CONFIG_DIR=' -e '^TZ=' "$DIR/.env" > "$DIR/.env.tmp" || true
{
  echo "CONFIG_DIR=$CONFIG_DIR"
  echo "TZ=$(cat /etc/timezone 2>/dev/null || timedatectl show -p Timezone --value 2>/dev/null || echo Asia/Beirut)"
} >> "$DIR/.env.tmp"
mv "$DIR/.env.tmp" "$DIR/.env"

# Replace the stock container (its data stays in $CONFIG_DIR).
docker rm -f "$OLD" >/dev/null 2>&1 || true

"$DIR/update.sh" $RELEASE
IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
echo "  Open http://${IP:-<this box>}:8123"
echo "  Later updates: $DIR/update.sh"
