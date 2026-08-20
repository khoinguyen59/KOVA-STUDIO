import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))

os.environ["CAPCAP_RUNTIME_PROFILE"] = "remote"
os.environ["CAPCAP_REMOTE_API_URL"] = "http://127.0.0.1:8765"

from services.project_service import ProjectService
from workflows.voice_workflow import VoiceWorkflow
from workflows.prepare_workflow import PrepareWorkflow

ps = ProjectService(PROJECT_ROOT)
proj_path = os.path.join(PROJECT_ROOT, "dist", "CapCap", "projects", "1_e8789095", "project.json")
if os.path.exists(proj_path):
    state = ps.load_project(proj_path)
    print("Project loaded:", state.project_id)
    print("Steps:", state.steps)
    print("Artifacts:", state.artifacts)
else:
    print("Project path does not exist:", proj_path)
