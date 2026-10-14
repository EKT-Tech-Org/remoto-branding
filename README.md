# Remoto Branding

White-labels the smart-home web UI as **Remoto**: the browser tab, the login page, the loading screen, the home-screen (PWA) icon, the theme and visible text. It works locally and through Nabu Casa.

## Deploy

### Docker boxes (recommended): the Remoto image
The image is the upstream image with Remoto built in. It installs the integration and the theme by itself, with **nothing to configure**.

**New or existing box**, run on the box:
```bash
curl -fsSL -H "Authorization: token <TOKEN>" \
  https://raw.githubusercontent.com/EKT-Tech-Org/remoto-branding/main/deploy/client/setup.sh \
  | bash -s -- <TOKEN>
```
- `<TOKEN>`: a GitHub token with read access to this repo (to download the script). Keep it in the office password manager.
- The image itself is public: `docker pull ghcr.io/ekt-tech-org/remoto:<tag>` works without a login, on Intel/AMD boxes and on Raspberry Pi (64-bit OS).
- Existing box: if a container named `homeassistant` is already running, its config folder is reused and backed up first. Devices, automations and history are kept.

**Upgrade:** set `REMOTO_VERSION` in `/opt/remoto/.env` to a published tag, then run `docker compose up -d` in `/opt/remoto`.
Published tags: GitHub → repo → Packages → `remoto`. A tag is only published after all checks pass.

### HA OS boxes
`deploy/install.sh root@<box> /config "ha core restart"` (needs the SSH add-on). It copies the integration, enables it and turns zeroconf off, and the integration then sets itself up.

### Still manual, per client
1. Create the client's user as **non-admin** (Settings → People).
2. Nabu Casa: set a custom domain (`<client>.remoto.<ourdomain>`) instead of `*.ui.nabu.casa`.

## How updates stay safe
- `HA compatibility` runs on every push and every Thursday. It builds the image for the **pinned** version (`deploy/.env`) and for upstream **stable**, then runs the Playwright checks on a fresh box and on an existing one.
- When it passes on `main`, the image is published as `remoto:<version>`, and the pinned build also as `remoto:latest`.
- To move clients to a newer upstream version, bump `HA_VERSION` in `deploy/.env` once the stable job is green and merge. `latest` then follows.
- If a run goes red, fix `www/remoto.js` (or `pages.py`), then bump `version` in `manifest.json`.

## Layout
| Path | Purpose |
|---|---|
| `custom_components/remoto_branding/` | The integration: script injection, HTML shell patches (`pages.py`), theme (`theme.py`), YAML auto-setup |
| `docker/` | Image build: Dockerfile, start-up installer, starter config for new boxes |
| `deploy/client/` | Client box compose file and one-line setup script |
| `deploy/docker-compose.yml` | Local dev instance (`docker compose -f deploy/docker-compose.yml up -d --build`) |
| `brand/` | Official Remoto logos and favicons (source for `www/icons`) |
| `tests/` | Playwright branding checks and the default_config drift check |
| `docs/technician-test-plan.csv` | Field test checklist |
| `docs/technician-laptop-setup.md` | Run Remoto on a technician's laptop (demo / onboarding practice) |

## License
Builds on Apache-2.0 licensed software. See `custom_components/remoto_branding/NOTICE`.
