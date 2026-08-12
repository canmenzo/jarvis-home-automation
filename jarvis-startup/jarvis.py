"""J.A.R.V.I.S. startup greeter — speaks a briefing on boot, then opens the workspace."""
import argparse
import asyncio
import ctypes
import logging
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import date, datetime, time as dtime, timedelta
from logging.handlers import RotatingFileHandler

import edge_tts
import feedparser
import requests
import sounddevice as sd
import soundfile as sf
import static_ffmpeg

import config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "jarvis.log")

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
KEV_WINDOW_DAYS = 7

log = logging.getLogger("jarvis")

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Light showers",
    81: "Showers", 82: "Heavy showers", 95: "Thunderstorm",
}

WET_CODES = {51, 53, 55, 61, 63, 65, 80, 81, 82, 95}

GREETINGS = {
    "morning": ["Good morning, sir.", "Morning, sir.", "Rise and shine, sir."],
    "afternoon": ["Good afternoon, sir.", "Afternoon, sir."],
    "evening": ["Good evening, sir.", "Evening, sir.", "Welcome home, sir."],
    "night": ["Working late, sir?", "Burning the midnight oil, sir.",
              "It is rather late, sir, but I am at your service."],
}

OPENERS = [
    "All systems are online and standing by.",
    "Systems nominal. Everything is exactly where you left it.",
    "Powering up. All subsystems report green.",
    "Diagnostics complete. We are running at full capacity.",
]

SIGNOFFS = [
    "Your workspace is ready. What shall we do today, sir?",
    "The workspace is prepared. Where would you like to begin, sir?",
    "Everything is ready for you, sir.",
]


def setup_logging(verbose=False):
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")

    fh = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)

    # Absent when launched headless via pythonw / the startup VBS.
    if sys.stdout is not None:
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        log.addHandler(sh)


def alert(title, body):
    """Surface a failure that would otherwise be invisible under the hidden startup window."""
    try:
        ctypes.windll.user32.MessageBoxW(0, body, title, 0x10)
    except Exception:
        log.warning("could not show message box", exc_info=True)


def part_of_day(now):
    h = now.hour
    if 5 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    if 17 <= h < 22:
        return "evening"
    return "night"


def get_audio_device_index():
    for i, d in enumerate(sd.query_devices()):
        if config.AUDIO_DEVICE in d["name"] and d["max_output_channels"] > 0:
            log.info("audio device %s: %s", i, d["name"])
            return i
    log.warning("audio device %r not found, falling back to system default", config.AUDIO_DEVICE)
    return None


def get_weather():
    for attempt in range(5):
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={config.WEATHER_LAT}&longitude={config.WEATHER_LON}"
                "&current=temperature_2m,apparent_temperature,weather_code"
                "&temperature_unit=celsius",
                timeout=8,
            )
            r.raise_for_status()
            cur = r.json()["current"]
            return {
                "temp": round(cur["temperature_2m"]),
                "feels": round(cur["apparent_temperature"]),
                "code": cur["weather_code"],
            }
        except Exception:
            # The network stack is often not up yet this early in boot.
            log.debug("weather attempt %s failed", attempt + 1, exc_info=True)
            time.sleep(3)
    log.warning("weather unavailable after 5 attempts")
    return None


def weather_line(w):
    desc = WMO_CODES.get(w["code"], "Clear")
    line = (f"Current conditions in {config.WEATHER_CITY}: {desc}, "
            f"{w['temp']} degrees, feels like {w['feels']}.")
    if w["code"] in WET_CODES:
        line += " You may want an umbrella."
    elif w["feels"] >= 32:
        line += " Do stay hydrated out there."
    elif w["feels"] <= 4:
        line += " I would advise a coat."
    return line


def say_cve(cve):
    parts = cve.split("-")
    return f"C V E {parts[1]}, {parts[2]}" if len(parts) == 3 else cve


def say_product(vendor, product):
    """KEV product names carry parentheticals and 'and'-joined variants that read badly aloud."""
    product = re.sub(r"\s*\([^)]*\)", "", product)
    product = re.split(r"\s+and\s+", product)[0]
    product = re.sub(r"\s+", " ", product).strip(" ,")
    return f"{vendor} {product}".strip()


def get_kev():
    """Vulnerabilities added to the CISA Known Exploited Vulnerabilities catalog this week."""
    try:
        r = requests.get(KEV_URL, timeout=20)
        r.raise_for_status()
        cutoff = date.today() - timedelta(days=KEV_WINDOW_DAYS)
        recent = [v for v in r.json()["vulnerabilities"]
                  if date.fromisoformat(v["dateAdded"]) >= cutoff]
    except Exception:
        log.warning("KEV feed unavailable", exc_info=True)
        return None

    if not recent:
        log.info("no new KEV entries in the last %s days", KEV_WINDOW_DAYS)
        return None

    recent.sort(key=lambda v: v["dateAdded"], reverse=True)
    latest = recent[0]
    ransomware = [v for v in recent if v["knownRansomwareCampaignUse"] == "Known"]

    noun = "vulnerability" if len(recent) == 1 else "vulnerabilities"
    line = (f"Threat intelligence: C I S A added {len(recent)} exploited {noun} "
            f"to the K E V catalog this week. The most recent is {say_cve(latest['cveID'])}, "
            f"affecting {say_product(latest['vendorProject'], latest['product'])}.")
    if ransomware:
        verb = "is" if len(ransomware) == 1 else "are"
        line += f" {len(ransomware)} of them {verb} linked to known ransomware campaigns."
    return line


def get_headline():
    for url in ("https://feeds.feedburner.com/TheHackersNews",
                "https://www.bleepingcomputer.com/feed/"):
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                return feed.entries[0].title
        except Exception:
            log.debug("feed %s failed", url, exc_info=True)
    log.warning("no security headline available")
    return None


def _event_start(ev):
    v = ev["DTSTART"].dt
    if isinstance(v, datetime):
        return v.astimezone() if v.tzinfo else v.astimezone()
    return datetime.combine(v, dtime.min).astimezone()  # all-day event


def get_next_event():
    """Next calendar event today, via a Google Calendar secret iCal URL (no OAuth)."""
    url = getattr(config, "CALENDAR_ICS_URL", "")
    if not url:
        return None
    try:
        import icalendar
        import recurring_ical_events

        r = requests.get(url, timeout=15)
        r.raise_for_status()
        cal = icalendar.Calendar.from_ical(r.content)

        now = datetime.now().astimezone()
        end_of_day = datetime.combine(now.date(), dtime.max).astimezone()
        events = recurring_ical_events.of(cal).between(now, end_of_day)
    except Exception:
        log.warning("calendar unavailable", exc_info=True)
        return None

    if not events:
        log.info("no remaining events today")
        return None

    events.sort(key=_event_start)
    ev = events[0]
    title = str(ev.get("SUMMARY", "an appointment"))
    start = _event_start(ev)
    when = start.strftime("%I:%M %p").lstrip("0")
    remaining = len(events)

    line = f"Your next appointment is {title}, at {when}."
    if remaining > 1:
        line += f" You have {remaining} events remaining today."
    return line


def build_message(now, weather, kev, headline, event):
    parts = [random.choice(GREETINGS[part_of_day(now)]), random.choice(OPENERS)]
    if weather:
        parts.append(weather_line(weather))
    if event:
        parts.append(event)
    if kev:
        parts.append(kev)
    elif headline:
        parts.append(f"Top cybersecurity headline: {headline}.")
    parts.append(random.choice(SIGNOFFS))
    return " ".join(parts)


async def speak(text):
    communicate = edge_tts.Communicate(text, config.VOICE, rate=config.RATE, pitch=config.PITCH)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        mp3_path = f.name
    await communicate.save(mp3_path)

    wav_path = mp3_path.replace(".mp3", ".wav")
    result = subprocess.run(
        ["ffmpeg", "-i", mp3_path,
         "-af", "equalizer=f=300:width_type=o:width=2:g=-3,"
                "equalizer=f=4000:width_type=o:width=2:g=5,"
                "aecho=0.8:0.9:25:0.15",
         wav_path, "-y"],
        capture_output=True,
    )
    if result.returncode != 0:
        log.error("ffmpeg failed: %s", result.stderr.decode(errors="replace")[-500:])
        raise RuntimeError("ffmpeg could not render the greeting")

    data, samplerate = sf.read(wav_path, dtype="float32")
    sd.play(data, samplerate, device=get_audio_device_index())
    sd.wait()

    os.unlink(wav_path)
    os.unlink(mp3_path)


def open_apps():
    # Spotify — open app, load playlist, press play
    if os.path.exists(config.SPOTIFY_EXE):
        subprocess.Popen([config.SPOTIFY_EXE])
        time.sleep(5)
    else:
        log.warning("Spotify not found at %s", config.SPOTIFY_EXE)
    subprocess.run(
        ["powershell", "-c", f"Start-Process '{config.SPOTIFY_PLAYLIST_URI}'"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    time.sleep(3)
    subprocess.run(
        ["powershell", "-c",
         "$wshell = New-Object -ComObject wscript.shell; "
         "$wshell.AppActivate('Spotify'); "
         "Start-Sleep 1; "
         "$wshell.SendKeys(' ')"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    if os.path.exists(config.LIBREWOLF_EXE):
        subprocess.Popen([config.LIBREWOLF_EXE])
    else:
        log.warning("LibreWolf not found at %s", config.LIBREWOLF_EXE)

    if os.path.exists(config.DISCORD_EXE):
        subprocess.Popen([config.DISCORD_EXE, "--processStart", "Discord.exe"])
    else:
        log.warning("Discord not found at %s", config.DISCORD_EXE)

    # CREATE_NEW_CONSOLE is required because jarvis.py runs headless (VBS window
    # style 0), so child processes inherit no console to attach to.
    if config.CLAUDECODE_DIR and os.path.isdir(config.CLAUDECODE_DIR):
        subprocess.Popen(
            ["powershell.exe", "-NoExit", "-Command",
             f"Set-Location '{config.CLAUDECODE_DIR}'; claude --dangerously-skip-permissions"],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    elif config.CLAUDECODE_DIR:
        log.warning("CLAUDECODE_DIR does not exist: %s", config.CLAUDECODE_DIR)


async def run(args):
    now = datetime.now()
    log.info("=== jarvis start (%s) ===", now.strftime("%Y-%m-%d %H:%M:%S"))

    weather = get_weather()
    kev = get_kev()
    headline = None if kev else get_headline()
    event = get_next_event()

    message = build_message(now, weather, kev, headline, event)
    log.info("message: %s", message)

    if args.text_only:
        print(message)
        return

    if not args.dry_run:
        open_apps()
    await speak(message)
    log.info("=== jarvis done ===")


def main():
    p = argparse.ArgumentParser(description="Jarvis startup greeter")
    p.add_argument("--dry-run", action="store_true", help="speak the briefing but do not open apps")
    p.add_argument("--text-only", action="store_true", help="print the briefing, no audio, no apps")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = p.parse_args()

    setup_logging(args.verbose)
    try:
        asyncio.run(run(args))
    except Exception:
        log.exception("jarvis failed")
        alert("Jarvis failed to start",
              f"{traceback.format_exc()[-900:]}\n\nFull log: {LOG_PATH}")
        sys.exit(1)


if __name__ == "__main__":
    static_ffmpeg.add_paths()
    main()
