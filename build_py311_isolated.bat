@echo off
set "PATH=C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem"
py -3.11 -m venv venv_py311_clean
venv_py311_clean\Scripts\pip install PySide6 pyinstaller websockets requests yt-dlp python-mpv python-dotenv
venv_py311_clean\Scripts\pyinstaller -y CapCap.spec
