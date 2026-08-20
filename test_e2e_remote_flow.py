import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))

os.environ["CAPCAP_RUNTIME_PROFILE"] = "remote"
os.environ["CAPCAP_REMOTE_API_URL"] = "http://127.0.0.1:8765"
os.environ["CAPCAP_REMOTE_API_TOKEN"] = "test_token"

from app.runtime_profile import is_remote_profile
print("is_remote_profile():", is_remote_profile())
assert is_remote_profile() == True, "Profile must be remote!"

from app.services.resource_download_service import ResourceDownloadService
rds = ResourceDownloadService(PROJECT_ROOT)
issues = rds.validate_pipeline_runtime()
print("validate_pipeline_runtime issues count:", len(issues))

from app.workflows.prepare_workflow import PrepareWorkflow
pw = PrepareWorkflow(PROJECT_ROOT)
print("PrepareWorkflow instantiated successfully in remote mode.")

print("\n--- ALL PRE-CHECKS PASSED ---")
