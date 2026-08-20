# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import os
import glob as _glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_root = Path(SPECPATH)
ui_root = project_root / "ui"
app_root = project_root / "app"

_datas_raw = [
    (project_root / "assets", "assets"),
    (project_root / "bin" / "ffmpeg", "bin/ffmpeg"),
    (project_root / "bin" / "mpv", "bin/mpv"),
    (project_root / "app" / "voice_preview_catalog.json", "app"),
    (project_root / "app" / "voice_download_catalog.json", "app"),
    (project_root / "app" / "voice_preview_catalog.release.json", "app"),
    (project_root / "app" / "utils", "app/utils"),
    (project_root / "app" / "utils", "utils"),
    (project_root / ".env_example", "."),
    (project_root / "ui" / "views" / "editor", "views/editor"),
    (project_root / "ui" / "views" / "editor", "ui/views/editor"),
    (project_root / "colab", "colab"),
]

datas = [(str(src), dst) for src, dst in _datas_raw if src.exists()]
rapidocr_hiddenimports = []

excludes = [
    "torch",
    "torchaudio",
    "torchvision",
    "demucs",
    "llama_cpp",
    "llama_cpp.*",
    "matplotlib",
    "PyQt5",
    "PyQt6",
    "skimage",
    "tensorflow",
    "keras",
    "pandas",
    "statsmodels",
    "IPython",
    "jupyter",
]


a = Analysis(
    [str(ui_root / "gui.py")],
    pathex=[str(project_root), str(ui_root), str(app_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "gui",
        "main_window",
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        "PySide6.QtMultimedia",
        "mpv",
        "remote_api",
        "remote_api_server",
        "services",
        "services.project_service",
        "services.gui_project_bridge",
        "services.voice_catalog_service",
        "services.resource_download_service",
        "services.engine_runtime",
        "services.workflow_runtime",
        "services.segment_service",
        "services.chunking_service",
        "services.asr_merge_service",
        "services.segment_regroup_service",
        # SpeakerDiarizationService is resolved lazily through services.__getattr__.
        # Include its concrete module so the frozen worker can import it.
        "services.speaker_diarization_service",
        # Dynamically loaded adapters (EngineRuntime uses importlib)
        "engines.ffmpeg_adapter",
        "engines.preview_adapter",
        "engines.subtitle_adapter",
        "engines.audio_mix_adapter",
        "engines.whisper_adapter",
        "engines.sensevoice_adapter",
        "engines.translator_adapter",
        "engines.tts_adapter",
        "engines.demucs_adapter",
        "engines.ocr_adapter",
        "engines.remote_whisper_adapter",
        "engines.remote_translator_adapter",
        "engines.remote_tts_adapter",
        "engines.remote_vocal_adapter",
        # Lazy-loaded translation providers
        "translation.providers.ai_polisher",
        "translation.providers.gemini_polisher",
        "translation.providers.google_web_translator",
        # Lazy-loaded workflows
        "workflows.prepare_workflow",
        "workflows.voice_workflow",
        "workflows.export_workflow",
        # Required for voice workflow
        "app.utils.voice_preview_utils",
        "utils.voice_preview_utils",
        # Required for timeline + audio
        "pydub",
        "aiohttp",
        "edge_tts",
        "dotenv",
        "huggingface_hub",
        "tts_processor",
        "preview_processor",
        "video_processor",
        "subtitle_builder",
        "runtime_paths",
        # Explicitly include the namespace-package module imported by the
        # timeline at runtime.  PyInstaller does not reliably discover
        # modules beneath the project-level ``app`` namespace automatically.
        "app.runtime_paths",
        "runtime_profile",
        "shapely",
        "omegaconf",
        "pyclipper",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

# Force-exclude heavy packages from final bundle
_EXCLUDE_PREFIXES = ("torch", "torchaudio", "torchvision", "demucs")
a.pure = [m for m in a.pure if not str(m[0]).replace("\\", "/").split("/")[0].split(".")[0] in _EXCLUDE_PREFIXES]
a.binaries = [m for m in a.binaries if not str(m[0]).replace("\\", "/").split("/")[0].split(".")[0] in _EXCLUDE_PREFIXES]
# PyInstaller can collect the same ONNX Runtime CUDA provider under a nested
# invalid destination as well as the normal capi directory. Keep only the
# normal provider copy; CUDA runtime DLLs are installed on demand by the
# Resource Manager, not bundled into the application.
a.binaries = [m for m in a.binaries if str(m[0]).replace("\\", "/") != "onnxruntime/capi/onnxruntime/capi/onnxruntime_providers_cuda.dll"]

# Do not silently turn the installer into a CUDA runtime installer. Native
# dependency analysis of CTranslate2 can discover these DLLs from the CUDA
# Toolkit installed on the build machine and place duplicate copies in
# ``_internal``. GPU mode intentionally resolves them from the separately
# downloadable ``bin/cuda12_fw`` resource directory instead. Keeping this
# exclusion explicit makes CPU-only installs small and keeps the Resource
# Manager as the single source for the GPU runtime.
_CUDA_RUNTIME_DLL_NAMES = {
    "cublas64_12.dll",
    "cublaslt64_12.dll",
    "cudart64_12.dll",
    "cufft64_11.dll",
}
a.binaries = [
    m for m in a.binaries
    if Path(str(m[0])).name.lower() not in _CUDA_RUNTIME_DLL_NAMES
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="CapCap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_dir=str(project_root / "upx"),
    console=False,
    icon=str(project_root / "assets" / "capcap.ico"),
    disable_windowed_traceback=False,
)
