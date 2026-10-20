import re
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts_service")

from app.config import ELEVENLABS_API_KEY
import httpx

class TTSService:
    def __init__(self):
        pass

    async def generate_speech_async(
        self,
        script_text: str,
        output_audio_path: str,
        voice_name: str = "en-US-GuyNeural",
        rate_modifier: float = 1.0,
        teacher_audio_sample: Optional[str] = None
    ) -> str:
        """
        Synthesizes audio using ElevenLabs voice cloning/synthesis if API key is provided,
        or falls back to high quality neural voices via edge-tts.
        """
        out_p = Path(output_audio_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        clean_text = re.sub(r'\[\/?FACT:?[^\]]*\]', '', script_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Tier 1: ElevenLabs Voice Cloning & Synthesis (as specified in doc)
        if ELEVENLABS_API_KEY:
            try:
                logger.info("Synthesizing audio via ElevenLabs API...")
                # Voice mapping or custom cloned voice
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel or custom teacher clone
                eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": clean_text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(eleven_url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        with open(output_audio_path, "wb") as f:
                            f.write(resp.content)
                        logger.info(f"ElevenLabs speech generated and saved to {output_audio_path}")
                        return output_audio_path
                    else:
                        logger.warning(f"ElevenLabs API returned {resp.status_code}: {resp.text}, falling back to Edge-TTS")
            except Exception as e:
                logger.warning(f"ElevenLabs synthesis error: {e}, falling back to Edge-TTS")

        # Tier 2: Free Microsoft Edge Neural Speech
        import edge_tts

        out_p = Path(output_audio_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        # Strip internal audit tags before vocalizing
        clean_text = re.sub(r'\[\/?FACT:?[^\]]*\]', '', script_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Format rate string (e.g. "+5%" or "-10%")
        rate_percent = int((rate_modifier - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"

        logger.info(f"Synthesizing speech with voice '{voice_name}', rate '{rate_str}'...")

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice_name,
            rate=rate_str
        )

        await communicate.save(str(output_audio_path))
        logger.info(f"Speech saved to {output_audio_path}")
        return output_audio_path

    def generate_speech(
        self,
        script_text: str,
        output_audio_path: str,
        voice_name: str = "en-US-GuyNeural",
        rate_modifier: float = 1.0,
        teacher_audio_sample: Optional[str] = None
    ) -> str:
        """Synchronous wrapper for generate_speech_async."""
        return asyncio.run(
            self.generate_speech_async(script_text, output_audio_path, voice_name, rate_modifier, teacher_audio_sample)
        )

tts_service = TTSService()
