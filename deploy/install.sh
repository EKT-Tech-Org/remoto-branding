#!/usr/bin/env bash
# Install or update Remoto Branding over SSH, for boxes that don't run Docker
# themselves (HA OS). Docker boxes: use deploy/client/setup.sh instead.
#
#   deploy/install.sh <ssh-host> [config-dir] [restart-cmd]
#
# Docker (default):  deploy/install.sh user@client /opt/homeassistant/config "docker restart homeassistant"
# HA OS (SSH add-on): deploy/install.sh root@client /config "ha core restart"
set -euo pipefail

HOST="${1:?usage: install.sh <ssh-host> [config-dir] [restart-cmd]}"
CONFIG_DIR="${2:-/opt/homeassistant/config}"
RESTART="${3:-docker restart homeassistant}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VERSION="$(python3 -c "import json;print(json.load(open('$ROOT/custom_components/remoto_branding/manifest.json'))['version'])")"
echo "→ Remoto Branding $VERSION → $HOST:$CONFIG_DIR"

ssh "$HOST" "mkdir -p '$CONFIG_DIR/custom_components'"
# tar over ssh works on both Docker hosts and the HA OS SSH add-on (no rsync needed)
tar -C "$ROOT/custom_components" --exclude '__pycache__' -czf - remoto_branding \
  | ssh "$HOST" "rm -rf '$CONFIG_DIR/custom_components/remoto_branding' && tar -C '$CONFIG_DIR/custom_components' -xzf -"
# Enable once; the integration then sets itself up and installs the Remoto theme.
ssh "$HOST" "grep -q '^remoto_branding:' '$CONFIG_DIR/configuration.yaml' || printf '\n# Added by Remoto\nremoto_branding:\n' >> '$CONFIG_DIR/configuration.yaml'"

echo "→ restarting: $RESTART"
ssh "$HOST" "$RESTART"
echo "✓ done"
