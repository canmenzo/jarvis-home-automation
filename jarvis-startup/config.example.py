# Copy this file to config.py and fill in your values.
# config.py is gitignored — never commit it.

# TTS voice settings
VOICE = "en-GB-RyanNeural"   # edge-tts voice name
RATE = "-5%"
PITCH = "-10Hz"

# Audio output device (partial match, case-sensitive)
# Run: python -c "import sounddevice as sd; print(sd.query_devices())" to list devices
AUDIO_DEVICE = "Speakers (Realtek(R) Audio)"

# Weather location (open-meteo.com coordinates)
# Find your lat/lon at: https://open-meteo.com/
WEATHER_LAT = 0.0000
WEATHER_LON = 0.0000
WEATHER_CITY = "Your City"

# Spotify
# Your Spotify URI — right-click a song/playlist → Share → Copy Spotify URI
SPOTIFY_PLAYLIST_URI = "spotify:track:39shmbIHICJ2Wxnk1fPSdz"  # Iron Man OST — Driving With the Top Down

# App paths — adjust to your username / install location
SPOTIFY_EXE = r"C:\Users\YOUR_USERNAME\AppData\Roaming\Spotify\Spotify.exe"
LIBREWOLF_EXE = r"C:\Program Files\LibreWolf\librewolf.exe"
DISCORD_EXE = r"C:\Users\YOUR_USERNAME\AppData\Local\Discord\Update.exe"

# Startup working directory for Claude Code (optional, leave empty string to skip)
CLAUDECODE_DIR = r"C:\Users\YOUR_USERNAME\Documents\claudecode"
