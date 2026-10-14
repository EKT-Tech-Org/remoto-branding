# Run Remoto on your laptop

Use this to try Remoto, practise the onboarding, or show it to a client before installing their box.
It runs on your laptop only. Nothing here touches a client box.

## 1. One-time preparation
1. Install **Docker Desktop** from docker.com (Windows or Mac) and start it. Wait until it says *Engine running*.
2. Open a terminal: **PowerShell** on Windows, **Terminal** on Mac.

## 2. Start Remoto
Copy this as **one line**. It works the same in PowerShell and on a Mac:
```
docker run -d --name remoto -p 8123:8123 -v remoto-config:/config ghcr.io/ekt-tech-org/remoto:2026.9.4
```
The first time it downloads the image (a few minutes). Then wait 1–2 minutes for the first start.

## 3. Onboarding
Open **http://localhost:8123** in your browser.

1. **Create the owner account**: name, username, password. This is our admin account, not the client's.
2. **Home location**: set location, time zone and units.
3. **Analytics**: leave everything off.
4. **Devices found**: skip.
5. **Finish**. Remoto branding and theme are already on. You do not need to add or configure anything.

## 4. Show the client view
1. Settings > People > **Add person**. Turn **Allow login** ON and **Administrator** OFF.
2. Open a private/incognito window, go to http://localhost:8123 and log in as that person.
3. You should see: the teal R logo, the purple Log in button, "Remoto" in the tab and sidebar, and no "Home Assistant" text anywhere.

## Useful commands
| What | Command |
|---|---|
| Stop | `docker stop remoto` |
| Start again (keeps your accounts) | `docker start remoto` |
| See start-up messages | `docker logs remoto` (look for lines starting with `[remoto]`) |
| Remove completely and start over | `docker rm -f remoto` then `docker volume rm remoto-config` |

## Troubleshooting
- **`unauthorized` when downloading**: the image is not public yet. Tell the office.
- **`port is already allocated`**: something else uses port 8123. Stop it, or change `-p 8123:8123` to `-p 8124:8123` and open http://localhost:8124.
- **Page does not load**: wait another minute; `docker logs remoto` shows progress.
