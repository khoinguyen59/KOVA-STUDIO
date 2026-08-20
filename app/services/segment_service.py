from __future__ import annotations

import re

from core.models import Segment


class SegmentService:
    """Create consistently timed subtitle/TTS cues from ASR results."""

    MAX_CUE_DURATION_SECONDS = 5.25
    MAX_CUE_GAP_SECONDS = 0.85
    MAX_CUE_CHARACTERS = 36
    MIN_CUE_DURATION_SECONDS = 0.75

    def transcript_dicts_to_models(self, raw_segments) -> list[Segment]:
        return [
            Segment.from_transcript_dict(raw_segment, segment_id=index)
            for index, raw_segment in enumerate(raw_segments or [], start=1)
        ]

    def normalize_transcript_cues(self, raw_segments) -> list[dict]:
        """Split long ASR segments using their word timestamps.

        Faster-Whisper commonly returns speech segments that last 20--60
        seconds. They are useful for recognition, but not for subtitles or
        per-cue TTS. This converts them into short cues, retains the original
        word timings, and removes timeline overlap before translation so the
        translated SRT and the voice track stay one-to-one.
        """
        cues: list[dict] = []
        for source in list(raw_segments or []):
            if not isinstance(source, dict):
                continue
            cues.extend(self._split_transcript_segment(source))
        return self._normalize_timeline(cues)

    def _split_transcript_segment(self, source: dict) -> list[dict]:
        text = str(source.get("text", "") or "").strip()
        start = self._as_seconds(source.get("start"), 0.0)
        end = max(start, self._as_seconds(source.get("end"), start))
        words = self._normalized_words(source.get("words"), start=start, end=end)
        if not words:
            return self._split_without_words(source, text=text, start=start, end=end)

        groups: list[list[dict]] = []
        current: list[dict] = []
        for word in words:
            if current:
                cue_start = float(current[0]["start"])
                cue_end = float(current[-1]["end"])
                candidate_duration = float(word["end"]) - cue_start
                gap = float(word["start"]) - cue_end
                candidate_text = self._join_word_texts([*current, word])
                should_split = (
                    gap > self.MAX_CUE_GAP_SECONDS
                    or (
                        candidate_duration > self.MAX_CUE_DURATION_SECONDS
                        and (cue_end - cue_start) >= self.MIN_CUE_DURATION_SECONDS
                    )
                    or (
                        len(candidate_text) > self.MAX_CUE_CHARACTERS
                        and (cue_end - cue_start) >= self.MIN_CUE_DURATION_SECONDS
                    )
                )
                if should_split:
                    groups.append(current)
                    current = []
            current.append(word)
            cue_duration = float(current[-1]["end"]) - float(current[0]["start"])
            if cue_duration >= self.MIN_CUE_DURATION_SECONDS and self._ends_sentence(str(word["text"])):
                groups.append(current)
                current = []
        if current:
            groups.append(current)

        return [self._cue_from_words(source, group) for group in groups if group]

    def _split_without_words(self, source: dict, *, text: str, start: float, end: float) -> list[dict]:
        if not text:
            return []
        duration = max(0.05, end - start)
        if duration <= self.MAX_CUE_DURATION_SECONDS and len(text) <= self.MAX_CUE_CHARACTERS:
            return [self._cue_from_text(source, text=text, start=start, end=end)]

        chunks = self._split_text_chunks(text)
        if not chunks:
            return [self._cue_from_text(source, text=text, start=start, end=end)]
        span = duration / len(chunks)
        return [
            self._cue_from_text(
                source,
                text=chunk,
                start=start + index * span,
                end=start + (index + 1) * span,
            )
            for index, chunk in enumerate(chunks)
        ]

    def _normalized_words(self, raw_words, *, start: float, end: float) -> list[dict]:
        words: list[dict] = []
        for item in list(raw_words or []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "") or "").strip()
            if not text:
                continue
            word_start = max(start, self._as_seconds(item.get("start"), start))
            word_end = max(word_start, self._as_seconds(item.get("end"), word_start))
            if end > start:
                word_start = min(word_start, end)
                word_end = min(max(word_end, word_start), end)
            # Whisper occasionally assigns a single token an implausibly long
            # duration (20+ seconds in the reproduced project). A subtitle
            # must not remain on screen for that entire malformed token.
            word_end = min(word_end, word_start + self.MAX_CUE_DURATION_SECONDS)
            words.append({"start": word_start, "end": word_end, "text": text})
        words.sort(key=lambda item: (float(item["start"]), float(item["end"])))
        return words

    def _cue_from_words(self, source: dict, words: list[dict]) -> dict:
        return self._cue_from_text(
            source,
            text=self._join_word_texts(words),
            start=float(words[0]["start"]),
            end=float(words[-1]["end"]),
            words=words,
        )

    def _cue_from_text(self, source: dict, *, text: str, start: float, end: float, words=None) -> dict:
        payload = {
            key: value
            for key, value in source.items()
            if key not in {"id", "start", "end", "text", "words", "tts_text", "tts_group_id", "tts_group_start", "tts_group_end"}
        }
        payload.update(
            {
                "start": round(float(start), 3),
                "end": round(max(float(end), float(start) + 0.05), 3),
                "text": str(text or "").strip(),
                "tts_text": "",
                "tts_group_id": "",
                "tts_group_start": round(float(start), 3),
                "tts_group_end": round(max(float(end), float(start) + 0.05), 3),
            }
        )
        if words:
            payload["words"] = [dict(word) for word in words]
        return payload

    def _normalize_timeline(self, cues: list[dict]) -> list[dict]:
        normalized: list[dict] = []
        previous_end = -1.0
        for cue in sorted(cues, key=lambda item: (self._as_seconds(item.get("start"), 0.0), self._as_seconds(item.get("end"), 0.0))):
            text = str(cue.get("text", "") or "").strip()
            if not text:
                continue
            start = max(0.0, self._as_seconds(cue.get("start"), 0.0))
            end = max(start + 0.05, self._as_seconds(cue.get("end"), start))
            if previous_end >= 0.0 and start < previous_end:
                start = round(previous_end + 0.01, 3)
            if end <= start:
                # This is an entirely duplicated/overlapped ASR fragment.
                # Do not create a flashing subtitle with no real duration.
                continue
            cue["id"] = len(normalized) + 1
            cue["start"] = round(start, 3)
            cue["end"] = round(end, 3)
            cue["tts_group_start"] = cue["start"]
            cue["tts_group_end"] = cue["end"]
            normalized.append(cue)
            previous_end = end
        return normalized

    @staticmethod
    def _as_seconds(value, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _ends_sentence(value: str) -> bool:
        return bool(re.search(r"[.!?…。！？]+$", str(value or "")))

    @staticmethod
    def _is_cjk(value: str) -> bool:
        return bool(re.search(r"[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]", value or ""))

    def _join_word_texts(self, words: list[dict]) -> str:
        result = ""
        for item in words:
            token = str(item.get("text", "") or "").strip()
            if not token:
                continue
            if not result:
                result = token
                continue
            previous = result[-1:]
            no_space = (
                token[0] in ",.!?;:…，。！？、】【)]}）】"
                or previous in "([{'（【"
                or (self._is_cjk(previous) and self._is_cjk(token[0]))
                or token.startswith(("'", "’"))
            )
            result += token if no_space else f" {token}"
        return result.strip()

    def _split_text_chunks(self, text: str) -> list[str]:
        value = str(text or "").strip()
        if not value:
            return []
        if self._is_cjk(value) and not re.search(r"\s", value):
            tokens = list(value)
            joiner = ""
        else:
            tokens = re.findall(r"\S+", value)
            joiner = " "
        chunks: list[str] = []
        current: list[str] = []
        for token in tokens:
            candidate = joiner.join([*current, token])
            if current and len(candidate) > self.MAX_CUE_CHARACTERS:
                chunks.append(joiner.join(current))
                current = []
            current.append(token)
        if current:
            chunks.append(joiner.join(current))
        return chunks

    def segment_dicts_to_models(self, segments, *, translated: bool = False) -> list[Segment]:
        models: list[Segment] = []
        for idx, seg in enumerate(segments or [], start=1):
            model = Segment.from_dict(seg, default_id=idx)
            if translated:
                translated_text = seg.get("text", "")
                model.apply_translation(translated_text, refined=bool(seg.get("polished")))
                if "words" in seg:
                    model.metadata["words"] = list(seg.get("words") or [])
                if "manual_highlights" in seg:
                    model.metadata["manual_highlights"] = list(seg.get("manual_highlights") or [])
                if "auto_highlights" in seg:
                    model.metadata["auto_highlights"] = list(seg.get("auto_highlights") or [])
            elif not model.original_text:
                model.original_text = str(seg.get("text", "") or "")
                model.status = "transcribed"
            models.append(model)
        return models

    def apply_translations(self, base_models, translated_segments) -> list[Segment]:
        models: list[Segment] = []
        base_models = base_models or []
        for idx, seg in enumerate(translated_segments or [], start=1):
            model = Segment.from_dict(seg, default_id=idx)
            if idx - 1 < len(base_models):
                base_model = base_models[idx - 1]
                if not model.original_text:
                    model.original_text = base_model.original_text
                source_words = base_model.metadata.get("words")
                if source_words and "words" not in seg:
                    model.metadata["words"] = list(source_words)
                source_speaker = str(base_model.metadata.get("speaker", "") or "").strip()
                if source_speaker and "speaker" not in seg:
                    model.metadata["speaker"] = source_speaker
                source_highlights = base_model.metadata.get("manual_highlights")
                if source_highlights and "manual_highlights" not in seg:
                    model.metadata["manual_highlights"] = list(source_highlights)
                source_auto_highlights = base_model.metadata.get("auto_highlights")
                if source_auto_highlights and "auto_highlights" not in seg:
                    model.metadata["auto_highlights"] = list(source_auto_highlights)
            translated_text = seg.get("text", "")
            model.apply_translation(translated_text, refined=bool(seg.get("polished")))
            model.metadata["translation_provider"] = seg.get("provider", "")
            model.metadata["source_text"] = seg.get("source_text", "")
            if "words" in seg:
                model.metadata["words"] = list(seg.get("words") or [])
            if "manual_highlights" in seg:
                model.metadata["manual_highlights"] = list(seg.get("manual_highlights") or [])
            if "auto_highlights" in seg:
                model.metadata["auto_highlights"] = list(seg.get("auto_highlights") or [])
            for key in ("tts_group_id", "tts_group_start", "tts_group_end"):
                if key in seg:
                    model.metadata[key] = seg.get(key)
            models.append(model)
        return models
