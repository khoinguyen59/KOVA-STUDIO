import ast
import glob
import importlib
import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

def audit_all_files():
    print("=" * 60)
    print("STAGE 1: AST SYNTAX AUDIT ON ALL PYTHON FILES")
    print("=" * 60)

    py_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "venv" in root or ".git" in root or "build" in root or "dist" in root or "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    syntax_errors = []
    for filepath in sorted(py_files):
        rel_path = os.path.relpath(filepath, PROJECT_ROOT)
        try:
            with open(filepath, "r", encoding="utf-8") as handle:
                code = handle.read()
            ast.parse(code, filename=filepath)
        except Exception as exc:
            print(f"[SYNTAX ERROR] {rel_path}: {exc}")
            syntax_errors.append((rel_path, str(exc)))

    if syntax_errors:
        print(f"FAILED: Found {len(syntax_errors)} syntax error(s)!")
        for path, err in syntax_errors:
            print(f"  - {path}: {err}")
        return False
    else:
        print(f"SUCCESS: All {len(py_files)} Python files parsed cleanly without syntax errors!")

    print("\n" + "=" * 60)
    print("STAGE 2: IMPORT AUDIT ON ALL APPLICATION MODULES")
    print("=" * 60)

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    modules_to_test = [
        "runtime_paths",
        "runtime_profile",
        "video_processor",
        "audio_mixer",
        "tts_processor",
        "whisper_processor",
        "subtitle_builder",
        "translator",
        "preview_processor",
        "services.project_service",
        "services.engine_runtime",
        "services.gui_project_bridge",
        "services.voice_catalog_service",
        "services.segment_service",
        "workflows.prepare_workflow",
        "workflows.voice_workflow",
        "workflows.export_workflow",
        "ui.views.main_window",
        "ui.views.start_panel",
        "ui.views.advanced_tabs",
        "ui.views.preview_panel",
        "ui.views.launcher",
        "ui.views.editor.timeline",
        "ui.views.editor.track_labels",
        "ui.controllers.pipeline_controller",
        "ui.controllers.preview_controller",
        "ui.controllers.subtitle_controller",
        "ui.utils.media_backend",
        "ui.worker_adapters.processing_workers",
        "ui.main_window",
    ]

    import_errors = []
    for mod_name in modules_to_test:
        try:
            mod = importlib.import_module(mod_name)
            print(f"  [OK] Imported module: {mod_name}")
        except Exception as exc:
            print(f"  [IMPORT ERROR] {mod_name}: {exc}")
            traceback.print_exc()
            import_errors.append((mod_name, str(exc)))

    if import_errors:
        print(f"FAILED: Found {len(import_errors)} module import error(s)!")
        return False
    else:
        print(f"SUCCESS: All {len(modules_to_test)} modules imported cleanly!")

    print("\n" + "=" * 60)
    print("STAGE 3: FULL GUI INSTANTIATION AND WIDGET TREE AUDIT")
    print("=" * 60)

    try:
        from ui.main_window import VideoTranslatorGUI
        gui = VideoTranslatorGUI()
        gui.prepare_initial_editor_layout()
        gui.show()
        print("  [OK] VideoTranslatorGUI instantiated and shown without errors.")

        # Test project creation, naming, volume, muting
        assert hasattr(gui, "project_name_edit"), "Missing project_name_edit"
        gui.project_name_edit.setText("Audit Project 2026")
        gui.on_project_name_changed("Audit Project 2026")
        print("  [OK] Project name edit signal verified.")

        gui.on_audio_a1_volume_changed(30)
        gui.on_audio_a2_volume_changed(75)
        gui.on_track_mute_toggled("A1 Audio", True)
        assert gui._is_audio_track_muted("A1 Audio") == True, "A1 Audio mute flag failed"
        gui.on_track_mute_toggled("A1 Audio", False)
        assert gui._is_audio_track_muted("A1 Audio") == False, "A1 Audio unmute flag failed"
        print("  [OK] Audio volume and mute logic verified.")

        gui.close()
        print("  [OK] GUI closed cleanly.")
    except Exception as exc:
        print(f"FAILED: GUI audit error: {exc}")
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("ALL 3 STAGES OF AUDIT PASSED 100% SUCCESSFULLY!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = audit_all_files()
    sys.exit(0 if success else 1)
