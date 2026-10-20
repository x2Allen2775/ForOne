import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from app.services.stt_service import stt_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("failsafe_verifier")

class FailsafeVerifier:
    def __init__(self):
        pass

    def verify_personalized_video(
        self,
        master_facts: List[Dict[str, Any]],
        generated_video_path: str,
        lecture_id: str,
        persona_id: str
    ) -> Dict[str, Any]:
        """
        Executes the mandatory dual-transcription and granular detail verification gate.
        1. Extracts audio from generated video and performs Speech-to-Text via Whisper.
        2. Granularly audits every single fact, formula, and detail against the master facts.
        3. Enforces strict failsafe: Returns FAILED_FAILSAFE error if any critical fact is missing or score < 95%.
        """
        gen_video_p = Path(generated_video_path)
        if not gen_video_p.exists():
            return {
                "status": "FAILED_FAILSAFE",
                "fidelity_score": 0.0,
                "error_message": f"Generated video file not found at {generated_video_path}",
                "facts_matrix": [],
                "missing_facts": master_facts,
                "gen_transcript": ""
            }

        # Step 1: Extract audio and transcribe generated video
        gen_audio_path = str(gen_video_p.parent / f"{gen_video_p.stem}_extracted_audio.wav")
        logger.info(f"Failsafe Gate: Extracting audio from generated video {generated_video_path}...")
        stt_service.extract_audio_from_video(generated_video_path, gen_audio_path)

        logger.info("Failsafe Gate: Transcribing generated audio using Whisper...")
        stt_result = stt_service.transcribe_audio(gen_audio_path)
        gen_transcript = stt_result.get("transcript", "")

        # Step 2: Granular Fact & Detail Comparison
        audit_matrix, total_weight, matched_weight, missing_critical = self._audit_facts(master_facts, gen_transcript)

        fidelity_score = round((matched_weight / total_weight * 100.0) if total_weight > 0 else 100.0, 1)

        # Step 3: Decision Gate (Strict 95% threshold + 0 critical facts missing)
        is_passed = (fidelity_score >= 95.0) and (missing_critical == 0)

        missing_facts = [item for item in audit_matrix if not item["matched"]]

        if is_passed:
            status = "APPROVED"
            error_msg = None
            logger.info(f"FAILSAFE PASSED: Fidelity {fidelity_score}%. All critical facts verified.")
        else:
            status = "FAILED_FAILSAFE"
            if missing_critical > 0:
                error_msg = f"FAILSAFE ERROR: Quality gate rejected! {missing_critical} critical concept(s) omitted or distorted in generated video. Score: {fidelity_score}%."
            else:
                error_msg = f"FAILSAFE ERROR: Quality gate rejected! Overall fact fidelity ({fidelity_score}%) is below strict 95% syllabus threshold."
            logger.error(error_msg)

        return {
            "status": status,
            "fidelity_score": fidelity_score,
            "error_message": error_msg,
            "total_facts": len(master_facts),
            "matched_facts": len(master_facts) - len(missing_facts),
            "missing_facts_count": len(missing_facts),
            "missing_critical_count": missing_critical,
            "facts_matrix": audit_matrix,
            "missing_facts": missing_facts,
            "gen_transcript": gen_transcript
        }

    def _audit_facts(
        self,
        master_facts: List[Dict[str, Any]],
        gen_transcript: str
    ) -> Tuple[List[Dict[str, Any]], float, float, int]:
        """
        Granularly cross-examines each master fact against the generated transcript.
        Checks keyword presence, mathematical formula preservation, and semantic coverage.
        """
        audit_matrix = []
        gen_transcript_lower = gen_transcript.lower()

        total_weight = 0.0
        matched_weight = 0.0
        missing_critical_count = 0
        for fact in master_facts:
            fact_id = fact.get("fact_id", "F00")
            statement = fact.get("statement", "")
            category = fact.get("category", "concept")
            criticality = fact.get("criticality", "critical")
            weight = 2.0 if criticality == "critical" else 1.0
            total_weight += weight

            # Meaningful technical terms filter
            stop_words = {
                "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
                "for", "of", "with", "by", "today", "we", "our", "if", "it", "as", "than",
                "into", "and", "or", "so", "this", "that", "from", "have", "they", "will",
                "what", "when", "where", "which", "there", "about", "must", "already", "each", "all"
            }

            raw_keywords = fact.get("keywords", [])
            if isinstance(raw_keywords, str):
                raw_keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]

            # Distinctive keywords from statement and keywords field
            content_words = [w for w in re.findall(r'\b[A-Za-z0-9_\-\+]{3,}\b', statement) if w.lower() not in stop_words]
            filtered_kws = list(set([k for k in raw_keywords if k.lower() not in stop_words] + content_words))

            # Check 1: Explicit Script Tag Presence
            tag_pattern = rf'\[FACT:{fact_id}\]'
            tag_in_script = bool(re.search(tag_pattern, gen_transcript, re.IGNORECASE))

            # Check 2: Core Keywords & Concept Presence in Generated Whisper STT
            matched_keywords = []
            for kw in filtered_kws:
                clean_kw = re.sub(r'[^a-zA-Z0-9_\-\+]', '', kw).lower()
                if clean_kw and clean_kw in gen_transcript_lower:
                    matched_keywords.append(kw)

            keyword_ratio = (len(matched_keywords) / len(filtered_kws)) if len(filtered_kws) > 0 else 0.0

            # Check 3: Formula / Math / Big-O exactness
            math_terms = re.findall(r'(O\([^\)]+\)|log|sorted|unsorted|half|minus one|plus one)', statement, re.IGNORECASE)
            math_matched = True
            for mt in math_terms:
                if mt.lower() not in gen_transcript_lower:
                    math_matched = False
                    break

            # A fact is verified only if:
            # 1. Its distinctive technical terms are spoken in the generated audio (keyword_ratio >= 0.6 and math_matched)
            # 2. Or explicit tag is present AND high ratio
            is_matched = False
            confidence = 0.0
            matched_snippet = ""

            if keyword_ratio >= 0.65 and math_matched:
                is_matched = True
                confidence = round(0.7 + (0.3 * keyword_ratio), 2)
                for kw in matched_keywords[:1]:
                    idx = gen_transcript_lower.find(kw.lower())
                    if idx != -1:
                        start_pos = max(0, idx - 30)
                        end_pos = min(len(gen_transcript), idx + 70)
                        matched_snippet = f"...{gen_transcript[start_pos:end_pos].strip()}..."
                        break
            else:
                is_matched = False
                confidence = round(keyword_ratio * 0.5, 2)
                matched_snippet = "OMITTED: Distinctive propositions and conditions not found in generated audio."

            if is_matched:
                matched_weight += weight
            else:
                if criticality == "critical":
                    missing_critical_count += 1

            audit_matrix.append({
                "fact_id": fact_id,
                "statement": statement,
                "category": category,
                "criticality": criticality,
                "matched": is_matched,
                "confidence": confidence,
                "matched_keywords": matched_keywords,
                "expected_keywords": filtered_kws,
                "evidence_snippet": matched_snippet,
                "timestamp_hint": fact.get("timestamp_hint", "00:00")
            })

        return audit_matrix, total_weight, matched_weight, missing_critical_count

failsafe_verifier = FailsafeVerifier()
