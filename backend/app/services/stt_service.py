import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stt_service")

class STTService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            logger.info(f"Loading faster-whisper model '{self.model_size}'...")
            from faster_whisper import WhisperModel
            # CPU with int8 quantization is fast, lightweight, and uses minimal memory
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            logger.info("faster-whisper model loaded successfully.")
        return self._model

    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """Extracts 16kHz mono WAV audio from a video file using FFmpeg."""
        video_p = Path(video_path)
        if not video_p.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        out_p = Path(output_audio_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",  # overwrite
            "-i", str(video_path),
            "-vn",  # disable video
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_audio_path)
        ]

        logger.info(f"Extracting audio: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg audio extraction error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed to extract audio: {result.stderr}")

        return output_audio_path

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribes audio file to text with timestamped segments using faster-whisper."""
        audio_p = Path(audio_path)
        if not audio_p.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._get_model()
        logger.info(f"Transcribing {audio_path}...")

        segments, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            word_timestamps=True,
            vad_filter=True
        )

        segment_list: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        for seg in segments:
            text = seg.text.strip()
            if text:
                full_text_parts.append(text)
                segment_list.append({
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": text
                })

        full_transcript = " ".join(full_text_parts)
        logger.info(f"Transcription complete. Length: {len(full_transcript)} chars, {len(segment_list)} segments.")

        return {
            "transcript": full_transcript,
            "segments": segment_list,
            "language": info.language,
            "duration": round(info.duration, 2)
        }

# Singleton instance
stt_service = STTService()
