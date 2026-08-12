' Launches jarvis.py with no visible window. Self-locating: it runs the jarvis.py
' sitting next to it, so put a SHORTCUT to this file in shell:startup rather than a
' copy — a copy silently drifts from the repo version.
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

here = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = here
shell.Run "python """ & fso.BuildPath(here, "jarvis.py") & """", 0, False
