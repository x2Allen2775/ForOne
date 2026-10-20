import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from app.config import MASTER_DIR, DB_PATH
from app.database import init_db, get_connection
from app.services.tts_service import tts_service
from app.services.video_service import video_service
from app.services.stt_service import stt_service
from app.services.fact_extractor import fact_extractor

def seed_sample_binary_search_lecture():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    lecture_id = "lec_binary_search_101"

    # Check if already seeded
    cursor.execute("SELECT id FROM lectures WHERE id = ?", (lecture_id,))
    if cursor.fetchone():
        print(f"Sample lecture '{lecture_id}' is already seeded.")
        conn.close()
        return lecture_id

    print("Generating sample master lecture: 'Binary Search Algorithm & Time Complexity'...")

    lecture_folder = MASTER_DIR / lecture_id
    lecture_folder.mkdir(parents=True, exist_ok=True)

    master_audio_path = str(lecture_folder / "master_audio.mp3")
    master_video_path = str(lecture_folder / "master_video.mp4")

    # The teacher's master lecture script
    teacher_script = (
        "Welcome everyone. Today we are diving into the Binary Search algorithm, one of the most foundational techniques in computer science. "
        "First, the fundamental prerequisite: the array must already be sorted in ascending order. If it is unsorted, binary search fails. "
        "Second, we initialize two pointers: low at index 0, and high at length minus 1. "
        "In each step, we calculate the middle index as low plus high divided by 2. "
        "If our target matches the middle element, we return the index. "
        "If our target is smaller than the middle element, we discard the right half by setting high to mid minus 1. "
        "If our target is larger, we discard the left half by setting low to mid plus 1. "
        "Because we divide the search space by two in every single iteration, the worst-case time complexity is O(log n), which is exponentially faster than linear search O(n)."
    )

    # 1. Synthesize Teacher Speech
    print("Synthesizing teacher audio using Edge-TTS...")
    tts_service.generate_speech(
        script_text=teacher_script,
        output_audio_path=master_audio_path,
        voice_name="en-US-SteffanNeural",  # Academic teacher voice
        rate_modifier=1.0
    )

    # 2. Render Slide Card and Compose Master Video
    print("Composing master video MP4 using FFmpeg...")
    master_facts_mock = [
        {
            "fact_id": "F01",
            "category": "prerequisite",
            "statement": "The array must already be sorted in ascending order for binary search to work.",
            "keywords": ["sorted", "ascending", "array", "prerequisite"],
            "criticality": "critical",
            "timestamp_hint": "00:08"
        },
        {
            "fact_id": "F02",
            "category": "step",
            "statement": "Initialize two pointers: low at index 0, and high at length minus 1.",
            "keywords": ["pointers", "low", "high", "index"],
            "criticality": "critical",
            "timestamp_hint": "00:15"
        },
        {
            "fact_id": "F03",
            "category": "formula",
            "statement": "In each step, calculate the midpoint index as low plus high divided by 2.",
            "keywords": ["midpoint", "formula", "divide"],
            "criticality": "critical",
            "timestamp_hint": "00:22"
        },
        {
            "fact_id": "F04",
            "category": "step",
            "statement": "Discard half the remaining elements depending on whether target is less or greater than midpoint.",
            "keywords": ["discard", "target", "midpoint", "half"],
            "criticality": "critical",
            "timestamp_hint": "00:30"
        },
        {
            "fact_id": "F05",
            "category": "formula",
            "statement": "The worst-case time complexity is O(log n) because search space halves every iteration.",
            "keywords": ["O(log n)", "time complexity", "halves", "worst-case"],
            "criticality": "critical",
            "timestamp_hint": "00:40"
        }
    ]

    mock_persona = {
        "id": "master_teacher",
        "name": "Prof. Alan Vance",
        "accent_color": "#38bdf8"
    }

    video_service.render_personalized_video(
        audio_path=master_audio_path,
        output_video_path=master_video_path,
        lecture_title="Binary Search Algorithm & Time Complexity",
        persona=mock_persona,
        facts=master_facts_mock
    )

    # 3. Transcribe and Extract Facts
    print("Transcribing master lecture with faster-whisper...")
    stt_res = stt_service.transcribe_audio(master_audio_path)
    transcript = stt_res.get("transcript", teacher_script)
    duration = stt_res.get("duration", 45.0)

    # 4. Extract structured facts
    print("Extracting granular syllabus facts...")
    facts = fact_extractor.extract_facts(transcript, stt_res.get("segments"))
    if not facts:
        facts = master_facts_mock

    # 5. Insert into Database
    cursor.execute("""
    INSERT INTO lectures (id, title, subject, instructor, duration_seconds, master_video_path, master_audio_path, master_transcript, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lecture_id,
        "Binary Search Algorithm & Time Complexity",
        "Computer Science / Data Structures & Algorithms",
        "Prof. Alan Vance",
        duration,
        master_video_path,
        master_audio_path,
        transcript,
        "ready",
        datetime.utcnow().isoformat()
    ))

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
    print(f"Sample lecture '{lecture_id}' successfully seeded and ready in database!")
    return lecture_id

if __name__ == "__main__":
    seed_sample_binary_search_lecture()
