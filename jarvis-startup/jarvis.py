import asyncio
import subprocess
import requests
import feedparser
import edge_tts
import sounddevice as sd
import numpy as np
import tempfile
import os
import time
import static_ffmpeg
import soundfile as sf

import config

static_ffmpeg.add_paths()

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Light showers",
    81: "Showers", 82: "Heavy showers", 95: "Thunderstorm",
}


def get_realtek_device_index():
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if config.AUDIO_DEVICE in d['name'] and d['max_output_channels'] > 0:
            return i
    return None


def get_weather():
    for _ in range(5):
        try:
            r = requests.get(
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={config.WEATHER_LAT}&longitude={config.WEATHER_LON}"
                "&current=temperature_2m,apparent_temperature,weather_code"
                "&temperature_unit=celsius",
                timeout=8
            )
            cur = r.json()["current"]
            temp = round(cur["temperature_2m"])
            feels = round(cur["apparent_temperature"])
            desc = WMO_CODES.get(cur["weather_code"], "Clear")
            return f"{desc}, {temp} degrees, feels like {feels}"
        except:
            time.sleep(3)
    return None


def get_headline():
    try:
        feed = feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
        if feed.entries:
            return feed.entries[0].title
    except:
        pass
    try:
        feed = feedparser.parse("https://www.bleepingcomputer.com/feed/")
        if feed.entries:
            return feed.entries[0].title
    except:
        pass
    return None


def build_message(weather, headline):
    msg = "Welcome home, sir. All systems are online and standing by."
    if weather:
        msg += f" Current conditions in {config.WEATHER_CITY}: {weather}."
    if headline:
        msg += f" Top cybersecurity intelligence: {headline}."
    msg += " Your workspace is ready. What shall we do today, sir?"
    return msg


async def speak(text):
    communicate = edge_tts.Communicate(text, config.VOICE, rate=config.RATE, pitch=config.PITCH)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp_path = f.name
    await communicate.save(tmp_path)

    wav_path = tmp_path.replace(".mp3", ".wav")
    subprocess.run(
        ["ffmpeg", "-i", tmp_path,
         "-af", "equalizer=f=300:width_type=o:width=2:g=-3,"
                "equalizer=f=4000:width_type=o:width=2:g=5,"
                "aecho=0.8:0.9:25:0.15",
         wav_path, "-y"],
        capture_output=True
    )

    data, samplerate = sf.read(wav_path, dtype="float32")
    device_idx = get_realtek_device_index()
    sd.play(data, samplerate, device=device_idx)
    sd.wait()

    os.unlink(wav_path)
    os.unlink(tmp_path)


def open_apps():
    # Spotify — open app, load playlist, press play
    if os.path.exists(config.SPOTIFY_EXE):
        subprocess.Popen([config.SPOTIFY_EXE])
        time.sleep(5)
    subprocess.run(
        ["powershell", "-c", f"Start-Process '{config.SPOTIFY_PLAYLIST_URI}'"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    time.sleep(3)
    subprocess.run(
        ["powershell", "-c",
         "$wshell = New-Object -ComObject wscript.shell; "
         "$wshell.AppActivate('Spotify'); "
         "Start-Sleep 1; "
         "$wshell.SendKeys(' ')"],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # LibreWolf
    if os.path.exists(config.LIBREWOLF_EXE):
        subprocess.Popen([config.LIBREWOLF_EXE])

    # Discord
    if os.path.exists(config.DISCORD_EXE):
        subprocess.Popen([config.DISCORD_EXE, "--processStart", "Discord.exe"])

    # Claude Code (optional) — CREATE_NEW_CONSOLE required because jarvis.py
    # runs headless (via VBS with window style 0), so children inherit no console.
    if config.CLAUDECODE_DIR:
        subprocess.Popen(
            ["powershell.exe", "-NoExit", "-Command",
             f"Set-Location '{config.CLAUDECODE_DIR}'; claude --dangerously-skip-permissions"],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )


async def main():
    weather = get_weather()
    headline = get_headline()
    message = build_message(weather, headline)
    open_apps()
    await speak(message)


if __name__ == "__main__":
    asyncio.run(main())
