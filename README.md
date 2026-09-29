# 🤖 J.A.R.V.I.S. Home Automation

![python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white) ![platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white) ![webhook](https://img.shields.io/badge/webhook-Docker-2496ED?logo=docker&logoColor=white)

> *"Good morning, sir. Today's forecast..."*

Say "Hey Siri, Wake up Daddy's Home" and your PC wakes over Wake-on-LAN, boots Windows, and Jarvis greets you through the speakers with a spoken briefing, then opens your workspace.

```
iPhone (Siri) → webhook on an always-on box → WoL magic packet → PC boots → Jarvis speaks
```

### ✨ Features
- ⚡ Tiny Flask webhook in Docker that sends a WoL magic packet on `GET /wakeup?token=...` (constant-time token check, `/health` endpoint)
- 🗣️ British TTS voice (`en-GB-RyanNeural` via edge-tts) with greetings that change by time of day and rotate so it never sounds canned
- 🌦️ Current weather from open-meteo.com (no API key), with a nudge for an umbrella, water, or a coat
- 🛡️ Threat brief from the CISA KEV catalog: new exploited vulns this week, the newest one, and how many are tied to ransomware (falls back to a Hacker News / BleepingComputer headline)
- 📅 Optional next appointment today from a Google Calendar secret iCal URL (no OAuth)
- 🎵 Opens Spotify on your playlist and presses play, plus LibreWolf, Discord, and a PowerShell window running Claude Code in a folder you pick
- 🔎 Rotating log file and a message box on any crash, so a hidden startup failure doesn't stay silent

### 🚀 Quick start

**1. WoL webhook** (NAS or any always-on Linux box with Docker)

```bash
cd wol-webhook
cp .env.example .env   # set WOL_MAC (the PC's MAC) and WOL_TOKEN (a long random string)
docker compose up -d
curl "http://<host>:8765/wakeup?token=<your_token>"   # should wake the PC
```

> `network_mode: host` is required. Magic packets don't survive Docker's NAT.

**2. Siri Shortcut** (iPhone)

1. Shortcuts → New Shortcut → **Get Contents of URL**
2. URL `http://<host>:8765/wakeup?token=<your_token>`, method GET
3. Name it **"Wake up Daddy's Home"** (optional: Accessibility → Touch → Back Tap → Double Tap)

**3. Jarvis greeter** (Windows PC)

```bash
cd jarvis-startup
pip install -r requirements.txt
cp config.example.py config.py   # paths, coordinates, Spotify URI, audio device
python jarvis.py --text-only     # print the briefing, no audio, no apps
python jarvis.py --dry-run       # speak it, don't open apps
python jarvis.py -v              # full run with debug logging
```

To run it on every boot: `Win+R` → `shell:startup`, then right-drag `run_jarvis.vbs` into that folder and pick *Create shortcuts here*. Use a **shortcut**, not a copy: the VBS is self-locating and runs the `jarvis.py` next to it, so a copy silently drifts from the repo. Keep the repo out of temp folders, which Storage Sense eventually cleans.

> ⚠️ `pydub` is broken on Python 3.14 (`audioop` was removed). This repo uses `soundfile` + `static-ffmpeg` instead, and ffmpeg downloads itself.

### ⚙️ Configuration

| File | What's in it |
|------|-------------|
| `wol-webhook/.env` | the PC's MAC address and the webhook token |
| `jarvis-startup/config.py` | voice, audio device, weather coordinates, calendar iCal URL, Spotify URI, app paths, Claude Code folder |

Both are gitignored; copy the `.example` versions. List audio devices with `python -c "import sounddevice as sd; print(sd.query_devices())"`. The calendar URL is a secret: anyone holding it can read your calendar. Leave it `""` to skip the calendar.

### 🔇 When Jarvis goes quiet

The VBS launcher hides the window, so read `jarvis-startup/jarvis.log` first (rotating, 1 MB x 3: weather failures, missing apps, the briefing text, the chosen audio device).

| Symptom | Cause |
|---|---|
| no log at all | the shortcut isn't in `shell:startup` (it doesn't survive a Windows reinstall) |
| log stops at import | Python was reinstalled; run `pip install -r requirements.txt` again |
| `audio device not found` | the device name changed; list devices and update `config.py` |

> 💀 **Don't add an "only greet on Wake-on-LAN" guard.** If the PC wakes from full power-off (S5), Windows keeps no wake history (`powercfg /lastwake` shows `Wake History Count - 0`), so the guard exits on every boot. This was tried and reverted. The workable route would be the webhook recording its last trigger behind a `/lastwake` endpoint that Jarvis polls.

<details>
<summary>📂 Project layout and wishlist</summary>

```
wol-webhook/        Flask webhook: receives the call, sends the packet (Dockerfile, compose, .env.example)
jarvis-startup/     jarvis.py, config.example.py, requirements.txt, run_jarvis.vbs (hidden-window launcher)
```

PRs welcome for any of these:

- [ ] HomeKit / Google Home trigger instead of the Siri Shortcut
- [ ] Smart lights on boot (Govee, Hue)
- [ ] Home Assistant integration
- [ ] Multi-room audio
- [ ] Android trigger
- [ ] Sleep command: "Jarvis, shut it down"

J.A.R.V.I.S. = *Just A Rather Very Intelligent System*.

</details>

### 📄 License
MIT (stated here; no LICENSE file in the repo yet).
