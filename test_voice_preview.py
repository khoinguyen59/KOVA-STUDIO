import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))

from services.engine_runtime import EngineRuntime

def test_voice_preview():
    print(f"Current profile: is_remote={EngineRuntime()._remote_profile}")
    engine = EngineRuntime()
    try:
        tmp_dir = os.path.join(PROJECT_ROOT, "temp", "test_voice")
        os.makedirs(tmp_dir, exist_ok=True)
        wav_path = os.path.join(tmp_dir, "test_sample.wav")
        if os.path.exists(wav_path):
            os.remove(wav_path)
        print("Calling engine.synthesize_segment for voice 'ngochuyen'...")
        engine.synthesize_segment(
            text="Chào bạn, đây là bản xem trước giọng nói của mẫu được chọn.",
            wav_path=wav_path,
            voice="ngochuyen",
            speed=1.0,
            tmp_dir=tmp_dir,
        )
        print(f"Generated WAV exists: {os.path.exists(wav_path)}, size: {os.path.getsize(wav_path) if os.path.exists(wav_path) else 0}")
    except Exception as exc:
        print("VOICE PREVIEW FAILED WITH EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    test_voice_preview()
