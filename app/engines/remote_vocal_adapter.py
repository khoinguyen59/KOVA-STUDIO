from __future__ import annotations

import base64
import os

from remote_api import remote_api_post


class RemoteVocalAdapter:
    """Vocal separation performed by the connected Colab server."""

    def separate(self, audio_path: str, output_dir: str):
        source = os.path.abspath(str(audio_path or "").strip())
        if not source or not os.path.isfile(source):
            raise FileNotFoundError(f"Audio file for remote vocal separation was not found: {audio_path}")

        with open(source, "rb") as handle:
            audio_b64 = base64.b64encode(handle.read()).decode("ascii")
        response = remote_api_post(
            "/v1/separate-vocals",
            {
                "audio_b64": audio_b64,
                "audio_filename": os.path.basename(source),
            },
            timeout=3600,
            retries=1,
        )
        try:
            vocals = base64.b64decode(str(response.get("vocals_b64", "") or "").encode("ascii"), validate=True)
            background = base64.b64decode(str(response.get("background_b64", "") or "").encode("ascii"), validate=True)
        except Exception as exc:
            raise RuntimeError("Remote Colab returned invalid vocal-separation audio data.") from exc
        if not vocals or not background:
            raise RuntimeError("Remote Colab did not return both vocal-separation stems.")

        stem_name = os.path.splitext(os.path.basename(source))[0] or "audio"
        stem_dir = os.path.join(os.path.abspath(output_dir), "remote_separated", stem_name)
        os.makedirs(stem_dir, exist_ok=True)
        vocals_path = os.path.join(stem_dir, "vocals.wav")
        background_path = os.path.join(stem_dir, "no_vocals.wav")
        with open(vocals_path, "wb") as handle:
            handle.write(vocals)
        with open(background_path, "wb") as handle:
            handle.write(background)
        return vocals_path, background_path
