@echo off
py -3.11 -m venv venv_py311
venv_py311\Scripts\pip install PySide6 pyinstaller websockets requests yt-dlp python-mpv python-dotenv
venv_py311\Scripts\pyinstaller -y CapCap.spec
