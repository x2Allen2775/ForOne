import re
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import GEMINI_API_KEY, GROQ_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rewriter_service")

class RewriterService:
    def __init__(self):
        pass

    def rewrite_for_persona(
        self,
        master_transcript: str,
        facts: List[Dict[str, Any]],
        persona: Dict[str, Any],
        simulate_error: bool = False
    ) -> str:
        """
        Rewrites the master lecture transcript to match the student persona while
        strictly retaining 100% of facts.
        If simulate_error is True, purposefully drops a critical fact to demonstrate the Failsafe quality gate.
        """
        persona_id = persona.get("id", "witty")

        # Check if external free LLM available
        if GEMINI_API_KEY and not simulate_error:
            try:
                script = self._rewrite_with_gemini(master_transcript, facts, persona)
                if script:
                    return script
            except Exception as e:
                logger.warning(f"Gemini rewriting failed, using local persona generator: {e}")

        # Local pedagogical persona engine
        return self._rewrite_locally(master_transcript, facts, persona_id, simulate_error)

    def _rewrite_with_gemini(
        self,
        master_transcript: str,
        facts: List[Dict[str, Any]],
        persona: Dict[str, Any]
    ) -> str:
        import httpx

        fact_list_str = "\n".join([f"- [{f['fact_id']}] {f['statement']} ({f['category']})" for f in facts])

        prompt = f"""
You are an award-winning personalized education AI rewriter.
Your task is to rewrite the following master lecture transcript into a dynamic, highly engaging video script tailored specifically to this student persona:

Persona: {persona['name']}
Tone & Delivery Style: {persona['tone']}
Persona Description: {persona['description']}

RULES:
1. You MUST incorporate EVERY SINGLE ONE of the following required facts and formulas without exception:
{fact_list_str}

2. Adjust the pacing, dialogue, analogies, and rhetorical framing to suit the persona perfectly.
3. Every time you express a required fact, embed it with tags: [FACT:Fxx] statement [/FACT:Fxx].
4. Output ONLY the finalized spoken video script. Do not include stage directions in brackets, just natural spoken words.

Original Master Transcript:
\"\"\"{master_transcript}\"\"\"
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = httpx.post(url, json=payload, timeout=25.0)
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"].strip()
        raise RuntimeError(f"Gemini REST returned {res.status_code}: {res.text}")

    def _rewrite_locally(
        self,
        master_transcript: str,
        facts: List[Dict[str, Any]],
        persona_id: str,
        simulate_error: bool = False
    ) -> str:
        """
        Deterministic local persona template and rhetorical transformer.
        Injects distinct persona intros, transitions, analogies, and pacing markers
        while guaranteeing factual fidelity (unless simulate_error is True).
        """
        output_paragraphs = []

        # Persona-specific hooks
        hooks = {
            "witty": "Alright tech squad, buckle up! You know that feeling when you're looking for one specific meme in a folder of 10,000 files? Exactly. Let's break down this concept the smart way, without the boring academic fluff.",
            "intuitive": "Let's pause and step back to first principles. Imagine the world as a physical landscape before we even write a single line of formal notation. Let's build the intuition together.",
            "exam_cram": "High-yield focus time. Here are the core concepts, exam traps, and exact formulas you will be tested on. Zero wasted words, let's lock this down.",
            "supportive": "Welcome! Take a nice deep breath. This topic might look intimidating at first glance, but we are going to walk through it step-by-step together at a comfortable pace. You've got this."
        }

        # Persona-specific statement wrappers
        wrappers = {
            "witty": [
                ("Here is the golden rule: ", " — honestly, that's just pure engineering genius."),
                ("Now, don't sleep on this part: ", " Boom, mind blown."),
                ("Notice the secret sauce here: ", " It's basically a life hack for algorithms."),
                ("Check this out: ", " Pretty neat, right?"),
            ],
            "intuitive": [
                ("Think of it like this: ", " Just like water flowing through the path of least resistance."),
                ("Visualizing the core principle: ", " The geometry makes it completely intuitive."),
                ("At its foundational level, ", " This is the bedrock of the entire concept."),
                ("From first principles, ", " Everything else naturally flows from this point."),
            ],
            "exam_cram": [
                ("CRITICAL EXAM TAKEAWAY: ", " (Memorize this for tests)."),
                ("Key formula and definition: ", " High probability exam question."),
                ("Step check: ", " Do not forget this edge case on your practical."),
                ("Core assertion: ", " Write this down."),
            ],
            "supportive": [
                ("Let's look at this key idea together: ", " Take your time to reflect on that."),
                ("Remember, ", " You are doing fantastic, and it will all connect shortly."),
                ("Here is the reassuring part: ", " It really is that straightforward when broken down."),
                ("Notice this gentle checkpoint: ", " You have already grasped the most challenging part."),
            ]
        }

        output_paragraphs.append(hooks.get(persona_id, hooks["witty"]))

        # Iterate over facts
        active_facts = list(facts)
        if simulate_error and len(active_facts) > 0:
            # Intentionally remove a critical fact (e.g. prerequisite sorted condition or formula) to trigger the failsafe!
            logger.info("Simulate error enabled: Intentionally omitting a critical fact to trigger failsafe.")
            for idx, f in enumerate(active_facts):
                if f.get("criticality") == "critical":
                    active_facts.pop(idx)
                    break

        p_wrappers = wrappers.get(persona_id, wrappers["witty"])

        for i, fact in enumerate(active_facts):
            prefix, suffix = p_wrappers[i % len(p_wrappers)]
            statement = fact["statement"].rstrip(".")
            fact_id = fact["fact_id"]
            
            # Format with fact tag for exact tracking
            paragraph = f"{prefix}[FACT:{fact_id}]{statement}[/FACT:{fact_id}]{suffix}"
            output_paragraphs.append(paragraph)

        # Persona conclusions
        outros = {
            "witty": "And that is how you crush this topic with style! Don't forget: master the logic, and the code writes itself. Catch you in the next one!",
            "intuitive": "Now that you have the mental model in your mind's eye, every single variation of this problem will make total sense. Beautiful, elegant logic.",
            "exam_cram": "That covers 100% of the syllabus requirements and edge cases. Review these checkpoints and you will ace the assessment.",
            "supportive": "You did an incredible job working through this today! Celebrate this milestone, and I will see you in the next session whenever you are ready."
        }
        output_paragraphs.append(outros.get(persona_id, outros["supportive"]))

        return "\n\n".join(output_paragraphs)

rewriter_service = RewriterService()
