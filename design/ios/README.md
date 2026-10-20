# Remoto iOS dashboard design

Uses the existing [iOS Themes](https://github.com/basnijholt/lovelace-ios-themes)
project by Bas Nijholt, Home Assistant's standard cards and
[card-mod](https://github.com/thomasloven/lovelace-card-mod). The iOS theme is
installed with HACS, not copied or forked here. Remoto's integration continues
to provide the name, logos, login and PWA branding.

`preview.html` is an offline visual mockup with illustrative readings. It does
not connect to Home Assistant. `starter.yaml` is the actual importable dashboard
with generic example entities. Map these to the site and check all gauge limits
and severity thresholds before use. It includes monitoring only.

## Activate the theme you downloaded

1. In HACS, install **iOS Themes** and **card-mod**. Keep Mushroom installed if
   your existing dashboard uses Mushroom cards; the starter does not require it.
2. In `/config/configuration.yaml`, merge this into the existing `frontend:`
   section. There must be only one `frontend:` key. Keep its other settings:

   ```yaml
   frontend:
     themes: !include_dir_merge_named themes
   ```

3. Restart Home Assistant after changing `configuration.yaml`. For later YAML
   theme changes, use Developer Tools → Actions → `frontend.reload_themes`.
4. Open your user profile and select **ios-dark-mode-blue-red** as the theme.
   The starter also selects it on its Overview view. An existing view with its
   own `theme:` overrides your profile selection; update that view if needed.
5. Confirm card-mod appears in Settings → Dashboards → Resources, using the URL
   installed by HACS. If configuring `frontend.extra_module_url` for card-mod,
   use that exact resource URL, including its version query. Follow card-mod's
   documentation to avoid loading two different versions.

The theme's standard background loads from the iOS Themes GitHub project.
For an offline installation, follow the project's local background instructions,
then select **ios-dark-mode-blue-red-alternative** in the profile and change the
starter view's `theme:` to the same name. The background file is
`/config/www/ios-themes/homekit-bg-blue-red.jpg`.

## Preview and install on a test dashboard

1. Open `preview.html` in a browser. This shows the intended layout and style;
   it is not a pixel-accurate rendering of Home Assistant's components.
2. Back up your current dashboard through its Raw configuration editor.
3. Create a new dashboard called **Remoto iOS Test** and take control of it if
   prompted. Open its Raw configuration editor and paste `starter.yaml`, or
   the output generated from your existing dashboard below.
4. Replace every `example_` entity with an actual entity ID. The sample entities
   deliberately do not have simulated states in Home Assistant.
5. Check desktop and phone layouts; available and unavailable readings; gauge
   thresholds; history; icons; and state-dependent warning colors. Compare any
   controls against the backup before switching users to the new dashboard.

Theme/card-mod styling is separate from the Docker image. Building or pulling
the Remoto image alone does not install HACS dependencies, import a dashboard,
or change each user's profile preference. No deployment script is run here.

## Apply the style to your current dashboard

Run on your workstation, outside the Home Assistant managed Python environment:

```bash
python3 -m venv .venv-ios
.venv-ios/bin/pip install -r design/ios/requirements.txt
.venv-ios/bin/python design/ios/style_dashboard.py current.yaml reviewed-ios.yaml
```

The output must be a new file; the tool refuses to overwrite. It accepts a full
raw exported dashboard, not a `configuration.yaml` containing `!include` tags.
It appends theme-aware CSS to supported gauge, tile, entity, entities, button
and Mushroom template cards, including cards nested inside grids and stacks.
Other custom cards keep their own styles. Existing CSS and shadow-root rules
are retained. Existing fixed sizes may still need manual adjustment.

Gauge cards use `needle: false` for a filled semicircle. Gauges with `segments`
retain their needle setting because Home Assistant requires `needle: true` for
segments. Entities, units, ranges, severity thresholds, actions, conditions and
templates are preserved. Static Mushroom icon colors follow the theme; templated
icon colors remain state-driven. Native cards keep their state colors. These
are the existing MDI icons with iOS-inspired styling, not Apple SF Symbols.

YAML formatting and comments are normalized by PyYAML. Review the output before
importing it. Your site export stays outside this public repository.

## Rebuild the starter and validate

```bash
python3 design/ios/style_dashboard.py design/ios/starter.source.yaml /tmp/starter.yaml
diff -u design/ios/starter.yaml /tmp/starter.yaml
python3 -m unittest discover -s tests/ios -v
```

Automated checks cover preservation of dashboard behavior, idempotence, nested
cards, segmented gauges, dynamic colors and overwrite refusal. They do not
replace testing in a running Home Assistant instance. No live deployment or
Home Assistant browser rendering was performed during package preparation.

## Rollback

Select the previous theme in your profile and return to the previous dashboard.
If you replaced a dashboard's YAML, restore the raw export you backed up. The
Remoto branding integration does not need to be removed.
