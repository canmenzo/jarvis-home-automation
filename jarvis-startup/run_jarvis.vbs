' Runs jarvis.py silently on Windows startup (no console window).
' Place this file in:
'   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
'
' Edit the path below to match where you cloned the repo.
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python C:\path\to\jarvis-home-automation\jarvis-startup\jarvis.py", 0, False
