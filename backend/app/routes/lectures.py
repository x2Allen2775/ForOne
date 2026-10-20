import shutil
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from app.config import MASTER_DIR
from app.database import (
    get_connection,
    get_all_lectures,
    get_lecture_by_id,
    get_lecture_facts
)
from app.services.stt_service import stt_service
from app.services.fact_extractor import fact_extractor
from app.services.video_service import video_service

router = APIRouter(prefix="/api/lectures", tags=["lectures"])

@router.get("")
def list_lectures():
    lectures = get_all_lectures()
    # Enrich with facts count
    for lec in lectures:
        facts = get_lecture_facts(lec["id"])
        lec["facts_count"] = len(facts)
    return {"lectures": lectures}

@router.get("/{lecture_id}")
def get_lecture(lecture_id: str):
    lec = get_lecture_by_id(lecture_id)
    if not lec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    facts = get_lecture_facts(lecture_id)
    return {
        "lecture": lec,
        "facts": facts
    }

@router.get("/{lecture_id}/video")
def get_lecture_video(lecture_id: str):
    lec = get_lecture_by_id(lecture_id)
    if not lec or not lec.get("master_video_path"):
        raise HTTPException(status_code=404, detail="Master video not found")
    video_p = Path(lec["master_video_path"])
    if not video_p.exists():
        raise HTTPException(status_code=404, detail="Video file missing on disk")
    return FileResponse(str(video_p), media_type="video/mp4")

@router.get("/{lecture_id}/audio")
def get_lecture_audio(lecture_id: str):
    lec = get_lecture_by_id(lecture_id)
    if not lec or not lec.get("master_audio_path"):
        raise HTTPException(status_code=404, detail="Master audio not found")
    audio_p = Path(lec["master_audio_path"])
    if not audio_p.exists():
        raise HTTPException(status_code=404, detail="Audio file missing on disk")
    return FileResponse(str(audio_p), media_type="audio/mpeg")

def process_uploaded_lecture_background(
    lecture_id: str,
    video_path: str,
    audio_path: str,
    title: str,
    subject: str,
    instructor: str
):
    try:
        # 1. Extract audio
        stt_service.extract_audio_from_video(video_path, audio_path)

        # 2. Transcribe
        stt_res = stt_service.transcribe_audio(audio_path)
        transcript = stt_res.get("transcript", "")
        duration = stt_res.get("duration", 0.0)

        # 3. Extract facts
        facts = fact_extractor.extract_facts(transcript, stt_res.get("segments"))

        # 4. Update Database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE lectures
        SET duration_seconds = ?, master_transcript = ?, status = 'ready'
        WHERE id = ?
        """, (duration, transcript, lecture_id))

        for f in facts:
            cursor.execute("""
            INSERT INTO lecture_facts (lecture_id, fact_id, category, statement, keywords, criticality, timestamp_hint)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lecture_id,
                f.get("fact_id", "F01"),
                f.get("category", "concept"),
                f.get("statement", ""),
                ",".join(f.get("keywords", [])),
                f.get("criticality", "critical"),
                f.get("timestamp_hint", "00:00")
            ))
        conn.commit()
        conn.close()

    except Exception as e:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE lectures SET status = 'failed' WHERE id = ?", (lecture_id,))
        conn.commit()
        conn.close()
        print(f"Error processing uploaded lecture {lecture_id}: {e}")

@router.post("/upload")
async def upload_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: str = Form(...),
    instructor: str = Form("Course Instructor")
):
    lecture_id = f"lec_{uuid.uuid4().hex[:8]}"
    lecture_folder = MASTER_DIR / lecture_id
    lecture_folder.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix or ".mp4"
    video_path = str(lecture_folder / f"master_video{file_ext}")
    audio_path = str(lecture_folder / "master_audio.wav")

    # Save uploaded file
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Register in DB with 'processing' status
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO lectures (id, title, subject, instructor, duration_seconds, master_video_path, master_audio_path, master_transcript, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'processing', ?)
    """, (
        lecture_id,
        title,
        subject,
        instructor,
        0.0,
        video_path,
        audio_path,
        "",
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

    # Trigger async processing
    background_tasks.add_task(
        process_uploaded_lecture_background,
        lecture_id,
        video_path,
        audio_path,
        title,
        subject,
        instructor
    )

    return {
        "status": "success",
        "message": "Lecture uploaded successfully and analysis pipeline started.",
        "lecture_id": lecture_id
    }
