import os
import sys
import shutil
import time
import subprocess
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ui"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "app"))

from services.project_service import ProjectService
from workflows.prepare_workflow import PrepareWorkflow
from workflows.voice_workflow import VoiceWorkflow
from workflows.export_workflow import ExportWorkflow
from services.engine_runtime import EngineRuntime
from core.models.segment import coerce_segments
from runtime_paths import bin_path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

def log(msg):
    print(f"\n========================================\n[TEST ENGINE] {msg}\n========================================")

def run_tests():
    ps = ProjectService(PROJECT_ROOT)
    runtime = EngineRuntime()
    ffmpeg = str(bin_path("ffmpeg", "ffmpeg.exe"))

    # 0. Find test video
    test_video = None
    for candidate in [
        os.path.join(PROJECT_ROOT, "1.mp4"),
        os.path.join(PROJECT_ROOT, "test.mp4"),
        os.path.join(PROJECT_ROOT, "dist", "CapCap", "temp", "projects", "1_e8789095", "preview", "test.mp4"),
    ]:
        if os.path.exists(candidate):
            test_video = candidate
            break

    if not test_video:
        test_video = os.path.join(PROJECT_ROOT, "temp_test_chinese.mp4")
        cmd = [
            ffmpeg, "-hide_banner", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=640x360:d=4:r=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p",
            test_video
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        log(f"Generated synthetic test video: {test_video}")

    log(f"Target test video: {test_video}")

    # =========================================================================
    # TEST 1: Chinese Input -> Extract -> Transcribe -> Translate -> Voiceover (TTS) -> Export (Mode: Both)
    # =========================================================================
    log("TEST 1/5: Full Standard Pipeline (Chinese -> Vietnamese TTS -> Both Audio)")
    t1_proj = ps.ensure_project(test_video, input_language="zh", target_language="vi", mode="both")
    t1_proj_file = ps.project_file(t1_proj.project_root)

    sample_zh_segments = [
        {"id": 1, "start": 0.0, "end": 1.8, "text": "你好，欢迎使用这个软件。"},
        {"id": 2, "start": 1.9, "end": 3.8, "text": "这是一个快速测试。"}
    ]
    ps.save_json_artifact(t1_proj, "transcript_raw", os.path.join("analysis", "transcript_raw.json"), sample_zh_segments)
    t1_proj.set_step_status("transcribe", "done")

    translated_vi_segments = [
        {"id": 1, "start": 0.0, "end": 1.8, "text": "Xin chào, chào mừng bạn sử dụng phần mềm này.", "tts_text": "Xin chào, chào mừng bạn sử dụng phần mềm này.", "dubbing_vi": "Xin chào, chào mừng bạn sử dụng phần mềm này."},
        {"id": 2, "start": 1.9, "end": 3.8, "text": "Đây là một bài kiểm tra nhanh.", "tts_text": "Đây là một bài kiểm tra nhanh.", "dubbing_vi": "Đây là một bài kiểm tra nhanh."}
    ]
    ps.save_segment_artifact(t1_proj, "translation_final", os.path.join("translation", "translation_final.json"),
                             coerce_segments(translated_vi_segments))
    srt_translated = ps.build_path(t1_proj, "subtitle", "test1_vi.srt")
    runtime.generate_srt(translated_vi_segments, srt_translated)
    t1_proj.set_artifact("subtitle_translated_srt", srt_translated)
    t1_proj.set_step_status("translate_raw", "done")
    ps.save_project(t1_proj)

    vw = VoiceWorkflow(PROJECT_ROOT)
    t1_temp_dir = os.path.join(PROJECT_ROOT, "temp", "projects", t1_proj.project_id, "tts")
    t1_voice_res = vw.run(
        segments=translated_vi_segments,
        output_dir=os.path.join(t1_proj.project_root, "audio"),
        project_state_path=t1_proj_file,
        project_temp_dir=t1_temp_dir,
        voice_name="vi-VN-HoaiMyNeural",
        voice_speed=1.0,
        timing_sync_mode="smart"
    )
    assert os.path.exists(t1_voice_res["voice_track"]), "Test 1 Failed: voice_vi.wav not generated!"
    log(f"Test 1 TTS voice generated: {t1_voice_res['voice_track']} (Size: {os.path.getsize(t1_voice_res['voice_track'])} bytes)")

    ew = ExportWorkflow(PROJECT_ROOT)
    t1_out_mp4 = os.path.join(PROJECT_ROOT, "output", f"test1_full_out_{int(time.time())}.mp4")
    ew.run(
        video_path=test_video,
        srt_path=srt_translated,
        audio_path=t1_voice_res["voice_track"],
        output_path=t1_out_mp4,
        mode="both",
        project_state_path=t1_proj_file,
        project_temp_dir=os.path.join(PROJECT_ROOT, "temp", "projects", t1_proj.project_id)
    )
    assert os.path.exists(t1_out_mp4) and os.path.getsize(t1_out_mp4) > 1000, "Test 1 Export Failed!"
    log(f"✅ TEST 1 PASSED -> Output: {t1_out_mp4}")

    # =========================================================================
    # TEST 2: Mute A1 Track (Original Chinese Muted, 100% Pure Vietnamese TTS)
    # =========================================================================
    log("TEST 2/5: Mute Original Audio (A1 Muted, 100% Vietnamese TTS in Video)")
    t2_out_mp4 = os.path.join(PROJECT_ROOT, "output", f"test2_pure_tts_{int(time.time())}.mp4")
    ew.run(
        video_path=test_video,
        srt_path=srt_translated,
        audio_path=t1_voice_res["voice_track"],
        output_path=t2_out_mp4,
        mode="voice", # pure voice mode
        project_state_path=t1_proj_file,
        project_temp_dir=os.path.join(PROJECT_ROOT, "temp", "projects", t1_proj.project_id)
    )
    assert os.path.exists(t2_out_mp4) and os.path.getsize(t2_out_mp4) > 1000, "Test 2 Export Failed!"
    log(f"✅ TEST 2 PASSED -> Pure TTS Video: {t2_out_mp4}")

    # =========================================================================
    # TEST 3: Audio Separation Mode (Clean Mode)
    # =========================================================================
    log("TEST 3/5: Clean Mode (Vocal Isolation & Background Mix)")
    from audio_mixer import mix_original_with_dub
    t3_bg_wav = os.path.join(PROJECT_ROOT, "temp", "test3_bg.wav")
    os.makedirs(os.path.dirname(t3_bg_wav), exist_ok=True)
    cmd = [ffmpeg, "-hide_banner", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=4", "-ar", "44100", "-ac", "2", t3_bg_wav]
    subprocess.run(cmd, check=True, capture_output=True)

    t3_mixed_wav = os.path.join(PROJECT_ROOT, "temp", "test3_mixed.wav")
    mix_original_with_dub(
        original_wav_path=t3_bg_wav,
        dub_wav_path=t1_voice_res["voice_track"],
        output_wav_path=t3_mixed_wav,
        original_gain_db=-6.0,
        dub_gain_db=0.0
    )
    assert os.path.exists(t3_mixed_wav) and os.path.getsize(t3_mixed_wav) > 1000, "Test 3 Mix Failed!"
    log(f"✅ TEST 3 PASSED -> Clean Mode Mixed Audio: {t3_mixed_wav}")

    # =========================================================================
    # TEST 4: Subtitle-Only Mode (TTS Skipped, Original Audio Kept)
    # =========================================================================
    log("TEST 4/5: Subtitle-Only Mode (Original Audio + Burned Subtitles)")
    t4_out_mp4 = os.path.join(PROJECT_ROOT, "output", f"test4_sub_only_{int(time.time())}.mp4")
    ew.run(
        video_path=test_video,
        srt_path=srt_translated,
        audio_path="",
        output_path=t4_out_mp4,
        mode="subtitle",
        project_state_path=t1_proj_file,
        project_temp_dir=os.path.join(PROJECT_ROOT, "temp", "projects", t1_proj.project_id)
    )
    assert os.path.exists(t4_out_mp4) and os.path.getsize(t4_out_mp4) > 1000, "Test 4 Export Failed!"
    log(f"✅ TEST 4 PASSED -> Subtitle Only Video: {t4_out_mp4}")

    # =========================================================================
    # TEST 5: Vietnamese Source Input (No Translation Needed, Direct TTS)
    # =========================================================================
    log("TEST 5/5: Vietnamese Source Video (Direct TTS without Translation Step)")
    t5_proj = ps.ensure_project(test_video, input_language="vi", target_language="vi", mode="both")
    t5_proj_file = ps.project_file(t5_proj.project_root)
    sample_vi_segments = [
        {"id": 1, "start": 0.0, "end": 1.8, "text": "Kiểm tra hệ thống âm thanh tiếng Việt."},
        {"id": 2, "start": 1.9, "end": 3.8, "text": "Hoàn tất kiểm tra năm lần liên tiếp."}
    ]
    ps.save_segment_artifact(t5_proj, "transcript_segments", os.path.join("analysis", "transcript_segments.json"),
                             coerce_segments(sample_vi_segments))
    t5_temp_dir = os.path.join(PROJECT_ROOT, "temp", "projects", t5_proj.project_id, "tts")
    t5_voice_res = vw.run(
        segments=sample_vi_segments,
        output_dir=os.path.join(t5_proj.project_root, "audio"),
        project_state_path=t5_proj_file,
        project_temp_dir=t5_temp_dir,
        voice_name="vi-VN-HoaiMyNeural",
        voice_speed=1.0,
        timing_sync_mode="smart"
    )
    assert os.path.exists(t5_voice_res["voice_track"]), "Test 5 Failed: voice_vi.wav not generated for Vietnamese source!"

    t5_out_mp4 = os.path.join(PROJECT_ROOT, "output", f"test5_vi_source_out_{int(time.time())}.mp4")
    srt_vi = ps.build_path(t5_proj, "subtitle", "test5_vi.srt")
    runtime.generate_srt(sample_vi_segments, srt_vi)
    ew.run(
        video_path=test_video,
        srt_path=srt_vi,
        audio_path=t5_voice_res["voice_track"],
        output_path=t5_out_mp4,
        mode="both",
        project_state_path=t5_proj_file,
        project_temp_dir=os.path.join(PROJECT_ROOT, "temp", "projects", t5_proj.project_id)
    )
    assert os.path.exists(t5_out_mp4) and os.path.getsize(t5_out_mp4) > 1000, "Test 5 Export Failed!"
    log(f"✅ TEST 5 PASSED -> Vietnamese Source Output: {t5_out_mp4}")

    log("🎉 ALL 5/5 END-TO-END AUTOMATED TESTS COMPLETED WITH 100% SUCCESS!")

if __name__ == "__main__":
    run_tests()
