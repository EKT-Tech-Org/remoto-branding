#!/usr/bin/env bash
# Move this box to a tested Remoto release: upstream version and branding together.
# Installed by setup.sh as /opt/remoto/update.sh. Run it as root.
#
#   update.sh              the latest tested release
#   update.sh <release>    a specific one, e.g. 2026.10.1-0.3.0
#   update.sh --rollback   the release this box ran before the last update
#
# A release is named <upstream version>-<branding version> and is only created
# after the branding checks passed on that pair.
#
# Testing: REMOTO_SOURCE=<repo checkout> installs from that folder instead of
# downloading, and then <release> is required.
set -euo pipefail

main() {
  DIR="$(cd "$(dirname "$0")" && pwd)"
  API="https://api.github.com/repos/EKT-Tech-Org/remoto-branding"
  ENV_FILE="$DIR/.env"
  URL="${HA_URL:-http://localhost:8123}"

  get() { sed -n "s/^$1=//p" "$ENV_FILE" 2>/dev/null | tail -1; }
  put() {
    touch "$ENV_FILE"
    grep -v "^$1=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
    echo "$1=$2" >> "$ENV_FILE.tmp"
    mv "$ENV_FILE.tmp" "$ENV_FILE"
  }
  api() {
    curl -fsSL -H "Authorization: Bearer $(cat "$DIR/.token")" \
      -H "X-GitHub-Api-Version: 2022-11-28" "$@"
  }

  CURRENT="$(get REMOTO_RELEASE)"
  CONFIG_DIR="$(get CONFIG_DIR)"
  [ -n "$CONFIG_DIR" ] || { echo "CONFIG_DIR is missing in $ENV_FILE; run setup.sh first"; exit 1; }

  case "${1:-}" in
    --rollback)
      RELEASE="$(get PREVIOUS_RELEASE)"
      [ -n "$RELEASE" ] || { echo "No earlier release recorded on this box"; exit 1; }
      ;;
    "")
      [ -z "${REMOTO_SOURCE:-}" ] || { echo "REMOTO_SOURCE needs an explicit <release>"; exit 1; }
      RELEASE="$(api "$API/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)"
      [ -n "$RELEASE" ] || { echo "Could not read the latest release (token or network?)"; exit 1; }
      ;;
    *) RELEASE="$1" ;;
  esac
  if ! echo "$RELEASE" | grep -Eq '^[0-9]{4}\.[0-9]+\.[0-9]+[a-z0-9.]*-[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Not a release name: $RELEASE (expected e.g. 2026.10.1-0.3.0)"; exit 1
  fi
  export HA_VERSION="${RELEASE%-*}"
  echo "→ Remoto $RELEASE (now: ${CURRENT:-none})"

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  if [ -n "${REMOTO_SOURCE:-}" ]; then
    SRC="$REMOTO_SOURCE"
  else
    SRC="$TMP/src"
    mkdir -p "$SRC"
    api "$API/tarball/$RELEASE" | tar -xz -C "$SRC" --strip-components=1
  fi

  cp "$SRC/deploy/client/docker-compose.yml" "$DIR/docker-compose.yml"
  cd "$DIR"
  # Download first, while the current version is still running.
  docker compose pull -q

  # First install: setup.sh already made a full backup of an existing box.
  if [ -n "$CURRENT" ]; then
    docker compose stop -t 120 >/dev/null 2>&1 || true
    mkdir -p "$DIR/backups"
    BACKUP="$DIR/backups/config-$CURRENT-$(date +%Y%m%d%H%M%S).tgz"
    # Settings, devices and automations; the history database is left out (large).
    tar -C "$(dirname "$CONFIG_DIR")" -czf "$BACKUP" \
      --exclude='home-assistant_v2.db*' --exclude='*.log*' --exclude="$(basename "$CONFIG_DIR")/backups" \
      "$(basename "$CONFIG_DIR")"
    echo "→ settings saved to $BACKUP"
    ls -1t "$DIR"/backups/config-*.tgz | tail -n +4 | xargs -r rm -f
  fi

  sh "$SRC/deploy/client/install-branding.sh" "$SRC" "$CONFIG_DIR"
  if [ "$RELEASE" != "$CURRENT" ] && [ -n "$CURRENT" ]; then
    put PREVIOUS_RELEASE "$CURRENT"
  fi
  put REMOTO_RELEASE "$RELEASE"
  put HA_VERSION "$HA_VERSION"
  docker compose up -d --force-recreate

  # Keep this script in step with the release.
  cp "$SRC/deploy/client/update.sh" "$DIR/update.sh.new"
  chmod +x "$DIR/update.sh.new"
  mv "$DIR/update.sh.new" "$DIR/update.sh"

  echo "→ waiting for the box to come back"
  BODY=""
  for _ in $(seq 1 150); do
    # The login page answers the same on a new box and on a configured one.
    BODY="$(curl -fsS -m 5 "$URL/auth/authorize" 2>/dev/null || true)"
    # The branding loads a moment after the web server, so keep polling until it shows.
    if [ -n "$BODY" ] && ! echo "$BODY" | grep -q '<title>Home Assistant</title>'; then
      echo "✓ Remoto $RELEASE running"
      return 0
    fi
    sleep 2
  done
  if [ -z "$BODY" ]; then
    echo "✗ The box did not come back. Check: docker logs homeassistant"
  else
    echo "✗ The box is up but shows the upstream name. Check: docker logs homeassistant | grep -i remoto"
  fi
  [ -z "$(get PREVIOUS_RELEASE)" ] || echo "  To go back: $DIR/update.sh --rollback"
  return 1
}

main "$@"
