# Follow upstream releases without a Remoto image

Date: 2026-10-07

## Goal

Whenever upstream ships a new version, Remoto follows it and the branding stays.
The repo no longer builds or publishes its own Docker image.

## What was asked, and what is assumed

Asked: follow every upstream release, keep the branding, stop depending on a
Remoto Docker image.

Assumed:
- "Fork" means re-applying the branding on each upstream release. The upstream
  source is not copied or modified.
- The repo stays private, so a box still needs a token to download from it.
- A client box must only run an upstream version that passed the branding checks.

## Design

**Release = a tested pair.** A GitHub release tagged `<upstream>-<branding>`
(for example `2026.10.1-0.3.0`) means: this branding version passed every check
on this upstream version. The tag carries both versions, so there is no extra
metadata file and nothing to build.

**Boxes run the official image.** `deploy/client/docker-compose.yml` uses
`ghcr.io/home-assistant/home-assistant:${HA_VERSION}`, which is public. The
integration is copied into the box's config folder by
`deploy/client/install-branding.sh`, the one place that knows how to install it
(new box: starter configuration; existing box: append `remoto_branding:` once).

**One command to move a box.** `/opt/remoto/update.sh` reads the latest release,
downloads the repo at that tag, installs the branding, sets `HA_VERSION` and
recreates the container. `update.sh <release>` picks a specific one and
`update.sh --rollback` returns to the one before. It saves the config (without
the history database) before changing anything and checks the box comes back up
branded. `setup.sh` is the one-time bootstrap: it finds an existing
installation, stops it, backs it up, stores the token and runs `update.sh`.

**Updates are started by a technician.** An upstream release can change a
client's devices and automations, so nothing updates unattended.

**CI follows upstream daily.** The workflow reads the current stable and beta
versions from upstream's version feed.
- Stable is tested on a new box and on an existing box, both installed through
  the real `setup.sh` on a Linux runner. If it passes on `main` and no release
  exists for that pair, the release is created.
- Beta is tested on a new box as an early warning. It never blocks a release.
- A failed scheduled run opens an issue naming the upstream version. Nothing is
  released, so boxes stay on the last tested pair.
- Scheduled runs skip a stable pair that is already released.
- The release is first created as a pre-release, installed once through the
  real download path, and only then published. Boxes follow full releases only.

**Token.** A fine-grained token with read-only Contents access to this one repo
replaces the classic `repo` + `read:packages` token.

## Not included

- A fork of the upstream source.
- An in-app update button. On Docker the app cannot replace its own container.
- HA OS: unchanged. It updates itself from its own button, so it cannot be held
  to tested versions; `deploy/install.sh` still installs the branding.
- Unattended updates.

## Testing

- CI: Playwright branding checks on new and existing boxes, installed by
  `setup.sh`; existing data must survive; `update.sh` run a second time.
- Local: the same scripts on a Linux Docker host, including a version change
  and a rollback.
- Still needed on a real client-like box: `docs/technician-test-plan.csv`.
