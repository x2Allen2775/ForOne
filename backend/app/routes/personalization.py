import json
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.config import PERSONALIZED_DIR
from app.database import (
    get_connection,
    get_all_personas,
    get_persona_by_id,
    get_lecture_by_id,
    get_lecture_facts,
    get_personalized_lectures,
    get_personalized_lecture_by_id
)
from app.services.rewriter_service import rewriter_service
from app.services.tts_service import tts_service
from app.services.video_service import video_service
from app.services.failsafe_verifier import failsafe_verifier

router = APIRouter(prefix="/api/personalize", tags=["personalization"])

class PersonalizeRequest(BaseModel):
    lecture_id: str
    persona_id: str
    simulate_error: bool = False  # Allows testing the failsafe error trigger

@router.get("/personas")
def list_personas():
    return {"personas": get_all_personas()}

@router.get("/lecture/{lecture_id}")
def list_personalized_variants(lecture_id: str):
    variants = get_personalized_lectures(lecture_id)
    # Parse audit JSON for frontend display
    for v in variants:
        if v.get("audit_report_json"):
            try:
                v["audit_report"] = json.loads(v["audit_report_json"])
            except Exception:
                v["audit_report"] = None
    return {"variants": variants}

@router.get("/{pers_id}")
def get_variant_detail(pers_id: str):
    var = get_personalized_lecture_by_id(pers_id)
    if not var:
        raise HTTPException(status_code=404, detail="Personalized lecture not found")
    if var.get("audit_report_json"):
        try:
            var["audit_report"] = json.loads(var["audit_report_json"])
        except Exception:
            var["audit_report"] = None
    return {"personalized_lecture": var}

@router.get("/{pers_id}/video")
def get_variant_video(pers_id: str):
    var = get_personalized_lecture_by_id(pers_id)
    if not var or not var.get("video_path"):
        raise HTTPException(status_code=404, detail="Video not found")
    video_p = Path(var["video_path"])
    if not video_p.exists():
        raise HTTPException(status_code=404, detail="Video file missing on disk")
    return FileResponse(str(video_p), media_type="video/mp4")

@router.post("/generate")
def generate_personalized_lecture(req: PersonalizeRequest):
    lecture = get_lecture_by_id(req.lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    persona = get_persona_by_id(req.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    facts = get_lecture_facts(req.lecture_id)
    if not facts:
        raise HTTPException(status_code=400, detail="Lecture has no extracted facts yet")

    pers_id = f"pers_{req.persona_id}_{uuid.uuid4().hex[:6]}"
    out_dir = PERSONALIZED_DIR / pers_id
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_path = str(out_dir / "personalized_audio.mp3")
    video_path = str(out_dir / "personalized_video.mp4")

    # Step 1: Pedagogical Persona Rewriting
    script = rewriter_service.rewrite_for_persona(
        master_transcript=lecture.get("master_transcript", ""),
        facts=facts,
        persona=persona,
        simulate_error=req.simulate_error
    )

    # Step 2: Neural Voice Synthesis & Voice Cloning
    tts_service.generate_speech(
        script_text=script,
        output_audio_path=audio_path,
        voice_name=persona.get("voice_name", "en-US-GuyNeural"),
        rate_modifier=persona.get("pacing_multiplier", 1.0),
        teacher_audio_sample=lecture.get("master_audio_path")
    )

    # Step 3: Render Educational Video with Dynamic Slides & Timing
    video_service.render_personalized_video(
        audio_path=audio_path,
        output_video_path=video_path,
        lecture_title=lecture["title"],
        persona=persona,
        facts=facts,
        master_video_path=lecture.get("master_video_path")
    )

    # Step 4: Mission-Critical Failsafe Fact & Detail Verification
    audit_result = failsafe_verifier.verify_personalized_video(
        master_facts=facts,
        generated_video_path=video_path,
        lecture_id=req.lecture_id,
        persona_id=req.persona_id
    )

    final_status = "approved" if audit_result["status"] == "APPROVED" else "rejected_failsafe"
    fidelity_score = audit_result["fidelity_score"]
    error_message = audit_result.get("error_message")
    audit_json = json.dumps(audit_result)
    gen_transcript = audit_result.get("gen_transcript", "")

    # Step 5: Save record into SQLite Database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO personalized_lectures (
        id, lecture_id, persona_id, script_text, audio_path, video_path,
        gen_transcript_text, status, fact_fidelity_score, audit_report_json, error_message, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pers_id,
        req.lecture_id,
        req.persona_id,
        script,
        audio_path,
        video_path,
        gen_transcript,
        final_status,
        fidelity_score,
        audit_json,
        error_message,
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

    return {
        "status": final_status,
        "personalized_id": pers_id,
        "fidelity_score": fidelity_score,
        "error_message": error_message,
        "audit_report": audit_result,
        "is_approved": (final_status == "approved")
    }
