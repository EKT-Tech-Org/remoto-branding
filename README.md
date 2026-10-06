# Remoto Branding

A custom integration that white-labels the smart-home web UI as **Remoto**: browser
tab title, favicon, home-screen (PWA) name and icon, and visible text. It works on
Docker and HA OS, both locally and through Nabu Casa remote access.

## Layout

| Path | Purpose |
|---|---|
| `custom_components/remoto_branding/` | The integration (Python + `www/remoto.js`) |
| `themes/remoto.yaml` | Remoto color theme |
| `deploy/` | Pinned docker-compose for local testing + `install.sh` for client boxes |
| `tests/e2e/` | Playwright check: no visible upstream branding |
| `.github/workflows/ha-compat.yml` | Weekly test against the newest upstream release |
| `brand/` | Official Remoto logos and favicons (source of truth; icons in `www/icons` are copied from here) |

## Client-install checklist

1. Copy the integration: `deploy/install.sh <host>` (see the script header).
2. Restart, then go to **Settings → Devices & services → Add integration → Remoto Branding**.
3. Add `frontend: themes: !include_dir_merge_named themes` and copy `themes/remoto.yaml`.
4. Set `homeassistant: name: "Remoto – <client>"`.
5. Replace `default_config:` with its individual items **without** `zeroconf`.
6. Create the client's user as **non-admin** and set their profile theme to `Remoto`.
7. Nabu Casa: set a custom domain (`<client>.remoto.<yourdomain>`) instead of `*.ui.nabu.casa`.

## Monthly update routine

1. Upstream ships on the first Wednesday of each month. Wait for the `.1`/`.2` patch.
2. Check the **HA compatibility** GitHub Action (it runs weekly against `stable`). Green means safe.
3. Bump `HA_VERSION` in `deploy/.env`, then roll out with `deploy/install.sh`.
4. If the check is red, fix `www/remoto.js`, bump `version` in `manifest.json` (this busts the browser cache), and release.

## License

Builds on Apache-2.0 licensed software. See `custom_components/remoto_branding/NOTICE`.
