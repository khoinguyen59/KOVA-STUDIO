"""Release-facing checks for remote execution, notebooks, and one-file packaging.

Run with the release virtual environment:
    venv_final\Scripts\python.exe test_release_contract.py
"""

from __future__ import annotations

import ast
import base64
import inspect
import json
import os
from pathlib import Path
import shutil
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
    assert 'UVR-MDX-NET-Inst_HQ_3.onnx' in all_source
    assert 'models/MDXNet/UVR-MDX-NET-Inst_HQ_3.onnx?download=true' in all_source
    assert '317554b07fe1ea5279a77f2b1520a41ea4b93432560c4ffd08792c30fddf9adc' in all_source
    assert 'sha256_file(download_path)' in all_source
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
    assert 'collect_dynamic_libs("numpy")' in spec
    assert '"numpy.libs"' in spec
    assert "set \"RELEASE_DIR=%PROJECT_ROOT%release\"" in build_script
    assert "--distpath \"%RELEASE_DIR%\"" in build_script
    assert "%RELEASE_DIR%\\CapCap.exe" in build_script

    desktop_settings = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8-sig")
    assert "CapCap_All_in_One_Colab.ipynb" in desktop_settings
    assert "CapCap_Whisper_Colab.ipynb" not in desktop_settings
    assert "All-in-One Colab" in desktop_settings

    prepare_source = (ROOT / "app" / "workflows" / "prepare_workflow.py").read_text(encoding="utf-8-sig")
    manual_subtitle_source = (ROOT / "ui" / "controllers" / "subtitle_controller.py").read_text(encoding="utf-8-sig")
    preview_source = (ROOT / "ui" / "controllers" / "preview_controller.py").read_text(encoding="utf-8-sig")
    assert 'build_path(project_state, "subtitle", "original.srt")' in prepare_source
    assert 'build_path(state, "subtitle", "original.srt")' in manual_subtitle_source
    assert "separate_vocals(audio_output_path" in prepare_source
    assert "_resolve_preview_background_audio_path" in preview_source
    assert "mix_original_with_dub(" in preview_source
    tts_source = (ROOT / "app" / "tts_processor.py").read_text(encoding="utf-8-sig")
    assert 'shutil.which("ffmpeg")' in tts_source
    assert "apt-get install -y -qq ffmpeg" in all_source
    print("[OK] Notebook JSON/code and one-file packaging contract validated.")


def _verify_qthread_result_lifecycle() -> None:
    """Ensure result signals never shadow QThread.finished again."""
    worker_sources = [
        ROOT / "ui" / "worker_adapters" / "processing_workers.py",
        ROOT / "ui" / "worker_adapters" / "preview_workers.py",
    ]
    violations = []
    for source_path in worker_sources:
        module = ast.parse(source_path.read_text(encoding="utf-8-sig"), filename=str(source_path))
        for class_node in (node for node in ast.walk(module) if isinstance(node, ast.ClassDef)):
            inherits_qthread = any(
                (isinstance(base, ast.Name) and base.id == "QThread")
                or (isinstance(base, ast.Attribute) and base.attr == "QThread")
                for base in class_node.bases
            )
            if not inherits_qthread:
                continue
            for statement in class_node.body:
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target] if isinstance(statement, ast.AnnAssign) else []
                if any(isinstance(target, ast.Name) and target.id == "finished" for target in targets):
                    violations.append(f"{source_path.relative_to(ROOT)}:{class_node.name}")
    assert not violations, "QThread.finished must remain the native Qt lifecycle signal: " + ", ".join(violations)

    from PySide6.QtCore import QCoreApplication, QTimer
    from ui.worker_adapters.processing_workers import TimelineWaveformWorker

    app = QCoreApplication.instance() or QCoreApplication([])
    results = []
    native_finished = []
    worker = TimelineWaveformWorker("contract", "", "", "")
    worker.result_ready.connect(lambda *args: results.append(args))
    worker.finished.connect(lambda: (native_finished.append(True), app.quit()))
    worker.start()
    QTimer.singleShot(5000, app.quit)
    app.exec()
    assert worker.wait(1000), "TimelineWaveformWorker did not stop cleanly."
    assert results == [("contract", [], 0.0, "")]
    assert native_finished == [True]
    print("[OK] QThread result/native-finished lifecycle validated.")


def _verify_all_in_one_colab_preflight() -> None:
    """Voice projects must reject a Whisper-only server before work begins."""
    ui_root = ROOT / "ui"
    if str(ui_root) not in sys.path:
        sys.path.insert(0, str(ui_root))
    from ui.controllers.pipeline_controller import PipelineController

    class _CapabilityGui:
        def __init__(self, mode: str):
            self.mode = mode

        def get_output_mode_key(self) -> str:
            return self.mode

    subtitle = PipelineController(_CapabilityGui("subtitle"))
    voice = PipelineController(_CapabilityGui("voice"))
    both = PipelineController(_CapabilityGui("both"))
    assert subtitle.required_colab_capabilities("transcript") == ("transcribe",)
    assert voice.required_colab_capabilities("transcript") == ("transcribe", "tts")
    assert both.required_colab_capabilities("translate", True) == (
        "transcribe", "translate", "separate_vocals", "tts"
    )

    main_window_source = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8-sig")
    voiceover_section = main_window_source.split("def run_voiceover_with_progress", 1)[1].split(
        "def run_pipeline_to_stage", 1
    )[0]
    assert 'ensure_colab_connection("Voice generation", ("tts",))' in voiceover_section
    print("[OK] Voice/Both flows require the All-in-One Colab capability set before work starts.")


def _verify_independent_stt_ocr_sources() -> None:
    """The external-editor workflow must keep STT and OCR SRTs separate."""
    prepare_source = (APP_ROOT / "workflows" / "prepare_workflow.py").read_text(encoding="utf-8-sig")
    pipeline_source = (ROOT / "ui" / "controllers" / "pipeline_controller.py").read_text(encoding="utf-8-sig")
    main_window_source = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8-sig")
    display_source = (ROOT / "ui" / "utils" / "display_utils.py").read_text(encoding="utf-8-sig")

    assert 'is_stt_ocr = transcription_engine == "stt_ocr"' in prepare_source
    assert "skip_translation = bool(skip_translation or is_stt_ocr)" in prepare_source
    assert '"original_stt.srt"' in prepare_source
    assert '"original_ocr.srt"' in prepare_source
    assert '"subtitle_original_stt_srt"' in prepare_source
    assert '"subtitle_original_ocr_srt"' in prepare_source
    assert "self.engine_runtime.transcribe_video_ocr(" in prepare_source
    assert "if is_stt_ocr:" in prepare_source
    assert "return project_state" in prepare_source

    assert 'is_independent_stt_ocr = transcription_engine == "stt_ocr"' in pipeline_source
    assert 'effective_target_stage = "transcript" if is_independent_stt_ocr else target_stage' in pipeline_source
    assert "No automatic merge or translation was run." in pipeline_source
    assert '"stt_ocr"' in main_window_source
    assert "Import Translated Subtitle" in main_window_source
    assert "Independent STT SRT" in display_source
    assert "Independent OCR SRT" in display_source
    print("[OK] Independent STT/OCR source SRT workflow and external-import hand-off validated.")


def _exercise_independent_stt_ocr_workflow() -> None:
    """Run the dual-source branch with fake engines, never real AI workloads."""
    from workflows.prepare_workflow import PrepareWorkflow

    class _DualSourceRuntime:
        def __init__(self):
            self.calls: list[str] = []

        def extract_audio(self, _video_path: str, audio_path: str) -> bool:
            Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
            Path(audio_path).write_bytes(b"fake-audio")
            return True

        def transcribe_audio(self, _audio_path: str, _model: str, *, language: str):
            self.calls.append(f"stt:{language}")
            return [{"start": 0.0, "end": 1.0, "text": "spoken source"}]

        def transcribe_video_ocr(self, _video_path: str, *, region: str):
            self.calls.append(f"ocr:{region}")
            return [{"start": 0.1, "end": 1.1, "text": "visible text"}]

        def generate_srt(self, segments, output_path: str) -> str:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            text = "\n".join(str(segment.get("text", "")) for segment in segments)
            Path(output_path).write_text(text, encoding="utf-8")
            return output_path

    previous_env = {
        key: os.environ.get(key)
        for key in ("CAPCAP_RUNTIME_PROFILE", "CAPCAP_REMOTE_API_URL", "CAPCAP_REMOTE_API_TOKEN")
    }
    try:
        os.environ["CAPCAP_RUNTIME_PROFILE"] = "remote"
        os.environ["CAPCAP_REMOTE_API_URL"] = "http://contract.invalid"
        os.environ["CAPCAP_REMOTE_API_TOKEN"] = "contract-token"
        with tempfile.TemporaryDirectory(prefix="capcap_dual_sources_") as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            video_path.write_bytes(b"fake-video")
            workflow = PrepareWorkflow(temp_dir)
            fake_runtime = _DualSourceRuntime()
            workflow.engine_runtime = fake_runtime
            workflow._prepare_asr_working_audio = lambda audio_path, _state: audio_path
            workflow.chunking_service.probe_wav_duration = lambda _audio_path: 1.0

            state = workflow.run(
                str(video_path),
                mode="voice",
                transcription_engine="stt_ocr",
                source_language="en",
                skip_translation=False,
            )
            stt_path = Path(state.artifacts["subtitle_original_stt_srt"])
            ocr_path = Path(state.artifacts["subtitle_original_ocr_srt"])
            assert fake_runtime.calls == ["stt:en", "ocr:bottom"]
            assert stt_path.is_file() and stt_path.read_text(encoding="utf-8") == "spoken source"
            assert ocr_path.is_file() and ocr_path.read_text(encoding="utf-8") == "visible text"
            assert state.artifacts.get("subtitle_translated_srt", "") == ""
            assert state.steps.get("translate_raw") == "skipped"
            assert state.settings.get("external_translation_required") is True
        print("[OK] Dual STT/OCR workflow produced two source SRTs without translation or TTS.")
    finally:
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _verify_timed_cues_and_tts_failure_guard() -> None:
    """Regression coverage for the reproduced giant-subtitle/silent-TTS bug."""
    from services.segment_service import SegmentService
    from workflows.voice_workflow import VoiceWorkflow
    import wave

    raw_segments = [
        {
            "start": 0.0,
            "end": 12.0,
            "text": "long recognition segment",
            "words": [
                {"start": float(index), "end": float(index + 1), "text": chr(0x4E00 + index)}
                for index in range(12)
            ],
        },
        {
            # Starts before the previous ASR segment ends: normalized output
            # must never emit overlapping visual/TTS cues.
            "start": 10.5,
            "end": 14.0,
            "text": "overlap",
            "words": [
                {"start": 10.5, "end": 11.0, "text": "續"},
                {"start": 11.0, "end": 12.0, "text": "篇"},
            ],
        },
    ]
    cues = SegmentService().normalize_transcript_cues(raw_segments)
    assert len(cues) >= 3
    assert max(cue["end"] - cue["start"] for cue in cues) <= 5.25
    assert all(cues[index]["start"] >= cues[index - 1]["end"] for index in range(1, len(cues)))
    assert all(cue["words"] for cue in cues)

    class _SilentTtsRuntime:
        def synthesize_segment(self, *, wav_path: str, **_kwargs):
            with wave.open(wav_path, "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                handle.writeframes(b"\x00\x00" * 1600)
            return wav_path

    with tempfile.TemporaryDirectory(prefix="capcap_tts_failure_guard_") as temp_dir:
        workflow = VoiceWorkflow(temp_dir)
        workflow.engine_runtime = _SilentTtsRuntime()
        workflow._voice_provider = lambda _voice_name: "edge"
        try:
            workflow._synthesize_segment_wavs(
                segments=[{"start": 0.0, "end": 1.0, "text": "Xin chao"}],
                tmp_dir=temp_dir,
                voice_name="edge:vi-VN-HoaiMyNeural",
            )
        except RuntimeError as exc:
            assert "No silent placeholder" in str(exc)
        else:
            raise AssertionError("Silent TTS output must fail instead of reaching export.")

    class _RetryTtsRuntime:
        def __init__(self):
            self.calls: list[str] = []

        def synthesize_segment(self, *, text: str, wav_path: str, **_kwargs):
            self.calls.append(text)
            with wave.open(wav_path, "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                # A non-silent 0.95-second candidate: close enough to a one
                # second cue and therefore preferable to the 2-second input.
                handle.writeframes((b"\x00\x20" * int(16000 * 0.95)))
            return wav_path

    with tempfile.TemporaryDirectory(prefix="capcap_tts_retry_guard_") as temp_dir:
        initial_wav = Path(temp_dir) / "seg_0000_base.wav"
        with wave.open(str(initial_wav), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(16000)
            handle.writeframes(b"\x00\x20" * int(16000 * 2.0))

        retry_runtime = _RetryTtsRuntime()
        workflow = VoiceWorkflow(temp_dir)
        workflow.engine_runtime = retry_runtime
        workflow._voice_provider = lambda _voice_name: "edge"
        segments = [{
            "start": 0.0,
            "end": 1.0,
            "text": "mot hai ba bon nam sau bay tam chin muoi muoi mot muoi hai",
            "source_text": "mot hai ba bon nam sau bay tam chin muoi muoi mot muoi hai",
            "tts_text": "mot hai ba bon nam sau bay tam chin muoi muoi mot muoi hai",
            "_tts_metrics": {"max_words_vi": 4, "speech_cost": 0, "retry_cap": 2},
        }]
        retried_wavs = workflow._retry_overlong_segments(
            segments=segments,
            wavs=[str(initial_wav)],
            tmp_dir=temp_dir,
            voice_name="edge:vi-VN-HoaiMyNeural",
            provider_speed=1.0,
            voice_provider="edge",
        )
        assert retry_runtime.calls, "An overlong TTS cue must trigger a retry synthesis."
        assert retried_wavs[0] != str(initial_wav)
        assert workflow._probe_wav_duration_seconds(retried_wavs[0]) < 1.0
        assert segments[0]["_tts_metrics"]["retry_applied"] is True

    print("[OK] Long ASR segments split into non-overlapping cues; silent TTS blocks export; overlong TTS retries.")


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


def _remove_tree_with_retry(path: str, *, timeout_seconds: float = 12.0) -> None:
    """Remove a PyInstaller extraction tree after Windows releases its DLL handles."""
    deadline = time.monotonic() + timeout_seconds
    last_error: OSError | None = None
    while Path(path).exists():
        try:
            shutil.rmtree(path)
            return
        except OSError as exc:
            last_error = exc
            if time.monotonic() >= deadline:
                break
            time.sleep(0.25)
    if Path(path).exists():
        raise AssertionError(f"Could not remove isolated frozen-EXE temp directory: {path}") from last_error


def _smoke_test_frozen_exe() -> None:
    """Verify one-file extraction, MPV availability, startup, and temp cleanup."""
    executable = ROOT / "release" / "CapCap.exe"
    assert executable.is_file(), f"Missing one-file release executable: {executable}"
    startup_info = None
    if os.name == "nt":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = 0
    minimum_free_bytes = int(os.environ.get("CAPCAP_FROZEN_MIN_FREE_BYTES", str(1_500_000_000)))

    extraction_root = tempfile.mkdtemp(prefix="capcap_frozen_extraction_")
    try:
        available_bytes = shutil.disk_usage(extraction_root).free
        assert available_bytes >= minimum_free_bytes, (
            "Insufficient free space for a one-file CapCap smoke test: "
            f"need at least {minimum_free_bytes:,} bytes, found {available_bytes:,}."
        )

        env = os.environ.copy()
        env["CAPCAP_HEADLESS"] = "1"
        env["QT_QPA_PLATFORM"] = "offscreen"
        # PyInstaller reads TEMP/TMP before app code runs. Isolating them makes
        # the test verify actual extraction without leaving _MEI folders in the
        # user's normal Temp directory when the one-file process tree is ended.
        env["TEMP"] = extraction_root
        env["TMP"] = extraction_root
        process = subprocess.Popen([str(executable)], cwd=str(executable.parent), env=env, startupinfo=startup_info)
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline and process.poll() is None:
                time.sleep(0.5)
            if process.poll() is not None:
                raise AssertionError(f"CapCap.exe stopped during startup with exit code {process.returncode}.")

            extracted_mpv = list(Path(extraction_root).glob("_MEI*/bin/mpv/libmpv-2.dll"))
            assert len(extracted_mpv) == 1, "CapCap.exe did not extract the bundled MPV DLL."
            mpv_size = extracted_mpv[0].stat().st_size
            assert mpv_size >= 100 * 1024 * 1024, (
                f"Extracted MPV DLL is incomplete: expected >= 100 MiB, found {mpv_size:,} bytes."
            )
            print("[OK] One-file CapCap.exe extracted MPV and started successfully in isolated headless smoke mode.")
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    # One-file PyInstaller starts a parent bootloader and a child
                    # GUI process. End the whole tree before the test removes
                    # its isolated _MEI extraction folder.
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    finally:
        _remove_tree_with_retry(extraction_root)


def _verify_frozen_exe_smoke_hygiene_contract() -> None:
    """Keep the one-file smoke test from leaking large PyInstaller temp trees."""
    source = inspect.getsource(_smoke_test_frozen_exe)
    module_source = Path(__file__).read_text(encoding="utf-8-sig")
    assert "def _remove_tree_with_retry" in module_source
    assert 'mkdtemp(prefix="capcap_frozen_extraction_")' in source
    assert 'env["TEMP"] = extraction_root' in source
    assert 'env["TMP"] = extraction_root' in source
    assert 'glob("_MEI*/bin/mpv/libmpv-2.dll")' in source
    assert "CAPCAP_FROZEN_MIN_FREE_BYTES" in source
    assert "_remove_tree_with_retry(extraction_root)" in source
    print("[OK] Frozen-EXE smoke test contract requires isolated extraction and MPV verification.")


def main() -> None:
    _parse_all_project_python()
    _validate_notebooks_and_onefile_spec()
    _verify_qthread_result_lifecycle()
    _verify_all_in_one_colab_preflight()
    _verify_independent_stt_ocr_sources()
    _exercise_independent_stt_ocr_workflow()
    _verify_timed_cues_and_tts_failure_guard()
    _exercise_remote_adapters()
    _verify_remote_server_forces_local_profile()
    _verify_frozen_exe_smoke_hygiene_contract()
    if "--smoke-exe" in sys.argv:
        _smoke_test_frozen_exe()
    print("ALL RELEASE CONTRACT CHECKS PASSED")


if __name__ == "__main__":
    main()
