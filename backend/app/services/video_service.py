import os
import time
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
from app.config import SYNCLABS_API_KEY, REPLICATE_API_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video_service")

class VideoService:
    def __init__(self):
        pass

    def get_media_duration(self, file_path: str) -> float:
        """Calculates audio/video duration using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and result.stdout.strip():
            try:
                return float(result.stdout.strip())
            except ValueError:
                pass
        return 10.0

    def _upload_asset_to_sync(self, file_path: str, content_type: str) -> Optional[str]:
        """Uploads local media file to Sync.so via presigned S3 URL and returns asset URL."""
        try:
            file_p = Path(file_path)
            file_size = file_p.stat().st_size
            headers = {"x-api-key": SYNCLABS_API_KEY, "Content-Type": "application/json"}
            payload = {
                "fileName": file_p.name,
                "contentType": content_type,
                "size": file_size
            }
            res = httpx.post("https://api.sync.so/v2/assets/upload", headers=headers, json=payload, timeout=30.0)
            if res.status_code != 201:
                logger.warning(f"Sync asset upload ticket failed: {res.text}")
                return None
            data = res.json()
            upload_url = data["uploadUrl"]
            asset_url = data["url"]

            with open(file_path, "rb") as f:
                content_bytes = f.read()

            put_res = httpx.put(upload_url, content=content_bytes, headers={"Content-Type": content_type}, timeout=120.0)
            if put_res.status_code not in [200, 204]:
                logger.warning(f"Sync asset S3 PUT failed: {put_res.status_code}")
                return None

            logger.info(f"Asset successfully uploaded to Sync: {asset_url}")
            return asset_url
        except Exception as e:
            logger.warning(f"Asset upload to Sync error: {e}")
            return None

    def sync_lips_with_synclabs(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """
        Invokes Sync Labs AI Lip-Sync API (lipsync-2 / sync-3 models) to seamlessly map mouth movements
        in the teacher's original video to the newly generated persona audio.
        """
        if not SYNCLABS_API_KEY:
            return False

        duration = self.get_media_duration(audio_path)
        logger.info(f"Executing Sync Labs AI Lip-Sync (media duration: {duration:.1f}s)...")
        
        # Check if duration exceeds SyncLabs free-tier 20s limit
        working_video = video_path
        working_audio = audio_path
        temp_clipped = False
        
        if duration > 19.5:
            logger.info("Audio duration exceeds 20s Sync Labs tier limit; generating synchronized lipsync preview segment...")
            short_v = f"/tmp/sync_temp_{int(time.time())}.mp4"
            short_a = f"/tmp/sync_temp_{int(time.time())}.mp3"
            subprocess.run(["ffmpeg", "-y", "-i", video_path, "-t", "18", "-c", "copy", short_v], capture_output=True)
            subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-t", "18", "-c", "copy", short_a], capture_output=True)
            if Path(short_v).exists() and Path(short_a).exists():
                working_video = short_v
                working_audio = short_a
                temp_clipped = True

        try:
            # 1. Upload video and audio to Sync
            video_url = self._upload_asset_to_sync(working_video, "video/mp4")
            audio_url = self._upload_asset_to_sync(working_audio, "audio/mpeg")

            if not video_url or not audio_url:
                logger.warning("Failed to obtain asset URLs for Sync.so, falling back to local engine.")
                return False

            # 2. Try models: lipsync-2 (active), lipsync-2-pro, sync-3
            headers = {"x-api-key": SYNCLABS_API_KEY, "Content-Type": "application/json"}
            job_id = None
            for model_name in ["lipsync-2", "lipsync-2-pro", "sync-3"]:
                generate_payload = {
                    "model": model_name,
                    "input": [
                        {"type": "video", "url": video_url},
                        {"type": "audio", "url": audio_url}
                    ]
                }
                gen_res = httpx.post("https://api.sync.so/v2/generate", headers=headers, json=generate_payload, timeout=30.0)
                if gen_res.status_code == 201:
                    job_id = gen_res.json().get("id")
                    logger.info(f"Sync Labs job submitted with model '{model_name}'! ID: {job_id}")
                    break
                else:
                    logger.warning(f"Sync.so model '{model_name}' returned: {gen_res.status_code} {gen_res.text[:120]}")

            if not job_id:
                logger.warning("All Sync Labs models rejected or at concurrency limit, using synchronized teacher video.")
                return False

            # 3. Poll for completion (up to 120s)
            for _ in range(40):
                time.sleep(3)
                poll_res = httpx.get(f"https://api.sync.so/v2/generate/{job_id}", headers=headers, timeout=15.0)
                if poll_res.status_code == 200:
                    job_data = poll_res.json()
                    status = job_data.get("status")
                    logger.info(f"Sync Labs job {job_id} status: {status}")

                    if status == "COMPLETED":
                        # Download result
                        output_url = job_data.get("outputUrl") or (job_data.get("output", {}).get("url") if isinstance(job_data.get("output"), dict) else None)
                        if not output_url and isinstance(job_data.get("output"), list) and len(job_data["output"]) > 0:
                            output_url = job_data["output"][0].get("url")

                        if output_url:
                            logger.info(f"Downloading completed lip-synced video from {output_url}...")
                            download_res = httpx.get(output_url, follow_redirects=True, timeout=120.0)
                            if download_res.status_code == 200:
                                with open(output_path, "wb") as f:
                                    f.write(download_res.content)
                                logger.info(f"Sync Labs video successfully saved to {output_path}!")
                                return True
                    elif status in ["FAILED", "REJECTED"]:
                        logger.warning(f"Sync Labs job failed: {job_data}")
                        return False

            logger.warning("Sync Labs job polling timed out, using synchronized local video.")
            return False
        except Exception as e:
            logger.warning(f"SyncLabs lip-sync execution error: {e}")
            return False

    def sync_lips_with_replicate(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """
        Invokes Replicate Wav2Lip model to lip-sync teacher face video to personalized audio.
        """
        if not REPLICATE_API_TOKEN:
            return False

        logger.info("Attempting Replicate Wav2Lip AI Lip-Sync...")
        try:
            import replicate
            client = replicate.Client(api_token=REPLICATE_API_TOKEN)
            with open(video_path, "rb") as face_file, open(audio_path, "rb") as audio_file:
                output = client.run(
                    "cjwbw/wav2lip:240728c0c45167e41d8e12df1d97ce1d368021f1d198ee6ecba947a11ab0caac",
                    input={
                        "face": face_file,
                        "audio": audio_file,
                        "pads": "0 10 0 0",
                        "smooth": True
                    }
                )
                if output:
                    logger.info(f"Replicate Wav2Lip output received: {output}")
                    resp = httpx.get(str(output), timeout=60.0)
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    return True
        except Exception as e:
            logger.warning(f"Replicate Wav2Lip failed: {e}")
            return False

    def render_personalized_video(
        self,
        audio_path: str,
        output_video_path: str,
        lecture_title: str,
        persona: Dict[str, Any],
        facts: List[Dict[str, Any]],
        master_video_path: Optional[str] = None
    ) -> str:
        """
        Produces the personalized video for the student:
        1. Attempts SyncLabs or Replicate Wav2Lip AI Lip-Sync on the teacher's original video.
        2. If running locally: Uses the EXACT teacher video as the full main canvas,
           stretches/loops the visual footage to match the personalized audio duration,
           overlays an elegant persona badge, and remuxes with the new audio track.
        """
        out_p = Path(output_video_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        audio_duration = self.get_media_duration(audio_path)
        logger.info(f"Target personalized audio duration: {audio_duration:.2f}s")

        # Check if master teacher video exists
        has_master_video = master_video_path and Path(master_video_path).exists()

        if has_master_video:
            # Step 1: Try Cloud Lip-Sync APIs if keys are available
            if SYNCLABS_API_KEY and self.sync_lips_with_synclabs(master_video_path, audio_path, output_video_path):
                return output_video_path

            if REPLICATE_API_TOKEN and self.sync_lips_with_replicate(master_video_path, audio_path, output_video_path):
                return output_video_path

            # Step 2: High-Quality Teacher Video Remux & Timing Synchronization
            # We preserve the EXACT original video of the teacher in full view!
            logger.info(f"Generating full teacher video with personalized audio from {master_video_path}...")

            master_duration = self.get_media_duration(master_video_path)
            logger.info(f"Master video duration: {master_duration:.2f}s, target audio duration: {audio_duration:.2f}s")

            # Timing Synchronization: NEVER loop or repeat the video from the beginning!
            # Instead, dynamically scale video presentation timestamps (setpts) so the teacher
            # video plays continuously from start to finish matching the personalized audio track.
            if master_duration > 0 and audio_duration > 0:
                pts_factor = audio_duration / master_duration
            else:
                pts_factor = 1.0

            # Guard extreme pts_factor (keep video natural between 0.4x and 2.5x)
            pts_factor = max(0.4, min(2.5, pts_factor))
            logger.info(f"Applying seamless PTS scaling factor: {pts_factor:.4f} (no looping)")

            cmd = [
                "ffmpeg", "-y",
                "-i", str(master_video_path),
                "-i", str(audio_path),
                "-vf", f"setpts={pts_factor:.4f}*PTS",
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(output_video_path)
            ]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and Path(output_video_path).exists():
                logger.info(f"Teacher video successfully synchronized without looping: {output_video_path}")
                return output_video_path
            else:
                logger.warning(f"PTS filter failed: {res.stderr}. Using direct remux...")
                cmd_fallback = [
                    "ffmpeg", "-y",
                    "-i", str(master_video_path),
                    "-i", str(audio_path),
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-c:a", "aac",
                    "-shortest",
                    str(output_video_path)
                ]
                subprocess.run(cmd_fallback, check=True)
                return output_video_path

        # If no master video is available, fallback to educational presenter canvas
        logger.info("No master video found. Rendering fallback presentation canvas...")
        temp_img = str(out_p.parent / "temp_slide.png")
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (1280, 720), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        draw.text((80, 200), lecture_title, fill=(248, 250, 252))
        draw.text((80, 280), f"Persona: {persona.get('name')}", fill=(96, 165, 250))
        img.save(temp_img)

        cmd_still = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", temp_img,
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-shortest",
            str(output_video_path)
        ]
        subprocess.run(cmd_still, check=True)
        return output_video_path

video_service = VideoService()
