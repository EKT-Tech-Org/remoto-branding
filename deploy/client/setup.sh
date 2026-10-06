#!/usr/bin/env bash
# One-time setup of a client box (Linux with Docker). Run ON the client box:
#
#   curl -fsSL -H "Authorization: token <TOKEN>" \
#     https://raw.githubusercontent.com/EKT-Tech-Org/remoto-branding/main/deploy/client/setup.sh \
#     | bash -s -- <TOKEN> [version] [folder]
#
# <TOKEN>: GitHub classic token with read:packages + repo (read). Ask the office.
# version: image tag, default "latest" (= the version we currently roll out)
# folder:  install folder, default /opt/remoto
#
# Existing box already running a container named "homeassistant"? Its config
# folder is detected and reused, so automations, devices and history stay.
set -euo pipefail

TOKEN="${1:?usage: setup.sh <TOKEN> [version] [folder]}"
VERSION="${2:-latest}"
DIR="${3:-/opt/remoto}"
RAW=https://raw.githubusercontent.com/EKT-Tech-Org/remoto-branding/main/deploy/client

command -v docker >/dev/null || { echo "Docker is not installed"; exit 1; }

echo "→ logging in to the Remoto image registry"
echo "$TOKEN" | docker login ghcr.io -u remoto --password-stdin >/dev/null

# Reuse the config folder of an existing container, if there is one.
CONFIG_DIR="$DIR/config"
if docker inspect homeassistant >/dev/null 2>&1; then
  EXISTING="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}' homeassistant)"
  if [ -n "$EXISTING" ]; then
    CONFIG_DIR="$EXISTING"
    echo "→ existing installation found, keeping its config: $CONFIG_DIR"
    tar -C "$(dirname "$CONFIG_DIR")" -czf "$DIR-config-backup-$(date +%Y%m%d%H%M).tgz" "$(basename "$CONFIG_DIR")" 2>/dev/null \
      && echo "→ backup written next to $DIR" || true
  fi
fi

mkdir -p "$DIR" "$CONFIG_DIR"
curl -fsSL -H "Authorization: token $TOKEN" "$RAW/docker-compose.yml" -o "$DIR/docker-compose.yml"
cat > "$DIR/.env" <<ENV
REMOTO_VERSION=$VERSION
CONFIG_DIR=$CONFIG_DIR
TZ=$(cat /etc/timezone 2>/dev/null || echo Asia/Beirut)
ENV

# Replace the stock container (its data stays in $CONFIG_DIR).
docker rm -f homeassistant >/dev/null 2>&1 || true

cd "$DIR"
docker compose pull
docker compose up -d
echo "✓ Remoto $VERSION running. Open http://$(hostname -I 2>/dev/null | awk '{print $1}'):8123"
