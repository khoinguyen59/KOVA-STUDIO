@echo off
py -3.11 -m venv venv_final
venv_final\Scripts\pip install PySide6 pyinstaller websockets requests yt-dlp python-mpv python-dotenv openai shapely omegaconf pyclipper google-generativeai
venv_final\Scripts\pyinstaller -y CapCap.spec
