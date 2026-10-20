import json
from fastapi import APIRouter, HTTPException
from app.database import get_personalized_lecture_by_id, get_lecture_facts
from app.routes.personalization import generate_personalized_lecture, PersonalizeRequest

router = APIRouter(prefix="/api/failsafe", tags=["failsafe"])

@router.get("/{pers_id}")
def get_failsafe_report(pers_id: str):
    var = get_personalized_lecture_by_id(pers_id)
    if not var:
        raise HTTPException(status_code=404, detail="Personalized lecture record not found")

    audit_data = None
    if var.get("audit_report_json"):
        try:
            audit_data = json.loads(var["audit_report_json"])
        except Exception:
            pass

    return {
        "personalized_id": pers_id,
        "lecture_title": var.get("lecture_title"),
        "persona_name": var.get("persona_name"),
        "status": var.get("status"),
        "fidelity_score": var.get("fact_fidelity_score"),
        "error_message": var.get("error_message"),
        "audit_report": audit_data,
        "script_text": var.get("script_text"),
        "gen_transcript_text": var.get("gen_transcript_text")
    }

@router.post("/simulate_demo")
def simulate_failsafe_comparison(lecture_id: str = "lec_binary_search_101"):
    """
    Executes a side-by-side demonstration comparing:
    1. A normal Witty persona generation (Expected: APPROVED, 100% facts verified).
    2. An intentionally incomplete generation (Expected: FAILED_FAILSAFE, flags missing facts).
    """
    # 1. Generate Passing Persona
    pass_res = generate_personalized_lecture(PersonalizeRequest(
        lecture_id=lecture_id,
        persona_id="witty",
        simulate_error=False
    ))

    # 2. Generate Failing Persona (Omits critical prerequisite and formula)
    fail_res = generate_personalized_lecture(PersonalizeRequest(
        lecture_id=lecture_id,
        persona_id="exam_cram",
        simulate_error=True
    ))

    return {
        "message": "Failsafe side-by-side comparison simulation completed.",
        "passing_case": pass_res,
        "failing_case": fail_res
    }
