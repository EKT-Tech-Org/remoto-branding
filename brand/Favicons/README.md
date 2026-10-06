# Favicons

Built from the app icon (teal `#59C7C4` tile, purple `#553D9F` R).

| File | Size | Use |
| --- | --- | --- |
| favicon.svg | vector | modern browsers |
| favicon-16.png, favicon-32.png, favicon-48.png | 16 / 32 / 48 | browser tabs, fallbacks |
| apple-touch-icon.png | 180 | iOS home screen (full-bleed square; iOS rounds it) |
| icon-192.png, icon-512.png | 192 / 512 | Android / PWA |
| icon-maskable-512.png | 512 | PWA maskable (R inside the 80% safe zone) |
| favicon.ico | 16+32+48 | legacy; in the download pack only (.ico can't be stored here) |

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#553d9f">
```

`site.webmanifest`:

```json
{ "name": "Remoto", "short_name": "Remoto",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "theme_color": "#553d9f", "background_color": "#ffffff", "display": "standalone" }
```
