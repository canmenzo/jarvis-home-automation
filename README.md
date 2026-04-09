# J.A.R.V.I.S. Home Automation 🔴🟡

```
      ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
      ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
      ██║███████║██████╔╝██║   ██║██║███████╗
 ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
 ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
```

> *"Good morning, sir. Today's forecast..."*
> yeah. i built that. in my apartment. no arc reactor required.

**"Hey Siri, Wake up Daddy's Home"** → PC wakes via Wake-on-LAN → Windows boots → Jarvis greets you through the speakers like you just walked into the Malibu mansion.

```
iPhone (Siri) → NAS webhook → WoL magic packet → PC boots → Jarvis speaks
```

---

## the stack 🧱

three moving parts. all stupid simple. all very Iron Man.

### 1. WoL Webhook (NAS — always-on device) ⚡

Lightweight Flask container sitting on your NAS doing absolutely nothing until you speak. Then it fires a Wake-on-LAN magic packet across your LAN like a butler who takes his job seriously.

**Setup:**

```bash
cd wol-webhook
cp .env.example .env
# set WOL_MAC (your PC's MAC address) and WOL_TOKEN (make it something good)
docker compose up -d
```

**Test it:**
```
http://<nas-ip>:8765/wakeup?token=<your_token>
```

> `network_mode: host` is required — magic packets don't survive NAT. don't ask how long it took me to figure that out.

---

### 2. Siri Shortcut (iPhone) 🎙️

No custom app. No subscription. No API key. Just Apple Shortcuts doing exactly what we need it to do.

1. Open **Shortcuts** → New Shortcut
2. Add action: **Get Contents of URL**
   - URL: `http://<nas-ip>:8765/wakeup?token=<your_token>`
   - Method: GET
3. Name it **"Wake up Daddy's Home"**
4. Bonus move: **Accessibility → Back Tap → Double Tap** → assign the shortcut

*"Hey Siri, Wake up Daddy's Home"* — say it with the energy of someone who just flew in from a press conference.

---

### 3. Jarvis Startup Script (Windows) 🖥️

Runs on boot. Greets you. Briefs you. Opens your apps. You just sit down and feel powerful.

**What Jarvis does when you boot:**
- 🗣️ Greets you in a proper British accent — `en-GB-RyanNeural` (closest thing to Paul Bettany without a SAG card)
- 🌦️ Reads current weather via open-meteo.com (no API key, no nonsense)
- 📰 Pulls latest cybersecurity headline from The Hacker News, falls back to BleepingComputer
- 🎵 Opens Spotify on your Iron Man playlist, LibreWolf, Discord, and your terminal

**Requirements:** Python 3.11+

> ⚠️ `pydub` is broken on Python 3.14 — they removed `audioop`. this repo uses `soundfile` + `static-ffmpeg` instead. ffmpeg auto-downloads itself, you don't have to touch anything.

**Setup:**

```bash
cd jarvis-startup
pip install -r requirements.txt
cp config.example.py config.py
# edit config.py — set your paths, city coordinates, Spotify URI, audio device index
python jarvis.py
```

**Run on every boot (Windows):**

1. Edit `run_jarvis.vbs` — update the path to your `jarvis.py`
2. Press `Win+R` → type `shell:startup` → hit Enter
3. Drop `run_jarvis.vbs` into that folder
4. Reboot. Sit down. Let him talk.

---

## config 🔧

| File | What's in it |
|------|-------------|
| `wol-webhook/.env` | your PC's MAC address + secret token |
| `jarvis-startup/config.py` | paths, city, Spotify URI, audio device |

Both are gitignored. Copy the `.example` versions and fill them in. You won't accidentally push your home network layout to GitHub.

---

## project structure 📂

```
jarvis-home-automation/
├── wol-webhook/
│   ├── app.py              # Flask webhook — receives the call, sends the packet
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example        # copy this → .env
└── jarvis-startup/
    ├── jarvis.py           # the man himself
    ├── config.example.py   # copy this → config.py
    ├── requirements.txt
    └── run_jarvis.vbs      # hidden-window Windows startup launcher
```

---

## PRs welcome 🦾

this is v1. it works and it slaps, but the mansion deserves more. here's what i'd love to see built:

- [ ] HomeKit / Google Home trigger (ditch the Siri shortcut dependency)
- [ ] Smart lights on boot — Govee, Hue, whatever you have
- [ ] Dynamic greetings based on time of day, calendar, or current mood
- [ ] Home Assistant integration
- [ ] Multi-room / multi-speaker audio
- [ ] Mobile app shortcut for Android users
- [ ] Sleep command — "Jarvis, shut it down"
- [ ] Pepper's voice profile (this one's important)

**if you build something cool on top of this, open a PR.** i'll merge it if it doesn't make Jarvis sound like a Raspberry Pi with anxiety.

---

## easter egg 🥚

```
J.A.R.V.I.S.
Just A Rather Very Intelligent System
```

*Marvel's official acronym. we are genuinely living in a Tony Stark fever dream and nobody told us.*

also — if you put your Iron Man Spotify playlist in `config.py` so Jarvis opens it on boot, that's the correct way to start every morning. [here's mine](https://open.spotify.com/playlist/0S78UVuLW857NQ2FaUYwTD) if you need a reference.

---

## license

MIT — do whatever you want, just don't make it worse than FRIDAY.
