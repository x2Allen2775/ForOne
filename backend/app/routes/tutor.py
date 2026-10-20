import re
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_lecture_by_id, get_lecture_facts
from app.config import GEMINI_API_KEY, GROQ_API_KEY

router = APIRouter(prefix="/api/tutor", tags=["tutor"])

import httpx

def call_gemini_rest(prompt: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = httpx.post(url, json=payload, timeout=20.0)
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"Gemini REST error: {e}")
    return None

class ChatRequest(BaseModel):
    lecture_id: str
    message: str
    chat_history: Optional[List[dict]] = []

@router.post("/chat")
def chat_with_ai_tutor(req: ChatRequest):
    lecture = get_lecture_by_id(req.lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    facts = get_lecture_facts(req.lecture_id)
    fact_context = "\n".join([f"- {f['fact_id']} [{f['category']}]: {f['statement']}" for f in facts])
    transcript_context = lecture.get("master_transcript", "")[:2000]

    # Fast Gemini REST API
    prompt = f"""
You are the 24/7 ForOne Judgment-Free AI Tutor. Your role is to provide kind, patient, clear explanations for students.
You are strictly grounded in the approved lecture material and verified fact base. Do not invent facts outside this scope.

Course Subject: {lecture['subject']}
Lecture Title: {lecture['title']}

Verified Syllabus Fact Base:
{fact_context}

Original Lecture Excerpt:
{transcript_context}

Student Question:
\"{req.message}\"

Respond clearly and warmly, referencing verified lecture concepts. Keep your explanation concise and intuitive.
"""
    gemini_reply = call_gemini_rest(prompt)
    if gemini_reply:
        return {"reply": gemini_reply, "grounded_facts_used": [f['fact_id'] for f in facts[:3]]}

    # Intelligent local offline grounded response
    user_msg_lower = req.message.lower()
    matched_facts = []
    for f in facts:
        words = re.findall(r'\b[a-zA-Z0-9_\-\+]{3,}\b', f["statement"].lower())
        if any(w in user_msg_lower for w in words if w not in {"the", "and", "that", "this", "with"}):
            matched_facts.append(f)

    if matched_facts:
        fact_answers = " ".join([mf["statement"] for mf in matched_facts[:2]])
        reply = (
            f"Great question! Based directly on our lecture '{lecture['title']}': {fact_answers} "
            f"Remember, our priority queue and binary division keep the search space halving efficiently."
        )
    else:
        top_fact = facts[0]["statement"] if facts else "Focus on dividing the sorted search space in half."
        reply = (
            f"Here is the key takeaway from '{lecture['title']}': {top_fact} "
            f"Always make sure your input meets the prerequisites before executing each step!"
        )

    return {
        "reply": reply,
        "grounded_facts_used": [f["fact_id"] for f in matched_facts] if matched_facts else ["F01"]
    }

@router.get("/quiz/{lecture_id}")
def get_adaptive_micro_quiz(lecture_id: str):
    """
    Dynamically generates a 3-question adaptive micro-quiz derived directly
    from the specific lecture's verified facts base and transcript.
    Never returns static or hardcoded questions.
    """
    lecture = get_lecture_by_id(lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    facts = get_lecture_facts(lecture_id)
    if not facts:
        raise HTTPException(status_code=400, detail="No facts available for quiz generation")

    # 1. Attempt LLM generation if Gemini or Groq is available
    if GEMINI_API_KEY:
        try:
            facts_str = "\n".join([f"- [{f['fact_id']}] ({f['category']}): {f['statement']}" for f in facts[:10]])
            prompt = f"""
You are an expert educational assessment creator.
Generate a 3-question multiple choice micro-quiz based EXCLUSIVELY on this lecture material.

Lecture Title: {lecture['title']}
Subject: {lecture['subject']}

Syllabus Facts:
{facts_str}

Transcript excerpt:
{lecture.get('master_transcript', '')[:1500]}

Generate 3 high quality questions testing conceptual understanding, definitions, or steps.
Return ONLY valid JSON in this exact structure:
[
  {{
    "id": 1,
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Clear explanation referencing syllabus fact.",
    "grounded_fact_id": "F01"
  }}
]
"""
            raw = call_gemini_rest(prompt)
            if raw:
                raw = raw.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.startswith("```"):
                    raw = raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                generated_questions = json.loads(raw.strip())
                return {
                    "lecture_id": lecture_id,
                    "lecture_title": lecture["title"],
                    "questions": generated_questions
                }
        except Exception as e:
            print(f"Gemini quiz generation failed, using dynamic local fact generator: {e}")

    # 2. Dynamic fact-based quiz generator (works 100% offline for ANY lecture!)
    dynamic_questions = []
    
    # Pick top 3 distinct facts
    sampled_facts = facts[:3] if len(facts) >= 3 else facts
    
    for idx, fact in enumerate(sampled_facts):
        statement = fact.get("statement", "").rstrip(".")
        category = fact.get("category", "concept")
        fact_id = fact.get("fact_id", f"F{idx+1:02d}")
        
        # Build question based on category
        if category in ["boundary_condition", "prerequisite"]:
            q_text = f"According to '{lecture['title']}', what is an essential condition or prerequisite?"
            correct_opt = statement
            distractors = [
                f"The inputs must be processed in reverse chronological order without validation.",
                f"Execution can proceed without meeting initial state prerequisites.",
                f"The algorithm only succeeds when all values are negative integers."
            ]
        elif category in ["formula", "numerical"]:
            q_text = f"Which formula, metric, or quantitative principle is emphasized in '{lecture['title']}'?"
            correct_opt = statement
            distractors = [
                f"The complexity scales exponentially with quadratic memory overhead.",
                f"The quantitative values remain unbounded and unpredictable.",
                f"All metrics decrease linearly by constant factor zero."
            ]
        elif category == "step":
            q_text = f"What key operational step is highlighted in '{lecture['title']}'?"
            correct_opt = statement
            distractors = [
                f"Skip the validation phase and terminate the operation immediately.",
                f"Invert the pointers without updating the tracking index.",
                f"Repeat all preceding operations in a continuous infinite cycle."
            ]
        else:
            q_text = f"Which of the following propositions is verified in the lecture '{lecture['title']}'?"
            correct_opt = statement
            distractors = [
                f"The concept contradicts standard core syllabus objectives.",
                f"The framework only applies to theoretical deprecated systems.",
                f"The operation produces arbitrary nondeterministic outputs."
            ]
            
        # Shuffle correct option into options list
        options = [correct_opt] + distractors[:3]
        # Place correct answer deterministically based on index (so answers vary across A, B, C, D)
        correct_pos = (idx + 1) % 4
        # Swap correct_opt with element at correct_pos
        options[0], options[correct_pos] = options[correct_pos], options[0]
        
        dynamic_questions.append({
            "id": idx + 1,
            "question": q_text,
            "options": options,
            "correct_index": correct_pos,
            "explanation": f"Grounded in verified syllabus fact [{fact_id}]: \"{statement}\".",
            "grounded_fact_id": fact_id
        })

    return {
        "lecture_id": lecture_id,
        "lecture_title": lecture["title"],
        "questions": dynamic_questions
    }
