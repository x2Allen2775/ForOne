import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lectures (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        instructor TEXT DEFAULT 'Instructor',
        duration_seconds REAL DEFAULT 0,
        master_video_path TEXT,
        master_audio_path TEXT,
        master_transcript TEXT,
        status TEXT DEFAULT 'uploaded',
        created_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lecture_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecture_id TEXT NOT NULL,
        fact_id TEXT NOT NULL,
        category TEXT NOT NULL,
        statement TEXT NOT NULL,
        keywords TEXT DEFAULT '',
        criticality TEXT DEFAULT 'critical',
        timestamp_hint TEXT DEFAULT '00:00',
        FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_personas (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        tag TEXT NOT NULL,
        description TEXT NOT NULL,
        voice_name TEXT NOT NULL,
        tone TEXT NOT NULL,
        pacing_multiplier REAL DEFAULT 1.0,
        accent_color TEXT DEFAULT '#3b82f6'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personalized_lectures (
        id TEXT PRIMARY KEY,
        lecture_id TEXT NOT NULL,
        persona_id TEXT NOT NULL,
        script_text TEXT,
        audio_path TEXT,
        video_path TEXT,
        gen_transcript_text TEXT,
        status TEXT DEFAULT 'pending',
        fact_fidelity_score REAL DEFAULT 0.0,
        audit_report_json TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE,
        FOREIGN KEY (persona_id) REFERENCES student_personas(id)
    );
    """)

    # Seed Default Personas if table empty
    cursor.execute("SELECT COUNT(*) FROM student_personas")
    if cursor.fetchone()[0] == 0:
        default_personas = [
            (
                "witty",
                "Witty & Relatable",
                "Engaging & Funny",
                "Uses punchy humor, modern gaming/tech analogies, and casual dialogue while maintaining 100% technical fact precision.",
                "en-US-GuyNeural",
                "enthusiastic_witty",
                1.05,
                "#f59e0b"
            ),
            (
                "intuitive",
                "First-Principles Intuitive",
                "Visual & Conceptual",
                "Deconstructs complex academic terms into physical real-world mental models (e.g. water pipes, road networks) before formalization.",
                "en-US-ChristopherNeural",
                "curious_philosophical",
                0.95,
                "#10b981"
            ),
            (
                "exam_cram",
                "High-Yield Exam Crusher",
                "Fast & Direct",
                "Razor-sharp pacing. Eliminates fluff, highlights exam trap questions, core formulas, and time complexity derivations.",
                "en-US-BrianNeural",
                "direct_authoritative",
                1.15,
                "#ef4444"
            ),
            (
                "supportive",
                "Slow & Supportive Mentor",
                "Calm & Reassuring",
                "Gentle pacing, step-by-step guidance, frequent summary check-ins, and zero-intimidation encouragement.",
                "en-US-JennyNeural",
                "calm_supportive",
                0.85,
                "#8b5cf6"
            )
        ]
        cursor.executemany("""
        INSERT INTO student_personas (id, name, tag, description, voice_name, tone, pacing_multiplier, accent_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_personas)

    conn.commit()
    conn.close()

# Database Helper Functions
def get_all_lectures() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lectures ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_lecture_by_id(lecture_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lectures WHERE id = ?", (lecture_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_lecture_facts(lecture_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lecture_facts WHERE lecture_id = ? ORDER BY id ASC", (lecture_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_personas() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_personas")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_persona_by_id(persona_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_personalized_lectures(lecture_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, s.name as persona_name, s.tag as persona_tag, s.accent_color
    FROM personalized_lectures p
    JOIN student_personas s ON p.persona_id = s.id
    WHERE p.lecture_id = ?
    ORDER BY p.created_at DESC
    """, (lecture_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_personalized_lecture_by_id(pers_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, s.name as persona_name, s.tag as persona_tag, s.accent_color,
           l.title as lecture_title, l.subject as lecture_subject
    FROM personalized_lectures p
    JOIN student_personas s ON p.persona_id = s.id
    JOIN lectures l ON p.lecture_id = l.id
    WHERE p.id = ?
    """, (pers_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
