import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))

from services.project_service import ProjectService
from core.state.project_state import ProjectState

def test_unique_projects():
    ps = ProjectService(PROJECT_ROOT)
    video_path = os.path.join(PROJECT_ROOT, "temp_test_chinese.mp4")
    if not os.path.exists(video_path):
        with open(video_path, "wb") as f:
            f.write(b"dummy")

    # 1. Create project 1 for video
    p1 = ps.create_new_project(video_path)
    print(f"Project 1 created: ID={p1.project_id}, Name={p1.project_name}, Root={p1.project_root}")
    assert p1.project_id, "Project 1 ID missing"
    assert p1.project_name, "Project 1 Name missing"
    assert os.path.exists(p1.project_root), "Project 1 directory missing"

    time.sleep(1.1)  # Ensure distinct timestamp

    # 2. Create project 2 for THE SAME video
    p2 = ps.create_new_project(video_path)
    print(f"Project 2 created: ID={p2.project_id}, Name={p2.project_name}, Root={p2.project_root}")
    assert p2.project_id, "Project 2 ID missing"
    assert p2.project_name, "Project 2 Name missing"
    assert os.path.exists(p2.project_root), "Project 2 directory missing"

    # Verify project 1 and project 2 are completely separate!
    assert p1.project_id != p2.project_id, f"Project IDs must be distinct! Got {p1.project_id} == {p2.project_id}"
    assert p1.project_root != p2.project_root, "Project roots must be distinct!"

    # 3. Edit project 1 name
    p1.set_name("Tập 1 - Phim Cổ Trang Vietsub")
    ps.save_project(p1)
    print(f"Project 1 renamed to: {p1.project_name}")

    # 4. Reload both and verify isolation
    reloaded_p1 = ps.load_project(ps.project_file(p1.project_root))
    reloaded_p2 = ps.load_project(ps.project_file(p2.project_root))

    assert reloaded_p1.project_name == "Tập 1 - Phim Cổ Trang Vietsub", "Project 1 name mismatch after reload"
    assert reloaded_p2.project_name != "Tập 1 - Phim Cổ Trang Vietsub", "Project 2 was erroneously modified"

    print("ALL UNIQUE PROJECT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_unique_projects()
