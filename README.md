# Remoto Branding

White-labels the smart-home web UI as **Remoto**: the browser tab, the login page, the loading screen, the home-screen (PWA) icon, the theme and visible text. It works locally and through Nabu Casa.

Remoto is an add-on to the upstream software, not a copy of it. Client boxes run the official upstream image, and this repo adds the branding on top and tests it on every upstream release.

## Deploy

### Docker boxes (recommended)
**New or existing box**, run on the box as root:
```bash
T=<TOKEN>; curl -fsSL -H "Authorization: Bearer $T" -H "Accept: application/vnd.github.raw" \
  https://api.github.com/repos/EKT-Tech-Org/remoto-branding/contents/deploy/client/setup.sh \
  | bash -s -- "$T"
```
- `<TOKEN>`: a GitHub fine-grained token limited to this repo, with **Contents: read-only**. Keep it in the office password manager. The box stores it in `/opt/remoto/.token` for later updates.
- New box: it starts Remoto with a ready-made configuration.
- Existing box: if a container named `homeassistant` is running, it is stopped, its config folder is backed up to `/opt/remoto/backups/` and then reused. Devices, automations and history are kept. If the container has another name, put `HA_CONTAINER=<name>` in front of `bash`.
- The integration and the theme set themselves up. There is nothing to configure.

**Update:** run `/opt/remoto/update.sh` on the box. It moves the box to the latest tested release: the upstream version and the branding together.
- `/opt/remoto/update.sh <release>` installs a specific release, for example `2026.10.1-0.3.0`.
- `/opt/remoto/update.sh --rollback` returns to the release the box ran before.
- Before each update it saves the settings (without the history database) to `/opt/remoto/backups/` and keeps the last three.
- It ends with `✓ Remoto <release> running`, or says what is wrong.

Releases: GitHub → repo → Releases. A release is only created after all checks pass on that upstream version.

### HA OS boxes
`deploy/install.sh root@<box> /config "ha core restart"` (needs the SSH add-on). It copies the integration and enables it, and the integration then sets itself up. HA OS updates itself from its own update button, so it is not held to tested versions: check the latest release here before pressing it.

### Still manual, per client
1. Create the client's user as **non-admin** (Settings → People).
2. Nabu Casa: set a custom domain (`<client>.remoto.<ourdomain>`) instead of `*.ui.nabu.casa`.

## How Remoto follows upstream
`HA compatibility` runs every day, on every pull request and on every push to `main`.
- It reads the current upstream **stable** and **beta** versions.
- Stable is installed with the real `setup.sh` on a new box and on an existing one, then the Playwright checks look for any visible upstream name. The existing box must keep its data.
- When stable passes on `main`, a release `<upstream>-<branding>` is created, installed once more through the technician's download path, and then published. From then on `update.sh` offers it to boxes.
- Beta is tested as an early warning before each monthly upstream release. It never blocks a release.
- If a daily run fails, an issue is opened and no release is created, so boxes stay on the last tested version. Fix `www/remoto.js` (or `pages.py`), then bump `version` in `manifest.json`.

A change to the integration only reaches boxes after `version` in `manifest.json` is bumped, because the release name includes it.

## Layout
| Path | Purpose |
|---|---|
| `custom_components/remoto_branding/` | The integration: script injection, HTML shell patches (`pages.py`), theme (`theme.py`), YAML auto-setup |
| `deploy/client/` | Client box: `setup.sh` (one-time), `update.sh` (every update), `install-branding.sh`, compose file, starter config |
| `deploy/install.sh` | HA OS boxes, over SSH |
| `deploy/docker-compose.yml` | Local dev instance (see the file header) |
| `brand/` | Official Remoto logos and favicons (source for `www/icons`) |
| `tests/` | Playwright branding checks and the default_config drift check |
| `docs/technician-test-plan.csv` | Field test checklist |

## License
Builds on Apache-2.0 licensed software. See `custom_components/remoto_branding/NOTICE`.
