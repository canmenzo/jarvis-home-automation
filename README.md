# Jarvis Home Automation

Iron Man-style home automation: say **"Hey Siri, Wake up Daddy's Home"** → PC wakes via Wake-on-LAN → Windows boots → Jarvis greets you through the speakers.

```
iPhone (Siri) → NAS webhook → WoL magic packet → PC boots → Jarvis speaks
```

---

## Components

### 1. WoL Webhook (NAS / always-on device)

A lightweight Flask container that receives an HTTP request and sends a Wake-on-LAN magic packet.

**Setup:**

```bash
cd wol-webhook
cp .env.example .env
# Edit .env — set WOL_MAC and WOL_TOKEN
docker compose up -d
```

**Test it:**
```
http://<nas-ip>:8765/wakeup?token=<your_token>
```

> Run with `network_mode: host` so the magic packet reaches the LAN broadcast domain.

---

### 2. Siri Shortcut (iPhone)

1. Open **Shortcuts** → New Shortcut
2. Add action: **Get Contents of URL**
   - URL: `http://<nas-ip>:8765/wakeup?token=<your_token>`
   - Method: GET
3. Name it **"Wake up Daddy's Home"**
4. Optionally: **Accessibility → Back Tap → Double Tap** → assign the shortcut

Say *"Hey Siri, Wake up Daddy's Home"* to trigger it from anywhere on your network.

---

### 3. Jarvis Startup Script (Windows PC)

Runs on boot and:
- Greets you with a Jarvis-style TTS voice (Microsoft edge-tts, `en-GB-RyanNeural`)
- Reports current weather (via open-meteo.com — no API key needed)
- Reads the latest cybersecurity headline (The Hacker News / BleepingComputer)
- Opens Spotify, LibreWolf, Discord, and Claude Code

**Requirements:**
- Python 3.11+ (tested on 3.14 — note: `pydub` is broken on 3.14, uses `soundfile` + `static-ffmpeg` instead)
- `ffmpeg` will be auto-downloaded via `static-ffmpeg`

**Setup:**

```bash
cd jarvis-startup
pip install -r requirements.txt
cp config.example.py config.py
# Edit config.py — set your paths, city coords, Spotify URI, audio device
```

**Test run:**
```bash
python jarvis.py
```

**Run on startup (Windows):**

1. Edit `run_jarvis.vbs` — update the path to `jarvis.py`
2. Press `Win+R` → `shell:startup`
3. Copy `run_jarvis.vbs` into that folder

---

## Configuration

| File | Purpose |
|------|---------|
| `wol-webhook/.env` | MAC address + secret token (gitignored) |
| `jarvis-startup/config.py` | All user-specific settings (gitignored) |

Both files are gitignored. Copy the `.example` versions and fill in your values.

---

## Project Structure

```
jarvis-home-automation/
├── wol-webhook/
│   ├── app.py              # Flask webhook
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example        # Template — copy to .env
└── jarvis-startup/
    ├── jarvis.py           # Main Jarvis script
    ├── config.example.py   # Template — copy to config.py
    ├── requirements.txt
    └── run_jarvis.vbs      # Windows startup launcher
```

---

## License

MIT
