@echo off
"C:\Users\Nguyen Trong Khoi\anaconda3\python.exe" -m venv venv_build
venv_build\Scripts\pip install PySide6 pyinstaller websockets requests yt-dlp python-mpv python-dotenv
venv_build\Scripts\pyinstaller -y CapCap.spec
