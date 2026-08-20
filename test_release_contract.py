"""Release-facing checks for remote execution, notebooks, and one-file packaging.

Run with the release virtual environment:
    venv_final\Scripts\python.exe test_release_contract.py
"""

from __future__ import annotations

import ast
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT / "app"
sys.path[:0] = [str(ROOT), str(APP_ROOT)]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _parse_all_project_python() -> None:
    skipped = {".git", "build", "dist", "release", "venv_build", "venv_final", "venv_py311", "venv_py311_clean", "__pycache__"}
    files = [path for path in ROOT.rglob("*.py") if not (set(path.parts) & skipped)]
    failures = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    assert not failures, "\n".join(failures)
    print(f"[OK] Parsed {len(files)} project Python files.")


def _validate_notebooks_and_onefile_spec() -> None:
    all_in_one = json.loads((ROOT / "colab" / "CapCap_All_in_One_Colab.ipynb").read_text(encoding="utf-8"))
    whisper_only = json.loads((ROOT / "colab" / "CapCap_Whisper_Colab.ipynb").read_text(encoding="utf-8"))
    all_source = "".join("".join(cell.get("source", [])) for cell in all_in_one["cells"])
    whisper_source = "".join("".join(cell.get("source", [])) for cell in whisper_only["cells"])

    assert 'env_vars["CAPCAP_RUNTIME_PROFILE"] = "local"' in all_source
    assert 'env_vars["CAPCAP_DEVICE"] = "cuda"' in all_source
    assert 'env_vars.pop("CAPCAP_REMOTE_API_URL", None)' in all_source
    assert '"capabilities": ["transcribe"]' in whisper_source
    assert "Mở file `.env`" not in whisper_source

    for cell in all_in_one["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        source = "\n".join("pass" if line.lstrip().startswith(("!", "%")) else line for line in source.splitlines())
        compile(source, "CapCap_All_in_One_Colab.ipynb", "exec")
    for cell in whisper_only["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        source = "\n".join("pass" if line.lstrip().startswith(("!", "%")) else line for line in source.splitlines())
        compile(source, "CapCap_Whisper_Colab.ipynb", "exec")

    spec = (ROOT / "CapCap.spec").read_text(encoding="utf-8-sig")
    build_script = (ROOT / "build_final_clean.bat").read_text(encoding="utf-8-sig")
    assert "COLLECT(" not in spec
    assert "a.binaries," in spec and "a.zipfiles," in spec and "a.datas," in spec
    assert "set \"RELEASE_DIR=%PROJECT_ROOT%release\"" in build_script
    assert "--distpath \"%RELEASE_DIR%\"" in build_script
    assert "%RELEASE_DIR%\\CapCap.exe" in build_script
    print("[OK] Notebook JSON/code and one-file packaging contract validated.")


class _FakeColabHandler(BaseHTTPRequestHandler):
    calls: list[tuple[str, dict]] = []

    def log_message(self, _format, *_args):
        return

    def _write_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assert self.path == "/health"
        self._write_json({
            "ok": True,
            "profile": "local",
            "capabilities": ["transcribe", "translate", "rewrite", "tts", "separate_vocals"],
        })

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        type(self).calls.append((self.path, payload))
        if self.path == "/v1/transcribe":
            self._write_json({"ok": True, "segments": [{"start": 0.0, "end": 1.0, "text": "hello"}]})
            return
        if self.path == "/v1/tts/synthesize":
            self._write_json({"ok": True, "audio_b64": base64.b64encode(b"RIFFmock-wave").decode("ascii")})
            return
        if self.path == "/v1/separate-vocals":
            self._write_json({
                "ok": True,
                "vocals_b64": base64.b64encode(b"vocals").decode("ascii"),
                "background_b64": base64.b64encode(b"background").decode("ascii"),
            })
            return
        raise AssertionError(f"Unexpected endpoint: {self.path}")


def _exercise_remote_adapters() -> None:
    from services.engine_runtime import EngineRuntime

    port = _free_port()
    _FakeColabHandler.calls.clear()
    server = ThreadingHTTPServer(("127.0.0.1", port), _FakeColabHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    previous_env = {key: os.environ.get(key) for key in ("CAPCAP_RUNTIME_PROFILE", "CAPCAP_REMOTE_API_URL", "CAPCAP_REMOTE_API_TOKEN")}
    try:
        thread.start()
        os.environ["CAPCAP_RUNTIME_PROFILE"] = "remote"
        os.environ["CAPCAP_REMOTE_API_URL"] = f"http://127.0.0.1:{port}"
        os.environ["CAPCAP_REMOTE_API_TOKEN"] = "test-token"
        engine = EngineRuntime()
        assert type(engine.whisper).__name__ == "RemoteWhisperAdapter"
        assert type(engine.tts).__name__ == "RemoteTTSAdapter"
        assert type(engine.demucs).__name__ == "RemoteVocalAdapter"

        with tempfile.TemporaryDirectory(prefix="capcap_contract_") as temp_dir:
            source = Path(temp_dir) / "input.wav"
            source.write_bytes(b"audio-input")
            segments = engine.transcribe_audio(str(source), "base", language="en-US")
            assert segments[0]["text"] == "hello"
            tts_path = Path(temp_dir) / "voice.wav"
            assert engine.synthesize_segment(text="Xin chao", wav_path=str(tts_path), voice="edge:vi-VN-HoaiMyNeural") == str(tts_path)
            assert tts_path.read_bytes() == b"RIFFmock-wave"
            vocals_path, background_path = engine.separate_vocals(str(source), str(Path(temp_dir) / "output"))
            assert Path(vocals_path).read_bytes() == b"vocals"
            assert Path(background_path).read_bytes() == b"background"

        endpoints = [path for path, _payload in _FakeColabHandler.calls]
        assert endpoints == ["/v1/transcribe", "/v1/tts/synthesize", "/v1/separate-vocals"]
        transcribe_payload = _FakeColabHandler.calls[0][1]
        assert transcribe_payload["language"] == "en"
        print("[OK] Whisper, TTS, and vocal separation all route to the remote API.")
    finally:
        server.shutdown()
        server.server_close()
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _verify_remote_server_forces_local_profile() -> None:
    port = _free_port()
    env = os.environ.copy()
    env.update({
        "CAPCAP_RUNTIME_PROFILE": "remote",
        "CAPCAP_REMOTE_API_URL": "https://client.example.invalid",
        "CAPCAP_REMOTE_API_PORT": str(port),
        "CAPCAP_REMOTE_API_HOST": "127.0.0.1",
        "CAPCAP_REMOTE_PRELOAD_MODELS": "0",
        "CAPCAP_QUIET": "1",
    })
    process = subprocess.Popen(
        [sys.executable, str(APP_ROOT / "remote_api_server.py")],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 12
        payload = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except OSError:
                time.sleep(0.2)
        if payload is None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"Remote API server did not start. Output:\n{output}")
        assert payload["profile"] == "local"
        assert "separate_vocals" in payload["capabilities"]
        print("[OK] Remote API server isolates itself from the desktop remote profile.")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _smoke_test_frozen_exe() -> None:
    """Assert that the one-file executable can extract and keep its Qt app alive."""
    executable = ROOT / "release" / "CapCap.exe"
    assert executable.is_file(), f"Missing one-file release executable: {executable}"
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    startup_info = None
    if os.name == "nt":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = 0
    process = subprocess.Popen(
        [str(executable)],
        cwd=str(executable.parent),
        env=env,
        startupinfo=startup_info,
    )
    try:
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.5)
        if process.poll() is not None:
            raise AssertionError(f"CapCap.exe stopped during startup with exit code {process.returncode}.")
        print("[OK] One-file CapCap.exe started successfully in headless smoke mode.")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main() -> None:
    _parse_all_project_python()
    _validate_notebooks_and_onefile_spec()
    _exercise_remote_adapters()
    _verify_remote_server_forces_local_profile()
    if "--smoke-exe" in sys.argv:
        _smoke_test_frozen_exe()
    print("ALL RELEASE CONTRACT CHECKS PASSED")


if __name__ == "__main__":
    main()
