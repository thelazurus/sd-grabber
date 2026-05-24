# 📡 SD Grabber

A self-hosted [Schedules Direct](https://schedulesdirect.org/) XMLTV grabber. Authenticates with the SD JSON API, fetches guide data and channel logos for your subscribed lineups, and serves the result as a standard XMLTV feed at `/epg.xml`.

Designed to feed into [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) alongside your IPTV provider's EPG, so you can mix and match per-channel sources before enrichment downstream.

> **Vibe coded** — this project was built entirely through conversational AI (Claude). It works and is tested, but hasn't been audited line-by-line by a human developer. Use it, break it, improve it — PRs welcome.

---

## Pipeline

```
SD Grabber  ─┐
             ├──→  Dispatcharr  ──→  FauxCable  ──→  Jellyfin / Emby
IPTV EPG   ─┘
```

SD Grabber fetches raw guide data from Schedules Direct. Dispatcharr merges it with your IPTV EPG and lets you pick the source per channel. [FauxCable](https://github.com/thelazurus/fauxcable) enriches Dispatcharr's output with poster art.

---

## Features

- **Full SD JSON API integration** — authenticates, fetches lineups, channels, schedules, and program details
- **Channel logos** — includes SD's station logo URLs in the XMLTV output
- **Scheduled pipeline** — runs on a configurable interval automatically
- **Web UI** — dashboard with run status and history, settings page
- **"Test connection" button** — verify SD credentials before your first run
- **HTTP EPG endpoint** — XMLTV served at `/epg.xml`, ready to add to Dispatcharr
- **SQLite run history** — see what ran, when, and how many stations/programs were fetched
- **Docker-ready** — single container, one volume mount

---

## Stack

- [FastAPI](https://fastapi.tiangolo.com/) + [Starlette](https://www.starlette.io/) — web server
- [HTMX](https://htmx.org/) + [Tailwind CSS](https://tailwindcss.com/) — UI (no build step)
- [aiosqlite](https://github.com/omnilib/aiosqlite) — async SQLite
- [APScheduler](https://apscheduler.readthedocs.io/) — scheduled pipeline runs
- [aiohttp](https://docs.aiohttp.org/) — async HTTP for SD API calls

---

## Quick Start

### Docker Compose (standalone)

```yaml
services:
  sd-grabber:
    build: https://github.com/thelazurus/sd-grabber.git
    container_name: sd-grabber
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=America/Chicago
      # Credentials can also be set via the Settings UI after first boot
      - SD_USERNAME=youruser
      - SD_PASSWORD=yourpassword
      # - SD_DAYS=3
      # - SCHEDULE_INTERVAL_HOURS=6
    restart: unless-stopped
```

### Combined stack with FauxCable

See [`docker-compose.yml`](docker-compose.yml) in this repo for the full stack example that includes both SD Grabber and FauxCable.

### After starting

1. Open `http://your-server-ip:8001`
2. If you didn't set credentials via env vars, go to **Settings** and enter your SD username and password
3. Hit **Test connection** to verify, then **Run Now** on the dashboard
4. Add `http://sd-grabber:8001/epg.xml` as an EPG source in Dispatcharr

---

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SD_USERNAME` | ✅ | Your Schedules Direct username |
| `SD_PASSWORD` | ✅ | Your SD password — stored as MD5 hash, never in plaintext |
| `SD_DAYS` | — | Days of guide data to fetch per run (default: `3`, max: `14`) |
| `SCHEDULE_INTERVAL_HOURS` | — | How often to auto-run (default: `6`) |
| `SD_OUTPUT_PATH` | — | Internal path for the XMLTV file (default: `data/epg.xml`) |

### Config priority

Settings are applied in this order, with later sources winning:

1. **Environment variables** — your compose file (primary)
2. **Settings page** — changes saved in the UI are written to `data/config.yaml` and take precedence over env vars on next restart

---

## Volume Mounts

| Host path | Container path | Purpose |
|-----------|---------------|---------|
| `./data/` | `/app/data/` | SQLite run history, XMLTV output, and Settings page overrides |

---

## Ports

| Port | Use |
|------|-----|
| `8001` | Web UI + `/epg.xml` endpoint |

---

## Requirements

A paid [Schedules Direct](https://schedulesdirect.org/) account (~$35/year) with at least one lineup added. SD provides guide data for US, Canada, and some international markets.

---

## License

MIT
