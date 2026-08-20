import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def run_gui_verification():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    from ui.main_window import VideoTranslatorGUI
    print("Instantiating VideoTranslatorGUI...")
    gui = VideoTranslatorGUI()
    gui.prepare_initial_editor_layout()
    gui.show()
    print("GUI successfully instantiated and shown!")

    # Test 1: Project Name Edit existence and functionality
    assert hasattr(gui, "project_name_edit"), "project_name_edit missing on gui"
    gui.project_name_edit.setText("Test Project 1")
    gui.on_project_name_changed("Test Project 1")
    print("Project Name Edit working!")

    # Test 2: Audio Volume and Mute methods
    gui.on_audio_a1_volume_changed(40)
    gui.on_audio_a2_volume_changed(80)
    gui.on_track_mute_toggled("A1 Audio", True)
    assert gui._is_audio_track_muted("A1 Audio") == True
    gui.on_track_mute_toggled("A1 Audio", False)
    assert gui._is_audio_track_muted("A1 Audio") == False
    print("Audio volume and mute methods working without any error!")

    # Test 3: Project Service unique project creation
    video_path = os.path.join(PROJECT_ROOT, "temp_test_chinese.mp4")
    if not os.path.exists(video_path):
        with open(video_path, "wb") as f:
            f.write(b"0")
    gui._current_video_path = os.path.abspath(video_path)
    gui.video_path_edit.setText(video_path)
    p = gui.ensure_current_project()
    assert p is not None, "ensure_current_project returned None"
    gui.load_project_context(p)
    print(f"Project context loaded successfully: {p.project_name}")

    gui.close()
    print("ALL GUI INTEGRATION & STARTUP TESTS PASSED 100%!")

if __name__ == "__main__":
    run_gui_verification()
