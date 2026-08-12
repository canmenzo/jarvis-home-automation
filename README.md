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
- 🕐 Varies the greeting by time of day — morning, afternoon, evening, and a knowing *"burning the midnight oil, sir"* after 10pm. Openers and sign-offs rotate, so he never sounds like a recording
- 🌦️ Reads current weather via open-meteo.com (no API key, no nonsense) and actually comments on it — umbrella if it's wet, hydration if it's brutal, a coat if it's freezing
- 🛡️ Briefs you on the **CISA KEV catalog** — how many actively exploited vulns landed this week, the newest one by vendor and product, and how many are tied to ransomware campaigns. Falls back to a Hacker News / BleepingComputer headline if the feed is down
- 📅 Tells you your next appointment today (optional — Google Calendar secret iCal URL, no OAuth dance)
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

**Flags — for when you don't want to reboot just to test a sentence:**

```bash
python jarvis.py --text-only   # print the briefing. no audio, no apps
python jarvis.py --dry-run     # speak it, but don't open anything
python jarvis.py -v            # debug logging
```

**Run on every boot (Windows):**

`run_jarvis.vbs` is self-locating — it runs the `jarvis.py` sitting next to it, so there is nothing to edit.

1. Press `Win+R` → type `shell:startup` → hit Enter
2. Drop a **shortcut** to `run_jarvis.vbs` in that folder — right-drag it in and pick *Create shortcuts here*
3. Reboot. Sit down. Let him talk.

> 📌 A **shortcut**, not a copy. Copy the file and you now maintain two versions of it; the one that actually runs on boot is the one you forget to update. Same reason the script shouldn't live in `C:\tmp` — Disk Cleanup and Storage Sense eventually eat temp directories. Keep it in the repo, point a shortcut at it.

---

### when Jarvis goes quiet 🔇

The startup VBS runs with the window hidden, which means a crash is completely silent — the script can be dead for months before you notice the room is too quiet. So it now tells you:

- **`jarvis-startup/jarvis.log`** — every run appends here (rotating, 1MB × 3). Weather failures, missing apps, the exact briefing text, which audio device got picked
- **A message box on any crash** — full traceback, so a broken boot announces itself instead of hiding

If he ever stops talking, read the log first. The usual suspects, in order:

| symptom | cause |
|---|---|
| no log at all, ever | the shortcut isn't in `shell:startup` — it does not survive a Windows reinstall |
| log stops at import | Python was reinstalled, dependencies are gone → `pip install -r requirements.txt` |
| `audio device not found` | device name changed → re-run the `sd.query_devices()` snippet, update `config.py` |

> 💀 **Do not add a "only greet on Wake-on-LAN" guard.** It is a very tempting idea and it will break everything. If your PC wakes from full power-off (S5) rather than sleep, Windows keeps no wake history — `powercfg /lastwake` returns `Wake History Count - 0` and the guard exits on *every single boot*. Ask me how I know. If you genuinely need it, the only workable route is having the NAS webhook record its last-trigger timestamp behind a `/lastwake` endpoint that Jarvis polls at startup.

---

## config 🔧

| File | What's in it |
|------|-------------|
| `wol-webhook/.env` | your PC's MAC address + secret token |
| `jarvis-startup/config.py` | paths, city, Spotify URI, audio device, calendar iCal URL |

> 🔐 The calendar URL is a *secret address* — anyone holding it can read your calendar. It lives in the gitignored `config.py`. Leave it as `""` to skip the calendar entirely.

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
    ├── run_jarvis.vbs      # hidden-window Windows startup launcher
    └── jarvis.log          # written at runtime, gitignored
```

---

## PRs welcome 🦾

this is v1. it works and it slaps, but the mansion deserves more. here's what i'd love to see built:

- [ ] HomeKit / Google Home trigger (ditch the Siri shortcut dependency)
- [ ] Smart lights on boot — Govee, Hue, whatever you have
- [x] ~~Dynamic greetings based on time of day, calendar, or current mood~~ — shipped
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
