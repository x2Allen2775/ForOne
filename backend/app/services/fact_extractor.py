import re
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import GEMINI_API_KEY, GROQ_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fact_extractor")

class FactExtractor:
    def __init__(self):
        pass

    def extract_facts(self, transcript: str, segments: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Extracts structured factual units from master lecture transcript.
        Tries free-tier LLM if key exists, otherwise uses advanced local rule-based proposition parser.
        """
        if not transcript.strip():
            return []

        # Attempt Gemini or Groq if available
        if GEMINI_API_KEY:
            try:
                facts = self._extract_with_gemini(transcript, segments)
                if facts:
                    return facts
            except Exception as e:
                logger.warning(f"Gemini fact extraction failed, falling back to local extractor: {e}")

        if GROQ_API_KEY:
            try:
                facts = self._extract_with_groq(transcript, segments)
                if facts:
                    return facts
            except Exception as e:
                logger.warning(f"Groq fact extraction failed, falling back to local extractor: {e}")

        # Highly reliable local offline extractor
        return self._extract_locally(transcript, segments)

        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = httpx.post(url, json=payload, timeout=25.0)
        if res.status_code != 200:
            raise RuntimeError(f"Gemini fact extraction failed: {res.text}")
        text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Clean potential markdown fences
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    def _extract_with_groq(self, transcript: str, segments: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""
Extract every minute technical detail, formula, definition, and step from this lecture transcript as a JSON list.
Transcript:
{transcript}

Return JSON array only:
[
  {{
    "fact_id": "F01",
    "category": "concept",
    "statement": "...",
    "keywords": ["..."],
    "criticality": "critical",
    "timestamp_hint": "00:00"
  }}
]
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif "facts" in data:
            return data["facts"]
        return []

    def _extract_locally(self, transcript: str, segments: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Deterministic, local rule-based extraction that parses sentences into propositions,
        identifies critical mathematical/scientific terminology, numbers, steps, and definitions.
        """
        # Split into sentences or clauses
        raw_sentences = re.split(r'(?<=[.!?])\s+', transcript)
        facts = []
        fact_idx = 1

        # Patterns for classification
        formula_pattern = re.compile(r'(O\([^\)]+\)|log|squared|\=|\+|\*|\/|\^|constant|exponential|linear)', re.IGNORECASE)
        definition_pattern = re.compile(r'(is defined as|means that|refers to|is called|is essentially|we define|is known as)', re.IGNORECASE)
        step_pattern = re.compile(r'(first|second|third|step|initially|next|then|finally|before|after)', re.IGNORECASE)
        boundary_pattern = re.compile(r'(must be|requires|prerequisite|sorted|unsorted|boundary|edge case|if|unless|condition)', re.IGNORECASE)
        number_pattern = re.compile(r'\b(\d+|zero|one|two|half|double)\b', re.IGNORECASE)

        for s_idx, sent in enumerate(raw_sentences):
            sent = sent.strip()
            if len(sent) < 15:
                continue

            # Approximate timestamp
            timestamp_str = "00:00"
            if segments and len(segments) > 0:
                # Find matching segment
                for seg in segments:
                    if any(w.lower() in seg['text'].lower() for w in sent.split()[:4]):
                        mins = int(seg['start'] // 60)
                        secs = int(seg['start'] % 60)
                        timestamp_str = f"{mins:02d}:{secs:02d}"
                        break

            category = "concept"
            criticality = "supplementary"

            if formula_pattern.search(sent):
                category = "formula"
                criticality = "critical"
            elif boundary_pattern.search(sent):
                category = "boundary_condition"
                criticality = "critical"
            elif definition_pattern.search(sent):
                category = "definition"
                criticality = "critical"
            elif step_pattern.search(sent):
                category = "step"
                criticality = "critical"
            elif number_pattern.search(sent):
                category = "numerical"
                criticality = "critical"

            # Extract keywords (capitalized words, numbers, and technical terms)
            words = re.findall(r'\b[A-Za-z0-9_/\(\)-]{3,}\b', sent)
            stop_words = {"this", "that", "with", "from", "have", "they", "will", "what", "when", "where", "which", "there", "about"}
            keywords = [w for w in words if w.lower() not in stop_words][:5]

            fact = {
                "fact_id": f"F{fact_idx:02d}",
                "category": category,
                "statement": sent,
                "keywords": keywords,
                "criticality": criticality,
                "timestamp_hint": timestamp_str
            }
            facts.append(fact)
            fact_idx += 1

        logger.info(f"Local fact extraction completed: {len(facts)} facts extracted.")
        return facts

fact_extractor = FactExtractor()
